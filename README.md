# File Management System (CLI)

## 📌 Overview
The **File Management System (CLI)** is a Python-based command-line tool designed to efficiently manage files with advanced features like **AI-powered categorization, encryption, cloud storage integration, automatic organization, and version control**. This tool simplifies file operations and enhances security and accessibility.

## 🚀 Features
✅ **Comprehensive File Operations** – List, rename, delete, and organize files easily.  
✅ **AI-Powered File Categorization** – Uses **OCR (Tesseract) & NLP** for intelligent sorting.  
✅ **Cloud Storage Integration** – Direct upload & retrieval from **AWS S3**.  
✅ **Smart Search & Fuzzy Matching** – Find files using **RapidFuzz** with filters by name, size, type, and date.  
✅ **Encryption & Decryption** – Secure files using **AES encryption**.  
✅ **Automatic File Organization** – Schedule auto-sorting into categories.  
✅ **Version Control** – Save, track, and restore file versions.  
✅ **User Authentication & Logging** – Track activity & ensure security with **JWT authentication**.  

## 🛠️ Technologies Used
- **Python**  
- **Boto3 (AWS SDK)** – For cloud storage.  
- **JWT Authentication** – User access control.  
- **Cryptography (AES Encryption)** – File security.  
- **OCR (Tesseract)** – Text extraction from images.  
- **NLP & Regex** – AI-driven file categorization.  
- **RapidFuzz (Fuzzy Matching)** – Intelligent search.  
- **Logging & Schedule** – For tracking and automation.  

## 📂 Installation & Setup
### Prerequisites:
- Python 3.x installed
- AWS credentials configured for S3 storage
- Required Python libraries installed

### 🔹 Install Dependencies
```bash
pip install boto3 jwt cryptography pytesseract rapidfuzz schedule
```

### 🔹 Run the Application
```bash
python file_management.py
```

## 🎯 How to Use
1️⃣ **Login** – Enter your username and password.  
2️⃣ **Perform File Operations** – Choose from listing, renaming, deleting, or organizing files.  
3️⃣ **Cloud Upload** – Upload files directly to AWS S3.  
4️⃣ **Encryption & Security** – Encrypt/decrypt files for enhanced security.  
5️⃣ **AI Categorization** – Let AI suggest folders based on content.  
6️⃣ **Version Control** – Save and restore previous file versions.  
7️⃣ **Exit & Logout** – Securely exit when done.  

## 🔗 Future Enhancements
🚀 **GUI Version (Tkinter/PyQt/Kivy)** for a user-friendly interface.  
🚀 **Web-Based Version (Flask/Django)** for remote access.  
🚀 **Deep Learning Integration** for improved AI-based file categorization.  

📌 **Stay tuned for more updates!** 🔥  

## 📌 Author
Developed by **[Your Name]**  
🔗 GitHub Repository: [Your GitHub Link]  

## 📝 License
This project is licensed under the **MIT License**.
