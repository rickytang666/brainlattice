import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, Any, Optional
import os

# Initialize Firebase
def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        # Use service account JSON file
        service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "secrets/firebase_private.json")
        cred = credentials.Certificate(service_account_path)
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

def save_project_data(project_id: str, reference_data: Dict[str, Any], graph_data: Dict[str, Any]):
    """
    Save project data to Firebase Firestore
    """
    try:
        db = init_firebase()
        
        # Save reference data (detailed AI analysis)
        db.collection('projects').document(project_id).set({
            'reference': reference_data,
            'graph': graph_data,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        
        return True
    
    except Exception as e:
        raise Exception(f"Failed to save project data: {str(e)}")

def get_project_data(project_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieve project data from Firebase Firestore
    """
    try:
        db = init_firebase()
        doc = db.collection('projects').document(project_id).get()
        
        if doc.exists:
            return doc.to_dict()
        return None
    
    except Exception as e:
        raise Exception(f"Failed to get project data: {str(e)}")

def list_projects() -> list:
    """
    List all projects
    """
    try:
        db = init_firebase()
        projects = db.collection('projects').stream()
        
        return [{"id": doc.id, **doc.to_dict()} for doc in projects]
    
    except Exception as e:
        raise Exception(f"Failed to list projects: {str(e)}")
