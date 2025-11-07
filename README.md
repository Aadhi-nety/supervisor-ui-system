# Supervisor UI System

A Flask-based web application that helps supervisors manage customer service requests with AI assistance.

## Video https://drive.google.com/file/d/1twyrW1IkVWWjqfvSmrwGbnWEBHDihDH8/view?usp=drive_link

## Features

- **Dashboard**: Overview of pending/resolved requests and knowledge base
- **Request Management**: View and respond to customer inquiries
- **AI Integration**: Groq AI agent for automated responses
- **Knowledge Base**: Store and manage common Q&A pairs
- **Real-time Updates**: Dynamic request status management

## Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd supervisor-ui-system
   # Create virtual environment (recommended)
   python -m venv venv

   # Activate virtual environment
   # On Windows:
   venv\Scripts\activate
   # On Mac/Linux:
   source venv/bin/activate
   ```

2. **Install Dependencies**
   ```bash
   # Install required packages
   pip install -r requirements.txt
   ```
3. **Configure Environment**
   ```bash
   # Create environment file
   cp .env.example .env

   # Add your Groq API key (get from https://console.groq.com)
   echo "GROQ_API_KEY=your_actual_groq_api_key_here" >> .env
   ```
4. **Run the Application**
   ```bash
   # Start the development server
   python app.py
   ```
5. **Access the Application**
   ```bash
   http://localhost:5000
   ```

## 📋 Prerequisites
- Python 3.8 or higher
- Groq API account (free at https://console.groq.com)

## 🎯 Usage
Access Main Features:
``` bash
Dashboard: http://localhost:5000
All Requests: http://localhost:5000/requests
Knowledge Base: http://localhost:5000/knowledge
Debug Routes: http://localhost:5000/debug-routes
```
## 🏗️ Architecture Notes
Key Technologies:
- Flask: Lightweight web framework
- Groq AI: Fast LLM inference engine
- Async Python: Efficient I/O handling
- Modular Services: Clean separation of concerns
Design Decisions:
- Chose Flask for rapid prototyping
- Used async services for better performance
- Modular architecture for maintainability
- Groq for millisecond response times

## 🔮 Next Improvements
- Database Integration - Replace in-memory storage
- User Authentication - Add login system
- Real-time Updates - WebSocket notifications
- Docker Deployment - Containerization
- API Rate Limiting - Abuse protection
