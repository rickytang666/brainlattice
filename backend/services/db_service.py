import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, Any, Optional
import os
import json

# Initialize Firebase
def init_firebase():
    """Initialize Firebase Admin SDK"""
    if not firebase_admin._apps:
        # Try to get credentials from environment variable (JSON string)
        firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        
        if firebase_creds_json:
            # Use credentials from environment variable
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
        else:
            # Fall back to file path
            service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "secrets/firebase_private.json")
            
            if not os.path.exists(service_account_path):
                raise Exception(f"Firebase credentials not found. Set FIREBASE_CREDENTIALS_JSON environment variable or provide file at {service_account_path}.")
            
            cred = credentials.Certificate(service_account_path)
        
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

def save_project_data(project_id: str, reference_data: Dict[str, Any], graph_data: Dict[str, Any]):
    """
    Save project data to Firebase Firestore
    """
    try:
        db = init_firebase()
        
        # Extract metadata from graph_data
        metadata = graph_data.get('graph_metadata', {})
        
        # Save project with metadata
        db.collection('projects').document(project_id).set({
            'title': metadata.get('title', 'Untitled Project'),
            'subject': metadata.get('subject', 'Unknown'),
            'total_concepts': metadata.get('total_concepts', 0),
            'depth_levels': metadata.get('depth_levels', 0),
            'digest_data': reference_data,
            'graph_data': graph_data,
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

def update_project_title(project_id: str, new_title: str) -> bool:
    """
    Update project title in Firebase Firestore
    """
    try:
        db = init_firebase()
        doc_ref = db.collection('projects').document(project_id)
        
        # Check if document exists
        if doc_ref.get().exists:
            doc_ref.update({
                'title': new_title,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            return True
        return False
    
    except Exception as e:
        raise Exception(f"Failed to update project title: {str(e)}")

def delete_project_data(project_id: str) -> bool:
    """
    Delete project from Firebase Firestore
    """
    try:
        db = init_firebase()
        doc_ref = db.collection('projects').document(project_id)
        
        # Check if document exists
        if doc_ref.get().exists:
            doc_ref.delete()
            return True
        return False
    
    except Exception as e:
        raise Exception(f"Failed to delete project: {str(e)}")
