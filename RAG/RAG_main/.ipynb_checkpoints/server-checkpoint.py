from flask import Flask, request, jsonify
from langchain.storage import InMemoryStore
from langchain.retrievers.multi_vector import MultiVectorRetriever
from database import create_multi_vector_retriever
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.vectorstores import Chroma
from retriever import multi_modal_rag_chain
import pickle
from langchain_core.load import dumpd, dumps, load, loads
import json

app = Flask(__name__)

class QASystem:
    def get_answer(self, question):
   
        embedding_model=HuggingFaceEmbeddings(model_name='sentence-transformers/all-mpnet-base-v2', model_kwargs={'device': 'cuda:0'})
   
        vectorstore=Chroma(collection_name="mm_RAG",
                           embedding_function=embedding_model,
                           persist_directory="./chroma_db")
        with open("./RAG2/docstore.json", 'r') as f:
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


re=QASystem()
# re.get_answer("what is the opinion for property market?")
@app.route('/api/ask', methods=['POST'])
def ask_question():
    question = request.json.get('question')
    get_docs, answer = qa_system.get_answer(question)
    return jsonify({'llm_answer_for_retriever_doc': answer,'retriever_doc':get_docs})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)  