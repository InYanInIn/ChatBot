# 🧠 ChatAI Platform

An interactive web application built with **FastAPI**, **Streamlit**, and **Ollama**, providing a user-friendly interface for conversing with a local language model.

## 🚀 Features

- 🔐 User registration and authentication  
- 💬 Chat with a local LLM via FastAPI (Ollama)  
- 📝 Persistent storage of message and conversation history in PostgreSQL  
- 🧠 Automatic generation of conversation titles from the first user message  
- 📊 Intuitive UI powered by Streamlit

## ⚙️ Technology Stack

- **Backend:** FastAPI, SQLAlchemy, Alembic  
- **Frontend:** Streamlit  
- **LLM:** Ollama (self-hosted)  
- **Database:** PostgreSQL + asyncpg  
- **Authentication:** JWT, passlib[bcrypt]  

## 🛡️ Security

- Passwords hashed using `bcrypt`  
- Protected endpoints via `Depends(get_current_user)`  
- Signed JWT tokens using a secret key
