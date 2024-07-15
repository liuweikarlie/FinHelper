from langchain_community.vectorstores import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.storage import InMemoryStore
from langchain.retrievers.multi_vector import MultiVectorRetriever
from retriever import multi_modal_rag_chain
import json
import uuid

from langchain.schema import Document
def get_answer(question):
   
        embedding_model=HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2', model_kwargs={'device': 'cuda:0'})
   
        vectorstore=Chroma(collection_name="mm_RAG",
                           embedding_function=embedding_model,
                           persist_directory="./chroma_db")
        with open("./RAG_main/docstore.json", 'r') as f:
            docstore_data = json.load(f)
        docstore = InMemoryStore()
        for k, v in docstore_data.items():
            if isinstance(v, dict) and 'page_content' in v:
                docstore.mset([(k, Document(**v))])
            else:
                docstore.mset([(k, v)])
        retriever = MultiVectorRetriever(
            vectorstore=vectorstore,
            docstore=docstore,
            id_key="doc_id",
        )
        get_docs=retriever.get_relevant_documents(question)
        
        
        chain_multimodal_rag = multi_modal_rag_chain(retriever)
        answer = chain_multimodal_rag.invoke(question) 

        
        print(answer)
        return get_docs,answer


question=""
print(get_answer(question))