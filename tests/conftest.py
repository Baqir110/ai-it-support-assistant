import os

import pytest


@pytest.fixture(autouse=True, scope="session")
def _isolate_chroma_dir(tmp_path_factory):
    """Points the vector store at a throwaway directory for the whole test run."""
    chroma_dir = tmp_path_factory.mktemp("chroma")
    os.environ["CHROMA_PERSIST_DIR"] = str(chroma_dir)
    yield
