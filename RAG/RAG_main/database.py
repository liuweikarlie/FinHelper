import uuid

from langchain.retrievers.multi_vector import MultiVectorRetriever
from langchain.storage import LocalFileStore, InMemoryStore
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document
from langchain_community.chat_models import ChatOllama
import pickle 
import json

from langchain_core.load import dumpd, dumps, load, loads

class JSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Document):
            return obj.dict()
        return super().default(obj)


def save_retriever_state(retriever, docstore_path):
    retriever.vectorstore.persist()
    docstore_data = {k: (v.dict() if isinstance(v, Document) else v) for k, v in retriever.docstore.store.items()}
    with open(docstore_path, 'w') as f:
        json.dump(docstore_data, f, cls=JSONEncoder)
        
def save_object(obj, filename):
    with open(filename, 'wb') as outp:  # Overwrites any existing file.
        pickle.dump(obj, outp)
        
def create_multi_vector_retriever(
    vectorstore, text_summaries, texts, table_summaries, tables, image_summaries, images
):
    """
    Create retriever that indexes summaries, but returns raw images or texts
    """

    # Initialize the storage layer
    # store_path = "./data"  
    store = InMemoryStore()
    id_key = "doc_id"

    # Create the multi-vector retriever
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        docstore=store,
        id_key=id_key,
    )

    # Helper function to add documents to the vectorstore and docstore
    def add_documents(retriever, doc_summaries, doc_contents):
        doc_ids = [str(uuid.uuid4()) for _ in doc_contents]
        summary_docs = [
            Document(page_content=s, metadata={id_key: doc_ids[i]})
            for i, s in enumerate(doc_summaries)
        ]
        retriever.vectorstore.add_documents(summary_docs)
        retriever.docstore.mset(list(zip(doc_ids, doc_contents)))

    # Add texts, tables, and images
    # Check that text_summaries is not empty before adding
    if text_summaries:
        add_documents(retriever, text_summaries, texts)
    # Check that table_summaries is not empty before adding
    if table_summaries:
        add_documents(retriever, table_summaries, tables)
    # Check that image_summaries is not empty before adding
    if image_summaries:
        add_documents(retriever, image_summaries, images)

    vectorstore.persist()
    save_retriever_state(retriever, "./RAG2/docstore.json")
    

   
    
    

    


    

    return retriever


