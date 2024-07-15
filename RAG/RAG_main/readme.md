# RAG

## Dependency to download

- step 1 download the library

```bash
pip install "unstructured[all-docs]" pillow pydantic lxml pillow matplotlib chromadb tiktoken langchain_community langchain_huggingface langchain_chroma

sudo apt update

sudo apt-get install poppler-utils

sudo apt-get install tesseract-ocr


```

- step 2 download ollama and models


```bash
curl -fsSL https://ollama.com/install.sh | sh
ollama serve
ollama pull llama3
ollama pull llava

```



