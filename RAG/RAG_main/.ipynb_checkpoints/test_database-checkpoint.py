from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.storage import InMemoryStore
from langchain.retrievers.multi_vector import MultiVectorRetriever
print("1")
vectorstore = Chroma(
        persist_directory="./chroma_db_database",
        collection_name="mm_RAG",
        embedding_function=HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2', model_kwargs={"device": "cuda"})
    )
id_key = "doc_id"
print("2")
store = InMemoryStore()
# Create the multi-vector retriever
retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    docstore=store,
    id_key=id_key,
)
print("3")
# Check retrieval
query = "In 2023, our growth in China?"
docs = retriever.invoke(query, limit=6)
print(docs)
