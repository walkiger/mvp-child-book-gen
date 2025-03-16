"""
Script to check users and make a user an admin.
"""

from app.database.session import get_db
from app.database.models import User

def check_users():
    """List all users in the database"""
    db = next(get_db())
    users = db.query(User).all()
    
    print(f"Found {len(users)} users:")
    for i, user in enumerate(users, 1):
        print(f"{i}. Email: {user.email}, Username: {user.username}, Admin: {getattr(user, 'is_admin', False)}")
    
    return users

def make_admin(user_id):
    """Make a user an admin by ID"""
    db = next(get_db())
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        print(f"User with ID {user_id} not found")
        return
    
    user.is_admin = True
    db.commit()
    print(f"User {user.username} ({user.email}) is now an admin!")

if __name__ == "__main__":
    users = check_users()
    
    if users:
        user_id = input("\nEnter the ID of the user to make admin (or press Enter to skip): ")
        if user_id.strip():
            make_admin(int(user_id))
    else:
        print("No users found. Please register a user first.") 