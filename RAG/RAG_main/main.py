from pdf_extraction import extract
from image_summary import generate_img_summaries
from database import create_multi_vector_retriever
from langchain.vectorstores import Chroma
from retriever import multi_modal_rag_chain
from langchain_huggingface import HuggingFaceEmbeddings
from pathlib import Path
from langchain_core.load import dumpd, dumps, load, loads
import json
import pickle
import os
from langchain.storage import LocalFileStore,InMemoryStore

if __name__=="__main__":
    directory="./RAG_main/"
    files = os.listdir(directory)
    pdf_files = [f for f in files if f.lower().endswith('.pdf')]
    if pdf_files:
        pdf_files_name=pdf_files[0]


        texts,tables,text_summaries, table_summaries = extract("./RAG_main/",pdf_files_name)
        img_base64_list, image_summaries = generate_img_summaries('./RAG_main/figures/')
        embedding_model=HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2', model_kwargs={"device": "cuda"})
        
        # The vectorstore to use to index the summaries
        vectorstore = Chroma(
            persist_directory="./chroma_db",
            collection_name="mm_RAG",
            embedding_function=embedding_model
        )
      
        # Create retriever
        retriever_multi_vector_img = create_multi_vector_retriever(
            vectorstore,
            text_summaries,
            texts,
            table_summaries,
            tables,
            image_summaries,
            img_base64_list,
        )
    
    
        # Create RAG chain
        chain_multimodal_rag = multi_modal_rag_chain(retriever_multi_vector_img)
        retriever_multi_vector_img.vectorstore.persist()
    else:
        print("no pdf file")
    

    