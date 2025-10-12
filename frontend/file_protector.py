from cryptography.fernet import Fernet
import os

# The name of the file where the encryption key will be stored.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
KEY_FILE = os.path.join(SCRIPT_DIR, 'secret.key')

def generate_key():
    """Generates a key and saves it into a file."""
    key = Fernet.generate_key()
    with open(KEY_FILE, "wb") as key_file:
        key_file.write(key)
    print(f"Encryption key saved to {KEY_FILE}.")

def load_key():
    """Loads the key from the current directory named `secret.key`."""
    if not os.path.exists(KEY_FILE):
        generate_key()
    return open(KEY_FILE, "rb").read()

def encrypt_file(file_path):
    """Encrypts a file and saves it with a .locked extension."""
    key = load_key()
    f = Fernet(key)

    with open(file_path, "rb") as file:
        file_data = file.read()

    encrypted_data = f.encrypt(file_data)

    locked_file_path = file_path + ".locked"
    with open(locked_file_path, "wb") as file:
        file.write(encrypted_data)
    
    # Securely remove the original file after encryption
    os.remove(file_path)
    
    print(f"Encrypted '{file_path}' to '{locked_file_path}'")
    return locked_file_path

def decrypt_and_open_file(locked_file_path):
    """Decrypts a file, saves it temporarily, opens it, and cleans up."""
    key = load_key()
    f = Fernet(key)

    with open(locked_file_path, "rb") as file:
        encrypted_data = file.read()

    try:
        decrypted_data = f.decrypt(encrypted_data)
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None # Failed to decrypt

    # Create a temporary path for the decrypted file
    original_path = locked_file_path.replace(".locked", "")
    
    with open(original_path, "wb") as file:
        file.write(decrypted_data)
        
    print(f"Decrypted to temporary file: {original_path}")
    
    # Open the file with its default application
    os.startfile(original_path)
    
    return original_path # Return the path so we can delete it later


