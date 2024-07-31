from random import choice, randint
import ollama
from rag import query_rag, load_documents, split_documents

def get_response(user_input: str) -> str:
    
    lowered_user_input = user_input.lower()
  
    if 'uncle' in lowered_user_input:
        documents: List = load_documents()
        chunks: List = split_documents(documents)
        response: str = query_rag(lowered_user_input)
        
        return response
    