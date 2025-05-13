from flask import Flask, request, jsonify
import os, json
from typing import Dict, List
from PyPDF2 import PdfReader
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationalRetrievalChain
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

# === Globals ===
USER_DATA_FILE = "users.json"
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
session_chains: Dict[str, ConversationalRetrievalChain] = {}
chat_histories: Dict[str, List[tuple[str, str]]] = {}

# === User Management ===
def load_user_data():
    if os.path.exists(USER_DATA_FILE):
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    return {}

def save_user_data(data):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f)

def add_session_to_user(username: str, session_id: str):
    users = load_user_data()
    if username in users:
        sessions = users[username].setdefault("sessions", [])
        if session_id not in sessions:
            sessions.append(session_id)
            save_user_data(users)

# === PDF Processing ===
def extract_text_from_pdf(file_path):
    reader = PdfReader(file_path)
    return "".join([page.extract_text() or "" for page in reader.pages])

def process_multiple_pdfs(filepaths):
    all_text = ""
    for path in filepaths:
        all_text += extract_text_from_pdf(path)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    splits = splitter.split_text(all_text)
    embeddings = GoogleGenerativeAIEmbeddings(model='models/text-embedding-004')
    vector_store = FAISS.from_texts(splits, embeddings)
    return vector_store.as_retriever()

# === Chat Chain Setup ===
custom_prompt = PromptTemplate.from_template("""
Always respond in English only.
Use the retrieved document to enhance your response.
If something has been asked out of context, then use your own knowledge base to answer.

{context}

Question: {question}
Answer:
""")

def get_chain(session_id: str, retriever):
    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)
    chain = ConversationalRetrievalChain.from_llm(
        llm=llm,
        retriever=retriever,
        memory=memory,
        combine_docs_chain_kwargs={"prompt": custom_prompt}
    )
    session_chains[session_id] = chain
    return chain

def load_history(session_id: str):
    filepath = f"history/{session_id}.json"
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return json.load(f)
    return []

def save_history(session_id: str, history: List[tuple[str, str]]):
    os.makedirs("history", exist_ok=True)
    with open(f"history/{session_id}.json", "w") as f:
        json.dump(history, f)

# === Flask Endpoints ===

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    username, password = data.get("username"), data.get("password")
    users = load_user_data()
    if username in users:
        return jsonify({"error": "User already exists"}), 400
    users[username] = {"password": password, "sessions": []}
    save_user_data(users)
    return jsonify({"message": f"User {username} registered."})

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username, password = data.get("username"), data.get("password")
    users = load_user_data()
    if username not in users or users[username]["password"] != password:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"message": f"User {username} logged in."})

@app.route("/submit_id", methods=["POST"])
def submit_id():
    data = request.json
    username = data.get("username")
    session_id = data.get("session_id")
    if not session_id or not username:
        return jsonify({"error": "Missing username or session_id"}), 400
    add_session_to_user(username, session_id)
    return jsonify({"message": f"Session ID {session_id} added for {username}."})

@app.route("/upload_pdfs", methods=["POST"])
def upload_pdfs():
    session_id = request.form.get("session_id")
    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400
    files = request.files.getlist("pdfs")
    if not files:
        return jsonify({"error": "No files uploaded"}), 400

    saved_paths = []
    for f in files:
        path = f"temp_{f.filename}"
        f.save(path)
        saved_paths.append(path)

    retriever = process_multiple_pdfs(saved_paths)
    get_chain(session_id, retriever)

    for path in saved_paths:
        os.remove(path)  # cleanup
    return jsonify({"message": f"PDFs processed for session {session_id}."})

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json
    session_id = data.get("session_id")
    message = data.get("message")
    if session_id not in session_chains:
        return jsonify({"error": "Session not initialized. Upload PDFs first."}), 400
    history = chat_histories.get(session_id, [])
    response = session_chains[session_id].run(message)
    history.append((message, response))
    chat_histories[session_id] = history
    save_history(session_id, history)
    return jsonify({"response": response})

@app.route("/chat_history/<session_id>", methods=["GET"])
def chat_history(session_id):
    history = load_history(session_id)
    return jsonify({"history": history})

if __name__ == "__main__":
    app.run(debug=True)
