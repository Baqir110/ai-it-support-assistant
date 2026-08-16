import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

KNOWLEDGE_BASE_DIR = "data/knowledge_base"
CHROMA_PATH = "data/chroma_db"


def build_vector_store():
    if not os.path.exists(KNOWLEDGE_BASE_DIR):
        raise FileNotFoundError(f"Directory {KNOWLEDGE_BASE_DIR} does not exist.")

    # 1. Load Markdown documents
    print("Loading knowledge base documents...")
    loader = DirectoryLoader(
        KNOWLEDGE_BASE_DIR,
        glob="**/*.md",
        loader_cls=TextLoader,
        loader_kwargs={"encoding": "utf-8"},
    )
    documents = loader.load()
    print(f"Loaded {len(documents)} document(s).")

    # 2. Split documents into semantic chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
        separators=["\n## ", "\n### ", "\n\n", "\n", " "],
    )
    chunks = text_splitter.split_documents(documents)
    print(f"Created {len(chunks)} text chunks.")

    # 3. Generate embeddings and persist to ChromaDB
    print("Generating embeddings and writing to ChromaDB...")
    embedding_function = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    vector_db = Chroma.from_documents(
        documents=chunks, embedding=embedding_function, persist_directory=CHROMA_PATH
    )

    print(f"Successfully indexed {len(chunks)} chunks in {CHROMA_PATH}.")
    return vector_db


if __name__ == "__main__":
    build_vector_store()
