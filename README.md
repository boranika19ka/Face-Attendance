# 🛡️ Professional Face Recognition Attendance System

A high-performance, biometric attendance system built with Python, OpenCV, and Streamlit. This system features a modern dark-themed UI, real-time face recognition, and a comprehensive administrative management dashboard.

## 🌟 Key Features

### 📸 Smart Recognition
- **Real-time Detection**: Automatic face detection using Haar Cascades.
- **Biometric Logging**: Instant attendance logging with "On Time" or "Late" status.
- **Video Overlays**: Interactive boxes and name labels on live camera feed.

### 👤 Student Registration
- **Dual Capture Mode**: Register students via live webcam or by uploading existing photos.
- **Auto-Training**: The system automatically retrains the AI model when a new student is added or removed.

### 🔐 Administrative Dashboard
- **Secure Management**: Password-protected access to system controls.
- **CRUD Operations**: Edit student details or delete records entirely.
- **Attendance Insights**: Visual charts showing daily attendance trends.
- **Warning List**: Automatic identification of students with poor attendance records.

### 🎨 Personalization
- **Theme Switching**: Seamlessly toggle between **Dark Mode** and **Light Mode**.
- **Responsive UI**: Optimized layout using Streamlit's modern design components.

## 🛠️ Technology Stack
- **Backend**: Python 3.12, SQLite3
- **Computer Vision**: OpenCV (LBPH Face Recognizer)
- **Frontend**: Streamlit
- **Data Handling**: Pandas, Numpy

## 🚀 Quick Start

### 1. Installation
Ensure you are in the project directory and run:
```powershell
pip install -r requirements.txt
```

### 2. Run the Application
```powershell
python -m streamlit run app.py
```

### 3. Admin Access
- **Default Username**: `admin`
- **Default Password**: `admin123`

## 📁 Project Structure
- `app.py`: Main application interface and routing.
- `database.py`: SQLite database handler and analytics queries.
- `face_utils.py`: OpenCV face detection and recognition logic.
- `styles.py`: Dynamic CSS theme system.
- `faces/`: Directory containing student photos.
- `data/`: Directory for the database and trained AI models.

---
*Created for Midterm Project - 2026*
