# models.py
from flask_login import UserMixin
from bson.objectid import ObjectId
from extensions import db

class User(UserMixin):
    """User model for authentication."""
    def __init__(self, user_data):
        self.id = str(user_data["_id"])
        self.username = user_data["username"]
        self.password_hash = user_data["password_hash"]
        self.role = user_data.get("role", "user")

def load_user(user_id):
    """Loads a user from the database for Flask-Login."""
    if db is not None:
        user_data = db.users.find_one({"_id": ObjectId(user_id)})
        return User(user_data) if user_data else None
    return None