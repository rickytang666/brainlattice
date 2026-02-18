import firebase_admin
from firebase_admin import credentials, firestore
from typing import Dict, Any, Optional
import os
import json

def init_firebase():
    """init firebase admin sdk"""
    if not firebase_admin._apps:
        # get creds from env or file
        firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS_JSON")
        
        if firebase_creds_json:
            cred_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(cred_dict)
        else:
            # fallback to relative path
            service_account_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH", "secrets/firebase_private.json")
            
            if not os.path.isabs(service_account_path):
                # make relative to project root (assuming backend/ is root or cwd)
                pass 
                
            if not os.path.exists(service_account_path):
                raise Exception(f"firebase creds not found at {service_account_path}")
            
            cred = credentials.Certificate(service_account_path)
        
        firebase_admin.initialize_app(cred)
    
    return firestore.client()

def save_project_data(project_id: str, reference_data: Dict[str, Any], graph_data: Dict[str, Any]):
    """save project to firestore"""
    try:
        db = init_firebase()
        metadata = graph_data.get('graph_metadata', {})
        
        db.collection('projects').document(project_id).set({
            'title': metadata.get('title', 'untitled project'),
            'subject': metadata.get('subject', 'unknown'),
            'total_concepts': metadata.get('total_concepts', 0),
            'depth_levels': metadata.get('depth_levels', 0),
            'digest_data': reference_data,
            'graph_data': graph_data,
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        })
        return True
    except Exception as e:
        raise Exception(f"failed to save project: {str(e)}")

def get_project_data(project_id: str) -> Optional[Dict[str, Any]]:
    """get project from firestore"""
    try:
        db = init_firebase()
        doc = db.collection('projects').document(project_id).get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        raise Exception(f"failed to get project: {str(e)}")

def list_projects() -> list:
    """list all projects"""
    try:
        db = init_firebase()
        projects = db.collection('projects').stream()
        return [{"id": doc.id, **doc.to_dict()} for doc in projects]
    except Exception as e:
        raise Exception(f"failed to list projects: {str(e)}")

def update_project_title(project_id: str, new_title: str) -> bool:
    """update project title"""
    try:
        db = init_firebase()
        doc_ref = db.collection('projects').document(project_id)
        if doc_ref.get().exists:
            doc_ref.update({
                'title': new_title,
                'updated_at': firestore.SERVER_TIMESTAMP
            })
            return True
        return False
    except Exception as e:
        raise Exception(f"failed to update title: {str(e)}")

def delete_project_data(project_id: str) -> bool:
    """delete project"""
    try:
        db = init_firebase()
        doc_ref = db.collection('projects').document(project_id)
        if doc_ref.get().exists:
            doc_ref.delete()
            return True
        return False
    except Exception as e:
        raise Exception(f"failed to delete project: {str(e)}")
