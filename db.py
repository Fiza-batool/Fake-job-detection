"""
Database Configuration for MongoDB
Backend/database/db.py
"""

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# MongoDB Configuration
MONGO_URI = "mongodb://localhost:27017/"
DATABASE_NAME = "jobdetect"

# Global database connection
_client = None
_db = None


def get_database():
    """Get MongoDB database instance"""
    global _client, _db

    if _db is not None:
        return _db

    try:
        _client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
        _client.admin.command('ping')
        _db = _client[DATABASE_NAME]
        print(f"✅ MongoDB Connected Successfully")
        return _db

    except ConnectionFailure as e:
        print(f"❌ MongoDB Connection Failed: {e}")
        print("⚠️  Make sure MongoDB is running!")
        return None
    except Exception as e:
        print(f"❌ Database Error: {e}")
        return None


def get_users_collection():
    """Get users collection"""
    db = get_database()
    if db is not None:
        return db['users']
    return None


def get_detection_history_collection():
    """Get detection history collection"""
    db = get_database()
    if db is not None:
        return db['detection_history']
    return None


def get_reports_collection():
    """Get reports collection"""
    db = get_database()
    if db is not None:
        return db['reports']
    return None


def get_feedback_collection():
    """Get feedback collection"""
    db = get_database()
    if db is not None:
        return db['feedback']
    return None


def close_connection():
    """Close MongoDB connection"""
    global _client
    if _client:
        _client.close()
        print("✅ MongoDB connection closed")


def create_indexes():
    """Create database indexes for better performance"""
    try:
        users_col = get_users_collection()
        if users_col is not None:
            users_col.create_index('email', unique=True)
            print("✅ Created unique index on users.email")

        history_col = get_detection_history_collection()
        if history_col is not None:
            history_col.create_index([('user_email', 1), ('timestamp', -1)])
            print("✅ Created indexes on detection_history")

    except Exception as e:
        print(f"⚠️  Index creation warning: {e}")


# Initialize on import
if __name__ != "__main__":
    get_database()
    create_indexes()