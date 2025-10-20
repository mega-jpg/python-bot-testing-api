from fastapi import APIRouter, HTTPException
from typing import List, Dict
from datetime import datetime
from pymongo import MongoClient
from bson import ObjectId
import os
import bcrypt

def get_db():
    mongodb_url = os.getenv("MONGODB_URL")
    db_name = os.getenv("MONGODB_DATABASE", "kjc-group-staging")
    client = MongoClient(mongodb_url, serverSelectionTimeoutMS=5000)
    return client[db_name]

def convert_objectid_fields(doc):
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    for k, v in list(doc.items()):
        if isinstance(v, ObjectId):
            doc[k] = str(v)
    return doc

router = APIRouter()

@router.post("/users")
async def create_user(user: Dict):
    db = get_db()
    now = datetime.utcnow().isoformat()
    # Fill missing fields with defaults
    schema = {
        "username": None,
        "password": None,
        "email": None,
        "phone": "0909090909",
        "type": "user",
        "status": "active",
        "avatarUrl": "",
        "point": 0,
        "totalPoint": 0,
        "levelId": "",
        "externalVerifyHistoryIds": [],
        "isVerifired": False,
        "createdAt": now,
        "updatedAt": now
    }
    # Overwrite schema with provided user fields
    for k in user:
        schema[k] = user[k]
    # Check unique username
    if schema["username"]:
        existing = db.users.find_one({"username": schema["username"], "deletedAt": {"$in": [None, ""]}})
        if existing:
            # Return 200 with message and existing user info
            existing = convert_objectid_fields(existing)
            return {"message": "Username already exists, user not created.", "user": existing}
    # Set email if not provided
    if not schema["email"] and schema["username"]:
        schema["email"] = f"{schema['username']}@itkjc.com"
    # Hash password if present and not already hashed
    if schema["password"] and not str(schema["password"]).startswith("$2b$"):
        hashed = bcrypt.hashpw(schema["password"].encode("utf-8"), bcrypt.gensalt())
        schema["password"] = hashed.decode("utf-8")
    # Always update createdAt and updatedAt
    schema["createdAt"] = now
    schema["updatedAt"] = now
    result = db.users.insert_one(schema)
    # Add the inserted _id as string for response, if needed
    schema["_id"] = str(result.inserted_id)
    return schema

@router.get("/users")
async def list_users() -> List[Dict]:
    db = get_db()
    users = list(db.users.find({"deletedAt": {"$in": [None, ""]}}))
    return [convert_objectid_fields(u) for u in users]

@router.get("/users/{user_id}")
async def get_user(user_id: str) -> Dict:
    db = get_db()
    user = db.users.find_one({"_id": ObjectId(user_id), "deletedAt": {"$in": [None, ""]}})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    user.pop("_id", None)
    return user

@router.put("/users/{user_id}")
async def update_user(user_id: str, user: Dict) -> Dict:
    db = get_db()
    user["updatedAt"] = datetime.utcnow().isoformat()
    result = db.users.update_one({"_id": ObjectId(user_id)}, {"$set": user})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    updated = db.users.find_one({"_id": ObjectId(user_id)})
    updated.pop("_id", None)
    return updated

@router.delete("/users/by-username/{username}")
async def delete_user_by_username(username: str):
    db = get_db()
    now = datetime.utcnow().isoformat()
    # Delete users with username containing or starting with the given username
    regex = f"^{username}"  # starts with
    query = {"$or": [
        {"username": {"$regex": username, "$options": "i"}},
        {"username": {"$regex": regex, "$options": "i"}}
    ]}
    result = db.users.update_many(query, {"$set": {"deletedAt": now}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="No user found with username containing or starting with: " + username)
    return {"status": "deleted", "matched": result.matched_count, "username_contains_or_startswith": username}
