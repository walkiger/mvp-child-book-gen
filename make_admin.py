"""
Script to set a user as an admin.
"""

import sys
from sqlalchemy.orm import Session
from app.database.session import engine, get_db
from app.database.models import User, Base
from app.config import settings

def make_user_admin(email):
    """
    Set a user as an admin by their email address.
    """
    db = next(get_db())
    
    try:
        # Find the user by email
        user = db.query(User).filter(User.email == email).first()
        
        if not user:
            print(f"User with email {email} not found.")
            return False
        
        # Set user as admin
        user.is_admin = True
        db.commit()
        
        print(f"User {user.username} ({user.email}) is now an admin!")
        return True
        
    except Exception as e:
        db.rollback()
        print(f"Error making user admin: {str(e)}")
        return False

def main():
    """
    Main entry point for the script.
    """
    if len(sys.argv) < 2:
        print("Usage: python make_admin.py <email>")
        return
    
    email = sys.argv[1]
    make_user_admin(email)

if __name__ == "__main__":
    main() 