# Multi Chat AI

Multi Chat AI is a powerful, intelligent chatbot platform featuring a built-in marketplace for AI applications. Powered by Google's Gemini AI, it offers seamless conversational experiences, content summarization, analysis, and code explanation capabilities.

## Features

- **Built-in Gemini Chatbot**: Integrated directly via an internal MCP (Model Context Protocol) server.
- **Marketplace**: Browse, enable, and manage AI applications.
- **Rich Chat Interface**: Modern UI with real-time streaming, Markdown support, and code syntax highlighting.
- **AI Tools**:
  - **Chat**: General purpose conversational AI.
  - **Summarize**: Condense articles and documents.
  - **Analyze**: Sentiment analysis and content breakdown.
  - **Code Explain**: Detailed explanation of programming code.
- **Secure Authentication**: User registration, login, and comprehensive role-based access control.

## Tech Stack

- **Frontend**: React.js, Vite, TailwindCSS
- **Backend**: Python, FastAPI
- **Database**: MySQL (Async SQLAlchemy)
- **AI Model**: Google Gemini 1.5/3.0 Flash for simple chat

## Prerequisites

- **Node.js** (v18+)
- **Python** (v3.10+)
- **MySQL Server**
- **Git**

## Setup Instructions

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/multi-chat-ai.git
cd multi-chat-ai
```

### 2. Backend Setup
Navigate to the backend directory:
```bash
cd backend
```

Create a virtual environment:
```bash
python -m venv venv
# Windows
.\venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Create `.env` file from example:
```bash
cp .env.example .env
```
Update `.env` with your database credentials and **Gemini API Key**.

Run the database setup:
```bash
# This will create tables and seed the initial data
python seed_builtin_chatbot.py
```

Start the backend server:
```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
The API will be available at `http://localhost:8000`.

### 3. Frontend Setup
Open a new terminal and navigate to the frontend directory:
```bash
cd frontend
```

Install dependencies:
```bash
npm install
```

Start the development server:
```bash
npm run dev
```
The application will be accessible at `http://localhost:3000` (or the port shown in terminal).

## How It Works

Multi Chat AI uses a clean **frontend-backend architecture**:
1.  **React Frontend**: Handles the UI, user interactions, and communicates with the backend via REST API.
2.  **FastAPI Backend**: Manages users, chat sessions, and marketplace apps.
3.  **Inbuilt MCP Server**: The backend hosts an internal MCP server that wraps the Google Gemini API. When you chat, the "Chat" tool is invoked dynamically via this server, routing your request to the AI model and returning the response.

## Usage

1.  **Sign Up/Login**: Create an account to get started.
2.  **Marketplace**: Go to "Enabled Apps" or "Marketplace".
3.  **Enable Gemini**: Find "Gemini AI Assistant" and click "Enable".
4.  **Chat**: Navigate to the Chat section and start a conversation!

