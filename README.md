# SalesGenie AI - Backend

SalesGenie AI is an AI-powered sales assistant designed to help sales teams manage leads, analyze companies, score leads, generate personalized outreach, summarize sales conversations, synchronize CRM data, and monitor sales analytics.

This repository contains the backend implementation of the SalesGenie AI project.

## 🚀 Features

- Lead Management
- Company Intelligence and Analysis
- AI-powered Lead Scoring
- Personalized Email and Outreach Generation
- Sales Conversation Summarization
- CRM Synchronization
- Sales Analytics and Dashboard APIs
- User Authentication
- Password Reset
- Google Authentication Support
- Gemini AI Integration

## 🛠️ Technologies Used

- Python
- FastAPI
- SQLAlchemy
- Pydantic
- SQLite / SQL Database
- Google Gemini API
- Uvicorn

## 📁 Project Structure

```text
salesgenie/
│
├── database/
│   ├── connection.py
│   └── models.py
│
├── modules/
│   ├── module1_leads.py
│   ├── module2_analysis.py
│   ├── module3_email.py
│   ├── module4_scoring.py
│   ├── module5_crm.py
│   ├── module5_summary.py
│   ├── module6_analytics.py
│   ├── module6_dashboard.py
│   └── module7_auth.py
│
├── services/
│   └── gemini_service.py
│
├── main.py
├── requirements.txt
└── README.md
