"""
Index - Local Knowledge Base with Semantic Search

Entry point for the application.
"""

import uvicorn

from src.api import create_app

# Create the FastAPI application
app = create_app()

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
