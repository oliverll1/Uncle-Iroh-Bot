from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders.pdf import PyPDFDirectoryLoader
from langchain.schema.document import Document
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.ollama import OllamaEmbeddings
from langchain_community.llms.ollama import Ollama
from langchain.prompts import ChatPromptTemplate

DATA_PATH = "data"
CHROMA_PATH = "chroma"

def load_documents() -> list[Document]:
    document_loader = PyPDFDirectoryLoader(DATA_PATH)
    return document_loader.load()

def calculate_chunk_ids(chunks: list[Document]):

    # This will create IDs like "data/iroh.pdf:6:2"
    # Page Source : Page Number : Chunk Index

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page")
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Set chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id

    return chunks

def get_embeddings() -> OllamaEmbeddings:
    embeddings = OllamaEmbeddings(
        model='llama3',
    )
    
    return embeddings

def add_to_chroma(chunks: list[Document]) -> None:
    # Load the existing database.
    db = Chroma(
        persist_directory=CHROMA_PATH, embedding_function=get_embeddings()
    )

    # Calculate Chunk IDs.
    chunks_with_ids = calculate_chunk_ids(chunks)

    # Add or Update the documents.
    existing_items = db.get(include=[])  # IDs are always included by default
    existing_ids = set(existing_items["ids"])
    print(f"Number of existing documents in DB: {len(existing_ids)}")

    # Only add documents that don't exist in the DB.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        db.add_documents(new_chunks, ids=new_chunk_ids)

    else:
        print("✅ No new documents to add")
        

def split_documents(documents: list[Document]) -> list[Document]:
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=100,
        length_function=len,
        is_separator_regex=False,
    )
   
    chunks = text_splitter.split_documents(documents)
    # print(f"Splited {len(documents)} into {len(chunks)} chunks")
    return chunks
    



def clear_database():
    if os.path.exists(CHROMA_PATH):
        shutil.rmtree(CHROMA_PATH)



PROMPT_TEMPLATE = """
You are Iroh (also known as Uncle Iroh), a character from the Last Airbender series. Do not tell anyone you are an AI language model. 

Don't mention that you are wise, speak like a normal person but a wiser normal person.
If you get asked something, be precise and concrete with your answer, dont write more than you need.
The first thing you need to do is provide your answer to the question or message from the user before offering any additional input.

Don't call yourself 'Uncle'

You can answer questions and respond to comments naturally, referring to the information below when needed.

{context}

Remember that in the provided chat conversation you are the user 'uncle iroh#[id number]'. 
Try to not repeat yourself or the answers you have given before.
Don't add your user to the beginning of your response.
Answers must have less than 2000 characters. Do not go beyond this limit.

---

Follow the context and respond to the following conversation, pay special attention to the last message given by the user: 

{question}
"""

def query_rag(query_text: str):
    db = Chroma(persist_directory=CHROMA_PATH, embedding_function=get_embeddings())
    results = db.similarity_search_with_score(query_text, k=5)
    
    print(results)
    
    context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results])
    prompt_template = ChatPromptTemplate.from_template(PROMPT_TEMPLATE)
    prompt = prompt_template.format(context=context_text, question=query_text)
    
    
    model = Ollama(model='llama3')
    response_text = model.invoke(prompt)
    
    sources = [doc.metadata.get('id', None) for doc, _score in results]
    
    return response_text
