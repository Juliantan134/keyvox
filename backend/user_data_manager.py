from pathlib import Path
import json
import hashlib


# users.json in the same folder as this script
USER_FILE = Path(__file__).parent / "users.json"

def update_email(old_email, new_email, user_file=USER_FILE):
    """
    Updates a user's email from old_email to new_email in users.json.
    """
    with open(user_file, "r") as f:
        users = json.load(f)

    for user in users.values():
        if user.get("email") == old_email:
            user["email"] = new_email
            with open(user_file, "w") as f:
                json.dump(users, f, indent=4)
            return

    raise ValueError(f"No user with email '{old_email}' found.")

def load_users(user_file=USER_FILE):
    """Load all users from users.json"""
    with open(user_file, "r") as f:
        return json.load(f)

def get_user_by_username(username, user_file=USER_FILE):
    """Find user data by username"""
    users = load_users(user_file)
    for user in users.values():
        if user.get("username", "").lower() == username.lower():
            return user
    return None

def get_user_by_email(email, user_file=USER_FILE):
    """Find user data by email"""
    users = load_users(user_file)
    for user in users.values():
        if user.get("email", "").lower() == email.lower():
            return user
    return None

def update_email_by_name_and_blank_email(full_name, new_email, user_file=USER_FILE):
    """
    Updates a user's email using their full name, only if their email is blank.
    """
    with open(user_file, "r") as f:
        users = json.load(f)

    for user in users.values():
        if user.get("full_name") == full_name and user.get("email") == "":
            user["email"] = new_email
            with open(user_file, "w") as f:
                json.dump(users, f, indent=4)
            return

    raise ValueError(f"No user with full_name '{full_name}' and blank email found.")


def get_user_by_key(key, user_file=USER_FILE):
    """
    Find a user by their dictionary key in users.json.
    Example keys: 'jc', 'user102'
    """
    users = load_users(user_file)
    return users.get(key)


def hash_password(password: str) -> str:
    """Return SHA-256 hash of the password as hex."""
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def change_password(user_key: str, new_password: str, user_file=USER_FILE):
    """
    Updates the password_hash for the specified user in users.json.
    
    Args:
        user_key: The key in users.json (e.g., 'jc', 'user102').
        new_password: The new plaintext password to set.
    """
    with open(user_file, "r") as f:
        users = json.load(f)

    if user_key not in users:
        raise KeyError(f"User '{user_key}' not found in {user_file}.")

    users[user_key]['password_hash'] = hash_password(new_password)

    with open(user_file, "w") as f:
        json.dump(users, f, indent=4)

    print(f"Password for user '{user_key}' updated successfully.")

def get_user_key_by_email_or_name(email: str = "", full_name: str = "", user_file=USER_FILE):
    users = load_users(user_file)
    email = email.strip().lower()
    full_name = full_name.strip().lower()

    for key, user in users.items():
        user_email = user.get("email", "").lower()
        user_name = user.get("full_name", "").lower()

        # If both provided, require both to match
        if email and full_name:
            if user_email == email and user_name == full_name:
                return key
        # If only one provided, match on that
        elif email and user_email == email:
            return key
        elif full_name and user_name == full_name:
            return key

    return None

