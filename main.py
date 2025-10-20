"""
FastAPI Server - Cách hiện đại và nhanh nhất
"""

import warnings
warnings.filterwarnings("ignore", message=".*Pydantic V1 functionality.*")
from fastapi import FastAPI, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
import uvicorn
from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv
from typing import List, Dict

# Load environment variables
load_dotenv()

# MongoDB helpers
def get_db():
    mongodb_url = os.getenv("MONGODB_URL")
    db_name = os.getenv("MONGODB_DATABASE", "kjc-group-staging")
    client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
    return client[db_name]

# Tạo FastAPI app
app = FastAPI(
    title="My Python Server",
    description="Server Python đơn giản với FastAPI",
    version="1.0.0"
)

# Route cơ bản
@app.get("/")
async def root():
    return {"message": "KJC Python Server API running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "server": "running"}

@app.get("/api/data")
async def get_data():
    return {
        "data": ["item1", "item2", "item3"],
        "count": 3
    }

@app.get("/mongodb/test")
async def test_mongodb():
    try:
        # Kết nối MongoDB Atlas từ env
        mongodb_url = os.getenv("MONGODB_URL")
        client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
        client.server_info()  # Test connection
        
        # Test database
        db_name = os.getenv("MONGODB_DATABASE", "kjc-group-staging")
        db = client[db_name]
        collection = db.api_test
        
        # Insert test data
        test_doc = {"message": "Hello MongoDB", "timestamp": datetime.now()}
        result = collection.insert_one(test_doc)
        
        # Read back
        found_doc = collection.find_one({"_id": result.inserted_id})
        found_doc["_id"] = str(found_doc["_id"])  # Convert ObjectId to string
        
        client.close()
        
        return {
            "status": "success",
            "mongodb_connected": True,
            "inserted_id": str(result.inserted_id),
            "document": found_doc
        }
    except Exception as e:
        return {
            "status": "error",
            "mongodb_connected": False,
            "error": str(e)
        }



# Import user routes
from user_routes import router as user_router
app.include_router(user_router)

# Chạy server
if __name__ == "__main__":
    print("🚀 Starting FastAPI server...")
    print("📖 Docs: http://localhost:8000/docs")
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Cho phép truy cập từ bên ngoài
        port=8000        # Port server
    )