## 🌐 Live Demo

**Try PriceLens AI:** https://pricelens-rag-assistant.vercel.app/

**GitHub Repository:** https://github.com/Ramana0306/pricelens-rag-assistant

Explore the application by submitting a supported product URL and asking questions about its features and specifications.

# 🛍️ PriceLens AI – Product RAG Assistant

An AI-powered product assistant that allows users to ask questions about products using a product URL. It extracts product information, stores it in a vector database, and generates context-based answers using Retrieval-Augmented Generation (RAG).

## 📌 Project Overview

PriceLens AI helps users understand product features and specifications without manually searching through long product descriptions.

Users can provide a product URL, build a knowledge base from the extracted product information, and ask questions through an AI-powered chat interface.

## ✨ Features

- 🔗 **Product URL Extraction** – Extract product information from supported product pages.
- 🧠 **RAG Pipeline** – Retrieve relevant product information before generating answers.
- 💬 **AI Chat Assistant** – Ask questions about product features and specifications.
- 🗄️ **Vector Database** – Store and retrieve document embeddings using PostgreSQL and pgvector.
- 🤖 **Gemini AI Integration** – Generate answers using Google's Gemini API.
- 🌐 **Web Interface** – Interact with the application through a React frontend.
- ☁️ **Cloud Deployment** – Deploy the frontend and backend separately.

## 🛠️ Tech Stack

| Technology | Purpose |
|---|---|
| Python | Backend development |
| FastAPI | REST API development |
| React | Frontend interface |
| Vite | Frontend development and build |
| PostgreSQL | Database |
| pgvector | Vector similarity search |
| Google Gemini API | AI answer generation |
| Sentence Transformers | Text embeddings |
| BeautifulSoup | HTML parsing |
| Supabase | Hosted PostgreSQL database |
| Render | Backend deployment |
| Vercel | Frontend deployment |
| Git & GitHub | Version control |

## 🔄 How It Works

1. **Enter a product URL:** The user submits a supported product page.
2. **Extract information:** The backend fetches the page and extracts available product content.
3. **Process the text:** The extracted content is cleaned and split into smaller chunks.
4. **Generate embeddings:** Text chunks are converted into vector embeddings.
5. **Store the knowledge base:** Chunks and embeddings are stored in PostgreSQL with pgvector.
6. **Ask a question:** The user submits a question about the product.
7. **Retrieve relevant chunks:** The system searches for product information relevant to the question.
8. **Generate an answer:** Gemini uses the retrieved context to generate a response.

## 🏗️ Architecture

```text
User
 |
 v
React + Vite Frontend
 |
 v
FastAPI Backend
 |
 v
Product URL Extraction
 |
 v
Text Cleaning and Chunking
 |
 v
Embedding Generation
 |
 v
PostgreSQL + pgvector
 |
 v
Similarity Search
 |
 v
Google Gemini API
 |
 v
AI-Generated Answer
```

## 📂 Project Structure

```text
pricelens-rag-assistant/
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   └── product_service.py
│   ├── requirements.txt
│   └── .python-version
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── index.html
├── .gitignore
└── README.md
```



## 🔐 Environment Variables

Configure these variables in your local environment and deployment dashboard.

| Variable | Description |
|---|---|
| `GEMINI_API_KEY` | Google Gemini API key |
| `DATABASE_URL` | PostgreSQL connection URL |
| `VITE_API_URL` | Backend API base URL for the frontend |

The exact names must match your application's configuration. Do not publish real secret values.

## 🚀 Deployment

The application can be deployed using:

- **Frontend:** Vercel
- **Backend:** Render
- **Database:** Supabase PostgreSQL with pgvector

Set the required environment variables in each hosting platform before testing the deployed application.

## 🧪 Example Usage

1. Open the PriceLens AI application.
2. Enter a supported product URL.
3. Allow the backend to extract and save the product information.
4. Ask questions such as:
   - What are the main features of this product?
   - What specifications are mentioned?
   - What are the advantages of this product?
   - Summarize the available product information.

Answers depend on the information successfully extracted and stored in the knowledge base.

## 🎯 Learning Outcomes

This project demonstrates practical experience with:

- Building REST APIs using FastAPI.
- Implementing a Retrieval-Augmented Generation pipeline.
- Extracting and processing web content.
- Creating text embeddings and performing vector similarity search.
- Integrating a large language model with a backend.
- Connecting Python applications to PostgreSQL.
- Building a React-based user interface.
- Deploying a full-stack application to cloud platforms.

## ⚠️ Limitations

- Some e-commerce websites block automated page extraction.
- The quality of answers depends on the extracted product information.
- Gemini API usage may be subject to quotas and billing limits.
- AI-generated answers may contain inaccuracies and should be checked against the original product listing.

## 🔮 Future Enhancements

- Support more e-commerce websites.
- Add product comparison between multiple URLs.
- Display source references for generated answers.
- Improve extraction error handling.
- Add product price history and availability tracking.
- Add user authentication and saved product collections.

## 👨‍💻 Author

**Ramana M.**

GitHub: [Ramana0306](https://github.com/Ramana0306)

## 📄 License

This project is intended for educational and learning purposes. Add a license file if you want to specify the terms under which others may use, modify, and distribute the project.

