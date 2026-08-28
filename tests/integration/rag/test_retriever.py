"""
Tests de integración para el recuperador (Retriever).

Estos tests requieren que los contenedores lab-ollama y lab-pinecone
estén en ejecución. Cada test que necesite datos indexa su propio
documento de prueba en el índice Pinecone.
"""

import pytest
from pathlib import Path
from langchain_core.documents import Document

from app.core.config import Settings
from app.rag import Retriever, SearchType, Indexer


# ------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------

@pytest.fixture
def valid_settings() -> Settings:
    """Retorna una instancia de Settings con valores válidos para Pinecone y Ollama."""
    return Settings(
        PINECONE_HOST="http://localhost:5081",
        PINECONE_INDEX_NAME="lab",
        IA_MODEL_HOST="http://localhost:11434",
        IA_MODEL_EMBEDDED_NAME="nomic-embed-text",
    )


@pytest.fixture
def retriever(valid_settings: Settings) -> Retriever:
    """Retorna un retriever configurado con search_type='similarity' y k=2."""
    return Retriever(k=2, settings=valid_settings)


def index_test_document(tmp_path: Path, content: str, settings: Settings) -> None:
    """Helper: indexa un documento de prueba en Pinecone."""
    file_path = tmp_path / "test_doc.txt"
    file_path.write_text(content, encoding="utf-8")
    indexer = Indexer(
        file_path=file_path,
        chunk_size=100,      # pequeño para que sea un solo fragmento
        chunk_overlap=0,
        settings=settings,
    )
    indexer.index()


# ------------------------------------------------------------
# Tests de validación (errores esperados)
# ------------------------------------------------------------

def test_retriever_raises_if_host_missing() -> None:
    """1. PINECONE_HOST no definido → ValueError."""
    bad_settings = Settings(PINECONE_HOST="", PINECONE_INDEX_NAME="lab")
    with pytest.raises(ValueError, match="PINECONE_HOST no está definido"):
        Retriever(settings=bad_settings)


def test_retriever_raises_if_index_name_missing() -> None:
    """2. PINECONE_INDEX_NAME no definido → ValueError."""
    bad_settings = Settings(PINECONE_HOST="http://localhost:5081", PINECONE_INDEX_NAME="")
    with pytest.raises(ValueError, match="PINECONE_INDEX_NAME no está definido"):
        Retriever(settings=bad_settings)


def test_retriever_raises_if_threshold_missing() -> None:
    """3. search_type='similarity_score_threshold' sin score_threshold → ValueError."""
    settings = Settings(
        PINECONE_HOST="http://localhost:5081",
        PINECONE_INDEX_NAME="lab",
    )
    with pytest.raises(ValueError, match="score_threshold es obligatorio"):
        Retriever(
            settings=settings,
            search_type=SearchType.SIMILARITY_SCORE_THRESHOLD,
        )


def test_retriever_raises_if_retrieve_with_scores_on_non_similarity(
    valid_settings: Settings,
) -> None:
    """4. retrieve_with_scores() con search_type != SIMILARITY → ValueError."""
    retriever_mmr = Retriever(
        settings=valid_settings,
        search_type=SearchType.MMR,
        fetch_k=10,
        lambda_mult=0.5,
    )
    with pytest.raises(ValueError, match="retrieve_with_scores solo está disponible"):
        retriever_mmr.retrieve_with_scores("ibuprofeno")


# ------------------------------------------------------------
# Tests de flujo exitoso (cada uno indexa su propio documento)
# ------------------------------------------------------------

def test_retriever_retrieve_returns_documents(
    valid_settings: Settings,
    tmp_path: Path,
) -> None:
    """5. retrieve() devuelve lista de Document con resultados del documento de prueba."""
    # Given: indexamos un documento con información específica
    content = (
        "La fórmula química del ibuprofeno es C13H18O2. "
        "Su masa molar es 206.28 g/mol."
    )
    index_test_document(tmp_path, content, valid_settings)

    # When: consultamos por la fórmula
    retriever = Retriever(k=1, settings=valid_settings)
    query = "fórmula química del ibuprofeno"
    docs = retriever.retrieve(query)

    # Then: debemos obtener al menos un documento que contenga esa información
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)
    assert "C13H18O2" in docs[0].page_content


def test_retriever_retrieve_with_scores_returns_scores(
    valid_settings: Settings,
    tmp_path: Path,
) -> None:
    """6. retrieve_with_scores() devuelve tuplas (Document, float)."""
    # Given: indexamos un documento con información sobre paracetamol
    content = (
        "El paracetamol (acetaminofén) es un analgésico y antipirético. "
        "Su dosis máxima diaria es de 4 gramos."
    )
    index_test_document(tmp_path, content, valid_settings)

    # When: consultamos por la dosis
    retriever = Retriever(k=1, settings=valid_settings, search_type=SearchType.SIMILARITY)
    query = "dosis máxima de paracetamol"
    results = retriever.retrieve_with_scores(query)

    # Then: debe haber al menos un resultado con score
    assert isinstance(results, list)
    assert len(results) > 0
    doc, score = results[0]
    assert isinstance(doc, Document)
    assert isinstance(score, float)
    assert 0.0 <= score <= 1.0
    assert "dosis máxima diaria es de 4" in doc.page_content


def test_retriever_retrieve_as_context_returns_text(
    valid_settings: Settings,
    tmp_path: Path,
) -> None:
    """7. retrieve_as_context() devuelve un string que contiene la información del documento de prueba."""
    # Given: indexamos un documento sobre ibuprofeno
    content = (
        "El ibuprofeno es un antiinflamatorio no esteroideo (AINE). "
        "Se utiliza para tratar el dolor y la inflamación."
    )
    index_test_document(tmp_path, content, valid_settings)

    # When: consultamos y obtenemos el contexto
    retriever = Retriever(k=1, settings=valid_settings)
    query = "ibuprofeno antiinflamatorio"
    context = retriever.retrieve_as_context(query)

    # Then: el contexto debe contener el texto del documento de prueba
    assert isinstance(context, str)
    assert len(context) > 0
    assert "antiinflamatorio no esteroideo" in context


def test_retriever_empty_query_returns_empty(retriever: Retriever) -> None:
    """8. retrieve() con query vacía devuelve lista vacía."""
    docs = retriever.retrieve("")
    assert docs == []

    docs = retriever.retrieve("   ")
    assert docs == []


def test_retriever_empty_query_returns_empty_for_scores(retriever: Retriever) -> None:
    """9. retrieve_with_scores() con query vacía devuelve lista vacía."""
    results = retriever.retrieve_with_scores("")
    assert results == []


def test_retriever_mmr_works(
    valid_settings: Settings,
    tmp_path: Path,
) -> None:
    """10. MMR funciona sin errores y devuelve documentos del documento de prueba."""
    # Given: indexamos un documento sobre antiinflamatorios
    content = (
        "Los antiinflamatorios no esteroideos (AINE) incluyen ibuprofeno, "
        "naproxeno y diclofenaco. Tienen efectos secundarios como "
        "irritación gástrica."
    )
    index_test_document(tmp_path, content, valid_settings)

    # When: usamos MMR para consultar
    retriever_mmr = Retriever(
        settings=valid_settings,
        search_type=SearchType.MMR,
        k=2,
        fetch_k=5,
        lambda_mult=0.5,
    )
    query = "efectos secundarios de los AINE"
    docs = retriever_mmr.retrieve(query)

    # Then: debe devolver documentos
    assert isinstance(docs, list)
    assert len(docs) > 0
    assert all(isinstance(d, Document) for d in docs)
    # Verificar que uno de los documentos contiene "irritación gástrica"
    assert any("gástrica" in d.page_content for d in docs)


def test_retriever_threshold_works(valid_settings: Settings) -> None:
    """11. similarity_score_threshold filtra por score mínimo (sin datos de prueba, solo verifica que no lance error)."""
    retriever_threshold = Retriever(
        settings=valid_settings,
        search_type=SearchType.SIMILARITY_SCORE_THRESHOLD,
        k=5,
        score_threshold=0.5,
    )
    query = "aspirina"
    docs = retriever_threshold.retrieve(query)

    # Este test solo verifica que no se levante excepción
    assert isinstance(docs, list)
    # Si no hay documentos con score >= 0.5, la lista estará vacía, lo cual es válido.
