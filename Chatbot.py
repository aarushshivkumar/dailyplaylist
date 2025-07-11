import torch
import sys
sys.path.append(r"C:/Users/development.pc/AppData/Local/Programs/Python/Python312/Lib/site-packages")
#device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
import os
#os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "0"
import json
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from unsloth import FastLanguageModel
from transformers import pipeline
from langchain.llms import HuggingFacePipeline
from langchain.chains import RetrievalQA
model_path="model/downloaded_llama3.2"
# Load JSON data
with open("FAQ.json", "r") as f:
    json_data = json.load(f)

# Convert to LangChain documents
documents = []
for entry in json_data:
    # Format as a readable text record
    text = (
        f"Site: {entry['sitename']}\n"
        f"Operator: {entry['operatorname']}\n"
        f"Timestamp: {entry['timestamp']}\n"
        f"Temperature: {entry['temperature']}°C\n"
        f"Voltage: {entry['voltage']} V\n"
        f"Current: {entry['current']} A"
    )
    documents.append(Document(page_content=text, metadata={"timestamp": entry["timestamp"]}))

# Split into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
chunks = splitter.split_documents(documents)

# Embed using sentence-transformers
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Create FAISS vector store
vectorstore = FAISS.from_documents(chunks, embedding_model)
retriever = vectorstore.as_retriever()

# Split documents
splitter = RecursiveCharacterTextSplitter(chunk_size=256, chunk_overlap=10)
chunks = splitter.split_documents(documents)

# Embed with Sentence Transformers
embedding_model = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Create FAISS index
vectorstore = FAISS.from_documents(chunks, embedding_model)
retriever = vectorstore.as_retriever()

model_id = "unsloth/llama-3-8b-Instruct-bnb-4bit"

model, tokenizer = FastLanguageModel.from_pretrained(
    model_name=model_id,
    max_seq_length=4096,
    dtype=None,
    load_in_4bit=True,
)

FastLanguageModel.for_inference(model)
model.save_pretrained(model_path)
tokenizer.save_pretrained(model_path)
llm_pipe = pipeline("text-generation", model=model, tokenizer=tokenizer, max_new_tokens=256)

llm = HuggingFacePipeline(pipeline=llm_pipe)
rag_chain = RetrievalQA.from_chain_type(llm=llm, retriever=retriever)

# Ask a question
query = "What was the temperature at 123 Main St, Anytown?"
result = rag_chain.run(query)
print(result)
