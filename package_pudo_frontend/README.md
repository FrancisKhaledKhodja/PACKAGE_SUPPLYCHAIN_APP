# Frontend

This folder will contain a separate UI project (e.g., React + Vite). The UI should consume the backend API at /api/*.

Suggested steps:
1. npm create vite@latest frontend -- --template react-ts
2. cd frontend && npm i && npm run dev
3. Configure VITE_API_BASE_URL to point to the Flask API (http://127.0.0.1:5001).
