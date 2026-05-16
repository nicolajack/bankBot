from llama_index.core import VectorStoreIndex, Settings
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.core import Document
import chromadb
from pathlib import Path

# load all markdown docs you want indexed
DOC_DIR = Path(__file__).parent
DOC_FILES = [
    DOC_DIR / "faq.md",
    DOC_DIR / "feeInfo.md",
    DOC_DIR / "savingsAccountPolicy.md",
]

docs = [
    Document(text=path.read_text(encoding="utf-8"), metadata={"source": path.name})
    for path in DOC_FILES
]

# set up embed model
Settings.embed_model = HuggingFaceEmbedding(model_name="sentence-transformers/all-MiniLM-L6-v2")

# set up chroma
chroma_client = chromadb.PersistentClient(path="./chroma_db")
chroma_collection = chroma_client.get_or_create_collection("rag_collection")
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)

# index handles chunking and embedding
index = VectorStoreIndex.from_documents(docs, vector_store=vector_store)
