import os

from dotenv import load_dotenv
from pinecone import Pinecone


load_dotenv()


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

pinecone_hosts = [
    os.getenv("PINECONE_HOST"),
    "http://localhost:5082", # fire code
]


# ------------------------------------------------------------
# Pinecone Local
# ------------------------------------------------------------

pinecone = Pinecone(
    api_key="pclocal"
)


# ------------------------------------------------------------
# Delete all vectors
# ------------------------------------------------------------

for host in pinecone_hosts:
    if not host:
        continue

    print(f"Clearing index: {host}")

    index = pinecone.Index(
        host=host
    )

    index.delete(delete_all=True)

    print(f"Cleared: {host}")


print("All Pinecone Local indexes cleared.")
