import cv2
import os
import numpy as np
from PIL import Image

# Path for face detection cascade
CASCADE_PATH = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
TRAINER_PATH = "data/trainer.yml"
FACES_DIR = "faces"

def get_recognizer():
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    if os.path.exists(TRAINER_PATH):
        recognizer.read(TRAINER_PATH)
    return recognizer

def train_recognizer():
    """Train the recognizer on all images in faces/ directory"""
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    detector = cv2.CascadeClassifier(CASCADE_PATH)
    
    face_samples = []
    ids = []
    
    # We'll use the student_id from filename (e.g., S101.jpg)
    # But LBPH needs integer IDs. We'll map them.
    id_map = {}
    current_int_id = 0
    
    if not os.path.exists(FACES_DIR):
        return False
        
    image_paths = [os.path.join(FACES_DIR, f) for f in os.listdir(FACES_DIR) if f.endswith('.jpg')]
    
    if not image_paths:
        return False
        
    for image_path in image_paths:
        student_id_str = os.path.split(image_path)[-1].split(".")[0]
        
        # Map string ID to int
        if student_id_str not in id_map:
            id_map[student_id_str] = current_int_id
            current_int_id += 1
        
        pil_img = Image.open(image_path).convert('L') # convert to grayscale
        img_numpy = np.array(pil_img, 'uint8')
        
        faces = detector.detectMultiScale(img_numpy)
        
        for (x, y, w, h) in faces:
            face_samples.append(img_numpy[y:y+h, x:x+w])
            ids.append(id_map[student_id_str])
            
    if face_samples:
        recognizer.train(face_samples, np.array(ids))
        
        # Ensure data directory exists
        os.makedirs(os.path.dirname(TRAINER_PATH), exist_ok=True)
        
        recognizer.save(TRAINER_PATH)
        # Save map for reverse lookup
        import json
        with open("data/id_map.json", "w") as f:
            json.dump(id_map, f)
        return True
    return False

def register_face(student_id, image_path):
    """Simply trigger a re-train after a new image is saved"""
    return train_recognizer()

def load_encodings():
    """Keep function name for compatibility with app.py"""
    if os.path.exists(TRAINER_PATH) and os.path.exists("data/id_map.json"):
        import json
        with open("data/id_map.json", "r") as f:
            return json.load(f)
    return {}

def recognize_face(frame, known_id_map):
    """Recognize faces in a live frame using LBPH"""
    if not known_id_map:
        return []
        
    recognizer = get_recognizer()
    detector = cv2.CascadeClassifier(CASCADE_PATH)
    
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector.detectMultiScale(gray, 1.2, 5)
    
    # Reverse the map for lookup
    rev_map = {v: k for k, v in known_id_map.items()}
    
    results = []
    for (x, y, w, h) in faces:
        id_int, confidence = recognizer.predict(gray[y:y+h, x:x+w])
        
        # Confidence: 0 is perfect match, > 100 is likely wrong
        if confidence < 70: # Adjust threshold as needed
            student_id = rev_map.get(id_int, "Unknown")
        else:
            student_id = "Unknown"
            
        results.append({
            "id": student_id,
            "location": (y, x+w, y+h, x) # (top, right, bottom, left) for compatibility
        })
        
    return results

def delete_student_face(student_id):
    """Delete student image and retrain model"""
    img_path = os.path.join(FACES_DIR, f"{student_id}.jpg")
    if os.path.exists(img_path):
        os.remove(img_path)
    
    # Retrain to update trainer.yml and id_map.json
    return train_recognizer()
