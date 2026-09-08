"""
Integration tests for OpenSearch vector store.

These tests create a real OpenSearch domain via Floci, wait for it to be ready,
use it for indexing and search, and then clean up the domain.
"""

import time
import boto3
import pytest
from botocore.exceptions import ClientError
from langchain_core.documents import Document
from app.aws.opensearch.vector_store import OpenSearchVectorStore
from app.core.config import settings
from app.core.exceptions import RAGError


# Helpers to manage OpenSearch domain via Floci
def _wait_for_domain(client, domain_name: str, max_attempts: int = 30, delay: int = 5):
    """Wait for the domain to become active and return its endpoint."""
    for _ in range(max_attempts):
        try:
            resp = client.describe_domain(DomainName=domain_name)
            status = resp["DomainStatus"]
            if status.get("Created") and status.get("Processing") is False:
                endpoint = status.get("Endpoint")
                if endpoint:
                    return endpoint
        except ClientError:
            pass
        time.sleep(delay)
    raise TimeoutError(f"Domain {domain_name} did not become ready within {max_attempts * delay} seconds.")


def _create_domain(domain_name: str):
    """Create an OpenSearch domain via Floci and return its endpoint."""
    client = boto3.client(
        "opensearch",
        endpoint_url="http://localhost:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
        use_ssl=False,
        verify=False,
    )
    try:
        # Try to delete if exists (ignore errors)
        client.delete_domain(DomainName=domain_name)
        time.sleep(2)
    except ClientError:
        pass

    client.create_domain(
        DomainName=domain_name,
        EngineVersion="OpenSearch_2.11",
        ClusterConfig={
            "InstanceType": "t3.small.search",
            "InstanceCount": 1,
        },
        EBSOptions={
            "EBSEnabled": True,
            "VolumeType": "gp2",
            "VolumeSize": 10,
        },
    )
    endpoint = _wait_for_domain(client, domain_name)
    return endpoint


def _delete_domain(domain_name: str):
    """Delete an OpenSearch domain via Floci."""
    client = boto3.client(
        "opensearch",
        endpoint_url="http://localhost:4566",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
        use_ssl=False,
        verify=False,
    )
    try:
        client.delete_domain(DomainName=domain_name)
        time.sleep(2)
    except ClientError:
        pass


@pytest.fixture(scope="function")
def opensearch_endpoint():
    """Create a temporary OpenSearch domain and return its endpoint."""
    domain_name = f"test-domain-{int(time.time() * 1000)}"
    endpoint = _create_domain(domain_name)
    yield endpoint
    _delete_domain(domain_name)


@pytest.fixture(scope="function")
def embeddings():
    """Create Ollama embeddings instance using the configured model."""
    from langchain_ollama import OllamaEmbeddings
    return OllamaEmbeddings(
        model=settings.IA_MODEL_EMBEDDED_NAME,
        base_url=settings.IA_MODEL_HOST,
    )


@pytest.fixture(scope="function")
def index_name() -> str:
    """Generate a unique index name for each test."""
    return f"test_index_{int(time.time() * 1000)}"


@pytest.fixture(scope="function")
def test_documents(tmp_path):
    """Create test documents using a temporary file."""
    from langchain_community.document_loaders import TextLoader
    from langchain_text_splitters import RecursiveCharacterTextSplitter

    content = (
        "El ibuprofeno es un antiinflamatorio no esteroideo (AINE). "
        "Se utiliza para aliviar el dolor, la fiebre y la inflamación. "
        "La dosis habitual en adultos es de 400-600 mg cada 6-8 horas. "
        "Contraindicaciones: úlcera péptica activa, insuficiencia renal grave."
    )
    file_path = tmp_path / "test_doc.txt"
    file_path.write_text(content, encoding="utf-8")

    loader = TextLoader(file_path, encoding="utf-8")
    docs = loader.load()
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=200,
        chunk_overlap=20,
    )
    return splitter.split_documents(docs)


@pytest.fixture(scope="function")
def vector_store(opensearch_endpoint, embeddings, index_name):
    """Create an OpenSearchVectorStore instance using the temporary domain."""
    store = OpenSearchVectorStore(
        index_name=index_name,
        embedding=embeddings,
        endpoint_url=opensearch_endpoint,
        http_auth=None,  # Floci no requiere auth para OpenSearch
    )
    yield store
    # Cleanup: delete the index (not the whole domain)
    try:
        store.delete_index()
    except Exception:
        pass


class TestOpenSearchVectorStore:
    def test_add_documents_and_search(self, vector_store, test_documents):
        store = vector_store
        ids = store.add_documents(test_documents)
        time.sleep(1)  # allow indexing to propagate

        assert len(ids) > 0
        results = store.similarity_search("ibuprofeno", k=2)
        assert len(results) > 0
        assert any("ibuprofeno" in doc.page_content.lower() for doc in results)

    def test_similarity_search_with_score(self, vector_store, test_documents):
        store = vector_store
        store.add_documents(test_documents)
        time.sleep(1)

        results = store.similarity_search_with_score("antiinflamatorio", k=2)
        assert len(results) > 0
        for doc, score in results:
            assert isinstance(score, float)
            assert 0.0 <= score <= 1.0

    def test_index_exists(self, vector_store):
        assert vector_store.index_exists() is False

        dummy = Document(page_content="Test content")
        vector_store.add_documents([dummy])
        time.sleep(1)
        assert vector_store.index_exists() is True

    def test_delete_index(self, vector_store):
        dummy = Document(page_content="Test content")
        vector_store.add_documents([dummy])
        time.sleep(1)
        assert vector_store.index_exists() is True

        vector_store.delete_index()
        time.sleep(1)
        assert vector_store.index_exists() is False

    def test_similarity_search_with_threshold(self, vector_store, test_documents):
        store = vector_store
        store.add_documents(test_documents)
        time.sleep(1)

        results = store.similarity_search("ibuprofeno", k=2, score_threshold=0.8)
        assert isinstance(results, list)
