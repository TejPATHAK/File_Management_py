import os
import shutil
import boto3
from botocore.exceptions import NoCredentialsError
from rapidfuzz import process  # Import RapidFuzz for fuzzy matching

# Initialize S3 client
s3 = boto3.client('s3')

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
    # Use RapidFuzz to find the closest match
    match = process.extractOne(filename, files)
    print(f"Best match: {match}")
    if match:
        return match[0]  # Return the best match
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

# Main menu
def main():
    print("\nFile Management System")
    print("1. List Files")
    print("2. Rename File")
    print("3. Delete File/Directory")
    print("4. Create Directory")
    print("5. Upload File to S3")
    print("6. Exit")

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
        print("Exiting... Goodbye!")
        exit()

if __name__ == "__main__":
    main()
