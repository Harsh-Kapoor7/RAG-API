# RAG-API


# 📘 Gemini PDF Chat API — Documentation

A Flask-based API to register/login users, upload PDFs, run conversational PDF-based RAG using Google Gemini, and fetch chat history.

**Base URL:**
```
http://localhost:5000
```

**Deployed URL:**
```
https://rag-api-c2vm.onrender.com
```

---

## 🔐 1. Register User

**Endpoint:** `POST /register`  
**Description:** Register a new user.

### Request
```json
{
  "username": "testuser",
  "password": "testpass"
}
```

### cURL
```bash
curl -X POST https://rag-api-c2vm.onrender.com/register \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'
```

---

## 🔓 2. Login User

**Endpoint:** `POST /login`  
**Description:** Log in an existing user.

### Request
```json
{
  "username": "testuser",
  "password": "testpass"
}
```

### cURL
```bash
curl -X POST https://rag-api-c2vm.onrender.com/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "testpass"}'
```

---

## 📄 3. Upload PDFs

**Endpoint:** `POST /upload_pdfs`  
**Description:** Upload one or more PDF files and initialize a chat session.

### Form Data
| Key        | Value         | Type  |
|------------|---------------|-------|
| `username` | `testuser`    | Text  |
| `session_id` | `session_xyz` | Text  |
| `pdfs`     | PDF file(s)   | File (repeatable) |

### cURL
```bash
curl -X POST https://rag-api-c2vm.onrender.com/upload_pdfs \
  -F "username=testuser" \
  -F "session_id=session_xyz" \
  -F "pdfs=@/path/to/file1.pdf" \
  -F "pdfs=@/path/to/file2.pdf"
```

---

## 💬 4. Ask a Question

**Endpoint:** `POST /chat`  
**Description:** Ask a question within a specific session ID.

### Request
```json
{
  "session_id": "session_xyz",
  "message": "What is this document about?"
}
```

### cURL
```bash
curl -X POST https://rag-api-c2vm.onrender.com/chat \
  -H "Content-Type: application/json" \
  -d '{"session_id": "session_xyz", "message": "What is this document about?"}'
```

---

## ➕ 6. Submit Session ID

**Endpoint:** `POST /submit_id`  
**Description:** Link a session ID to a specific user.

### Request
```json
{
  "username": "testuser",
  "session_id": "session_xyz"
}
```

### cURL
```bash
curl -X POST https://rag-api-c2vm.onrender.com/submit_id \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "session_id": "session_xyz"}'
```

---

## 📜 6. Get Chat History

**Endpoint:** `GET /chat_history/<session_id>`  
**Description:** Fetch chat history for a session.

### Example
```
GET /chat_history/session_xyz
```

### cURL
```bash
curl https://rag-api-c2vm.onrender.com/chat_history/session_xyz
```

---

## 🧠 Notes

- PDF files must be `.pdf` format.
- Session IDs are used to persist chat memory and store chat histories.
- History is stored in JSON files under `history/` folder.
- Vector search is powered by FAISS with Gemini embeddings.
- Chat uses LangChain’s `ConversationalRetrievalChain`.
