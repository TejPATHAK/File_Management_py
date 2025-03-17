import os
import shutil
import time
import boto3
import zipfile
import schedule           # For scheduling auto-organization
import time as t          # Used in the schedule loop
import logging
import getpass
import jwt                # For JWT authentication
from cryptography.fernet import Fernet
from botocore.exceptions import NoCredentialsError
from rapidfuzz import process, fuzz
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

from PIL import Image
import re
from collections import Counter

from transformers import pipeline

# Setup logging: logs will be saved in file_management.log
logging.basicConfig(filename='file_management.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
current_user = getpass.getuser()

# --- Authentication Setup ---
AUTH_SECRET = "mysecretkey"  # Secret key for JWT encoding/decoding

# Hardcoded users database
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "user": {"password": "user123", "role": "user"}
}

# Global variables to store authentication token and logged-in username
auth_token = None
logged_in_user = None

def login():
    global auth_token, logged_in_user
    print("=== Login ===")
    username = input("Username: ")
    password = input("Password: ")
    if username in users and users[username]["password"] == password:
        payload = {
            "username": username,
            "role": users[username]["role"],
            "iat": int(time.time())
        }
        auth_token = jwt.encode(payload, AUTH_SECRET, algorithm="HS256")
        logged_in_user = username
        logging.info(f"User {username} logged in successfully.")
        print("Login successful!")
    else:
        logging.error(f"Failed login attempt for user {username}.")
        print("Invalid credentials.")
        login()  # Retry login

def require_admin():
    global auth_token
    try:
        payload = jwt.decode(auth_token, AUTH_SECRET, algorithms=["HS256"])
        if payload.get("role") != "admin":
            print("Permission denied: Only admins can perform this action.")
            logging.warning(f"User {payload.get('username')} attempted admin-only action.")
            return False
        return True
    except Exception as e:
        print("Authentication error:", e)
        logging.error(f"Authentication error: {e}")
        return False




s3 = boto3.client('s3')                           # Initialize S3 client

import os
from cryptography.fernet import Fernet

def load_key(key_file="key.key"):
    if not os.path.exists(key_file):
        key = Fernet.generate_key()
        with open(key_file, "wb") as f:
            f.write(key)
        print(f"Encryption key generated and saved to '{key_file}'")
    else:
        with open(key_file, "rb") as f:
            key = f.read()
        print(f"Encryption key loaded from '{key_file}'")
    return key

# Load or generate the key (only once!)
ENCRYPTION_KEY = load_key()  # For create 'key.key' if it doesn't exist
cipher = Fernet(ENCRYPTION_KEY)

# Function to upload a file to S3
def upload_to_s3(local_file_path, bucket_name, s3_file_name):
    try:
        s3.upload_file(local_file_path, bucket_name, s3_file_name)
        print(f"File '{local_file_path}' uploaded successfully to S3 bucket '{bucket_name}' as '{s3_file_name}'")
    except FileNotFoundError:
        print(f"Error: The file {local_file_path} was not found.")
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please configure your AWS credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")

# File management functions
def list_files(directory):
    files = os.listdir(directory)
    if not files:
        print("No files found in the directory")
    else:  
        for file in files:
            print(file)

def find_closest_file(directory, filename):
    files = os.listdir(directory)
    print(f"Looking for '{filename}' in directory...")
    match = process.extractOne(filename, files)              # Use RapidFuzz to find the closest match
    print(f"Best match: {match}")
    if match:
        return match[0]  
    return None

def rename_file(directory, old_name, new_name):
    closest_match = find_closest_file(directory, old_name)
    if closest_match:
        old_path = os.path.join(directory, closest_match)
        new_path = os.path.join(directory, new_name)
        os.rename(old_path, new_path)
        print(f"File renamed from '{closest_match}' to '{new_name}'")
    else:
        print(f"Error: The file '{old_name}' was not found.")

def delete_path(directory, name):
    closest_match = find_closest_file(directory, name)
    if closest_match:
        path = os.path.join(directory, closest_match)
        if os.path.isfile(path):
            os.remove(path)
            print(f"File '{closest_match}' deleted successfully!")
        elif os.path.isdir(path):
            shutil.rmtree(path)
            print(f"Directory '{closest_match}' deleted successfully!")
    else:
        print(f"Error: No matching file or directory found for '{name}'.")

def create_directory(directory, folder_name):
    path = os.path.join(directory, folder_name)
    os.makedirs(path, exist_ok=True)
    print(f"Directory '{folder_name}' created successfully.")

def upload_file_to_s3(directory):
    file_name = input("Enter the file name you want to upload to S3: ")
    local_file_path = os.path.join(directory, file_name)
    
    if os.path.exists(local_file_path):
        s3_file_name = input("Enter the name you want to assign the file on S3: ")
        bucket_name = input("Enter your S3 bucket name: ")
        upload_to_s3(local_file_path, bucket_name, s3_file_name)
    else:
        print(f"File '{file_name}' not found in the directory.")

# NEW: File search with filters
def search_files(directory, search_term, filter_type="name", fuzzy=False):
    try:
        files = os.listdir(directory)
        if not files:
            print("No files found in the directory")
            return

        matched_files = []
        for file in files:
            file_path = os.path.join(directory, file)

            # Get file properties
            file_name = os.path.basename(file)
            file_extension = file_name.split('.')[-1] if '.' in file_name else ''
            file_size = os.path.getsize(file_path)  # in bytes
            file_modified_time = time.ctime(os.path.getmtime(file_path))

            # Filtering logic based on the filter type
            if filter_type == "name":
                if fuzzy:
                    # Fuzzy search for the file name
                    if fuzz.partial_ratio(search_term.lower(), file_name.lower()) > 80:
                        matched_files.append(file_name)
                else:
                    if search_term.lower() in file_name.lower():
                        matched_files.append(file_name)
            elif filter_type == "type":
                if search_term.lower().lstrip('.') == file_extension.lower():
                    matched_files.append(file_name)

            elif filter_type == "size":
                try:
                    search_size = int(search_term)  # Search by size in bytes
                    if file_size >= search_size:
                        matched_files.append(file_name)
                except ValueError:
                    print("Please enter a valid size.")
            elif filter_type == "date":
                if search_term.lower() in file_modified_time.lower():
                    matched_files.append(file_name)

        if matched_files:
            print(f"Matched files for '{search_term}':")
            for file in matched_files:
                print(file)
        else:
            print(f"No files matched for '{search_term}'.")

    except Exception as e:
        print(f"Error: {e}")

def display_search_options():
    print("\nSearch Files By:")
    print("1. Name")
    print("2. Type (Extension)")
    print("3. Size (in bytes)")
    print("4. Date Modified")
    print("5. Exit")

def file_search_menu(directory):
    while True:
        display_search_options()
        choice = input("Enter your choice: ")

        if choice == "1":
            search_term = input("Enter the file name to search for: ")
            fuzzy = input("Do you want fuzzy search? (y/n): ").lower() == 'y'
            search_files(directory, search_term, filter_type="name", fuzzy=fuzzy)

        elif choice == "2":
            search_term = input("Enter the file type (extension) to search for : ")
            search_files(directory, search_term, filter_type="type")

        elif choice == "3":
            search_term = input("Enter the minimum size (in bytes): ")
            search_files(directory, search_term, filter_type="size")

        elif choice == "4":
            search_term = input("Enter the date to search for: ")
            search_files(directory, search_term, filter_type="date")

        elif choice == "5":
            print("Exiting search menu...")
            break
        else:
            print("Invalid choice. Try again.")


# Function to upload a file to S3
def upload_to_s3(local_file_path, bucket_name, s3_file_name):
    try:
        s3.upload_file(local_file_path, bucket_name, s3_file_name)
        print(f"File '{local_file_path}' uploaded successfully to S3 bucket '{bucket_name}' as '{s3_file_name}'")
    except FileNotFoundError:
        print(f"Error: The file {local_file_path} was not found.")
    except NoCredentialsError:
        print("Error: AWS credentials not found. Please configure your AWS credentials.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Function to compress a file
def compress_file(directory, file_name):
    file_path = os.path.join(directory, file_name)
    zip_file_path = os.path.join(directory, f"{file_name}.zip")

    if os.path.exists(file_path):
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            zipf.write(file_path, arcname=file_name)
        print(f"File '{file_name}' compressed successfully into '{zip_file_path}'")
    else:
        print(f"Error: File '{file_name}' not found!")


#encryption of file

def encrypt_file(directory, file_name):
    file_path = os.path.join(directory, file_name)
    encrypted_file_path = os.path.join(directory, f"{file_name}.enc")
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            file_data = f.read()
        encrypted_data = cipher.encrypt(file_data)
        with open(encrypted_file_path, 'wb') as f:
            f.write(encrypted_data)
        print(f"File '{file_name}' encrypted successfully as '{encrypted_file_path}'")
    else:
        print(f"Error: File '{file_name}' not found!")

        #decryption of file

def decrypt_file(directory, encrypted_file_name):
    key_file = "key.key"
    encrypted_file_path = os.path.join(directory, encrypted_file_name)
    try:
        with open(key_file, "rb") as keyfile:
            key = keyfile.read()
    except FileNotFoundError:
        print("Error: Encryption key file not found!")
        return
    cipher_local = Fernet(key)
    try:
        with open(encrypted_file_path, "rb") as encrypted_file:
            encrypted_data = encrypted_file.read()
        decrypted_data = cipher_local.decrypt(encrypted_data)
        decrypted_file_path = encrypted_file_path.replace(".enc", "")
        with open(decrypted_file_path, "wb") as decrypted_file:
            decrypted_file.write(decrypted_data)
        print(f"File decrypted successfully and saved as: {decrypted_file_path}")
    except FileNotFoundError:
        print(f"Error: Encrypted file '{encrypted_file_name}' not found!")
    except Exception as e:
        print(f"Decryption error: {e}")



# --- AUTOMATIC FILE ORGANIZATION ---
def organize_files(directory):
    """
    Organize files in the given directory into subfolders based on their extension.
    Categories include Documents, Images, Videos, Music, Archives, and Others.
    """
    categories = {
        "Documents": ['pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'ppt', 'pptx', 'odt'],
        "Images": ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'tiff', 'svg'],
        "Videos": ['mp4', 'mkv', 'avi', 'mov', 'wmv', 'flv'],
        "Music": ['mp3', 'wav', 'flac', 'aac', 'ogg'],
        "Archives": ['zip', 'rar', '7z', 'tar', 'gz']
    }
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path):
            ext = file.split('.')[-1].lower() if '.' in file else ""
            moved = False
            for category, ext_list in categories.items():
                if ext in ext_list:
                    target_folder = os.path.join(directory, category)
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    shutil.move(file_path, os.path.join(target_folder, file))
                    print(f"Moved '{file}' to '{target_folder}'")
                    moved = True
                    break
            if not moved:
                target_folder = os.path.join(directory, "Others")
                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)
                shutil.move(file_path, os.path.join(target_folder, file))
                print(f"Moved '{file}' to '{target_folder}'")

def schedule_organization(directory, interval=1):
    """
    Schedule automatic file organization for the given directory every 'interval' minutes.
    """
    schedule.every(interval).minutes.do(organize_files, directory)
    print(f"Scheduled auto-organization every {interval} minute(s) in directory '{directory}'.")
    print("Press Ctrl+C to stop the scheduler.")
    try:
        while True:
            schedule.run_pending()
            t.sleep(1)
    except KeyboardInterrupt:
        print("Auto-organization scheduler stopped.")

        # --- VERSION CONTROL FUNCTIONS ---
def save_version(directory, file_name):
    """
    Save the current version of the specified file.
    The version will be stored in a 'versions' subfolder with a timestamp.
    """
    file_path = os.path.join(directory, file_name)
    if not os.path.exists(file_path):
        print(f"Error: File '{file_name}' not found!")
        return
    versions_dir = os.path.join(directory, "versions")
    if not os.path.exists(versions_dir):
        os.makedirs(versions_dir)
    base, ext = os.path.splitext(file_name)
    timestamp = time.strftime("%Y%m%d%H%M%S")
    versioned_file_name = f"{base}_{timestamp}{ext}"
    versioned_file_path = os.path.join(versions_dir, versioned_file_name)
    shutil.copy2(file_path, versioned_file_path)
    print(f"Version saved as '{versioned_file_name}'.")

def list_versions(directory, file_name):
    """
    List all saved versions of the specified file from the 'versions' folder.
    """
    versions_dir = os.path.join(directory, "versions")
    if not os.path.exists(versions_dir):
        print("No versions found.")
        return []
    base, ext = os.path.splitext(file_name)
    versions = [f for f in os.listdir(versions_dir) if f.startswith(f"{base}_") and f.endswith(ext)]
    if not versions:
        print("No versions found for this file.")
        return []
    versions = sorted(versions)
    print("Available versions:")
    for idx, version in enumerate(versions, start=1):
        print(f"{idx}. {version}")
    return versions

def restore_version(directory, file_name):
    """
    Restore a selected version of the specified file.
    """
    versions = list_versions(directory, file_name)
    if not versions:
        return
    choice = input("Enter the version number to restore (or 'q' to cancel): ")
    if choice.lower() == 'q':
        return
    try:
        idx = int(choice) - 1
        if idx < 0 or idx >= len(versions):
            print("Invalid selection.")
            return
        version_to_restore = versions[idx]
        versions_dir = os.path.join(directory, "versions")
        version_path = os.path.join(versions_dir, version_to_restore)
        target_path = os.path.join(directory, file_name)
        shutil.copy2(version_path, target_path)
        print(f"Restored version '{version_to_restore}' to '{file_name}'.")
    except ValueError:
        print("Invalid input.")

def version_control_menu(directory):
    """
    Version Control submenu that allows saving, listing, and restoring versions.
    """
    while True:
        print("\nVersion Control Menu")
        print("1. Save current version")
        print("2. List versions")
        print("3. Restore a version")
        print("4. Back to main menu")
        choice = input("Enter your choice: ")
        if choice == "1":
            file_name = input("Enter the file name to save a version for: ")
            save_version(directory, file_name)
        elif choice == "2":
            file_name = input("Enter the file name to list versions for: ")
            list_versions(directory, file_name)
        elif choice == "3":
            file_name = input("Enter the file name to restore a version for: ")
            restore_version(directory, file_name)
        elif choice == "4":
            break
        else:
            print("Invalid choice. Try again.")


# --- AI-POWERED FEATURES ---
def suggest_folder_from_text(text):
    """
    Suggest a folder name based on the content of text.
    Uses a simple heuristic: remove common stopwords, count word frequencies, and join the top words.
    """
    stopwords = set(["the", "and", "is", "in", "to", "of", "a", "for", "with", "on", "that", "this", "it", "as", "by", "an"])
    words = re.findall(r'\w+', text.lower())
    words = [word for word in words if word not in stopwords and len(word) > 3]
    if not words:
        return "Uncategorized"
    counter = Counter(words)
    most_common = counter.most_common(3)
    suggested = "_".join([w for w, count in most_common])
    print(f"Suggested folder name: {suggested}")
    return suggested

def ai_assistant_suggest_folder(directory, file_name):
    """
    Analyze the content of an image (using OCR) or a text file to suggest a folder name.
    """
    file_path = os.path.join(directory, file_name)
    ext = file_name.split('.')[-1].lower()
    text = ""
    if ext in ["jpg", "jpeg", "png", "tiff", "bmp", "gif"]:
        try:
            text = pytesseract.image_to_string(Image.open(file_path))
        except Exception as e:
            print(f"Error during OCR: {e}")
            return None
    elif ext in ["txt"]:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()
        except Exception as e:
            print(f"Error reading text file: {e}")
            return None
    else:
        print("Unsupported file type for AI categorization. Only images and text files are supported.")
        return None
    if text:
        print("Extracted text:")
        print(text)
        return suggest_folder_from_text(text)
    else:
        print("No text could be extracted.")
        return None

def ai_powered_features_menu(directory):
    """
    AI-Powered Features submenu that provides:
      1. OCR: Extract text from an image.
      2. Folder suggestion: Analyze file content to suggest a folder name.
      3. Back to main menu.
    """
    while True:
        print("\nAI-Powered Features Menu")
        print("1. Extract text from image (OCR)")
        print("2. Suggest folder name based on file contents")
        print("3. Back to main menu")
        choice = input("Enter your choice: ")
        if choice == "1":
            file_name = input("Enter image file name: ")
            file_path = os.path.join(directory, file_name)
            try:
                text = pytesseract.image_to_string(Image.open(file_path))
                print("Extracted Text:")
                print(text)
            except Exception as e:
                print(f"Error during OCR: {e}")
        elif choice == "2":
            file_name = input("Enter file name (image or text) for categorization: ")
            suggestion = ai_assistant_suggest_folder(directory, file_name)
            if suggestion:
                print(f"Suggested folder name: {suggestion}")
        elif choice == "3":
            break
        else:
            print("Invalid choice. Try again.")



def summarize_text_file(directory):
    file_name = input("Enter the text file name to summarize: ")
    file_path = os.path.join(directory, file_name)

    if not os.path.exists(file_path):
        print(f"Error: File '{file_name}' not found!")
        return

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            text = file.read()

        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        summary = summarizer(text, max_length=150, min_length=50, do_sample=False)

        print("\n=== AI-Generated Summary ===")
        print(summary[0]["summary_text"])

    except Exception as e:
        print(f"Error in summarization: {e}")


def logout():
    global auth_token, logged_in_user
    logging.info(f"User {logged_in_user} logged out.")
    auth_token = None
    logged_in_user = None
    print("Logged out successfully.")


# --- MAIN MENU ---
def main():
    login()  # Call login() at the very start
    while True:
        print("\nFile Management System")
        print("1. List Files")
        print("2. Rename File")
        print("3. Delete File/Directory")
        print("4. Create Directory")
        print("5. Upload File to S3")
        print("6. Search Files")
        print("7. Compress File")
        print("8. Encrypt File")
        print("9. Decrypt File")
        print("10. Organize Files Automatically")
        print("11. Schedule Auto-Organization")
        print("12. Version Control")
        print("13. AI-Powered Features")
        print("14. Summarize a Text File")
        print("15. Logout")
        print("16. Exit")

        choice = input("Enter your choice: ")
        if choice == "1":
            directory = input("Enter directory path: ")
            list_files(directory)
        elif choice == "2":
            directory = input("Enter directory path: ")
            old_name = input("Enter old file name: ")
            new_name = input("Enter new file name: ")
            rename_file(directory, old_name, new_name)
        elif choice == "3":
            directory = input("Enter directory path: ")
            name = input("Enter file or directory name to delete: ")
            delete_path(directory, name)
        elif choice == "4":
            directory = input("Enter directory path: ")
            folder_name = input("Enter new folder name: ")
            create_directory(directory, folder_name)
        elif choice == "5":
            directory = input("Enter directory path: ")
            upload_file_to_s3(directory)
        elif choice == "6":
            directory = input("Enter directory path: ")
            file_search_menu(directory)
        elif choice == "7":
            directory = input("Enter directory path: ")
            file_name = input("Enter the file name to compress: ")
            compress_file(directory, file_name)
        elif choice == "8":
            directory = input("Enter directory path: ")
            file_name = input("Enter the file name to encrypt: ")
            encrypt_file(directory, file_name)
        elif choice == "9":
            directory = input("Enter directory path: ")
            encrypted_file_name = input("Enter the encrypted file name to decrypt: ")
            decrypt_file(directory, encrypted_file_name)
        elif choice == "10":
            directory = input("Enter directory path for organization: ")
            organize_files(directory)
        elif choice == "11":
            directory = input("Enter directory path for scheduled organization: ")
            interval = input("Enter interval in minutes for auto-organization: ")
            try:
                interval = int(interval)
            except ValueError:
                print("Invalid interval, using default of 1 minute.")
                interval = 1
            schedule_organization(directory, interval)
        elif choice == "12":
            directory = input("Enter directory path for version control: ")
            version_control_menu(directory)
        elif choice == "13":
            directory = input("Enter directory path for AI-powered features: ")
            ai_powered_features_menu(directory)
        elif choice == "14":
            directory = input("Enter directory path: ")
            summarize_text_file(directory)
        elif choice == "15":
            logout()
            login() # Prompt for login after logging out
        elif choice == "16":
            logging.info(f"User {logged_in_user} exited the program.")
            print("Exiting... Goodbye!")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    main()

