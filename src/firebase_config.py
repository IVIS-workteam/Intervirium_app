import firebase_admin
from firebase_admin import credentials, firestore, auth as admin_auth
import json
from google.cloud import storage
from google.oauth2 import service_account
import os
from kivy.utils import platform

# Путь к файлу сервисного аккаунта
if platform == 'android':
    from android.storage import primary_external_storage_path
    service_account_path = os.path.join(primary_external_storage_path(), 'kivy', 'intervirium', 'interviriumapp-d155b-firebase-adminsdk-fbsvc-f0721e098a.json')
else:
    service_account_path = 'interviriumapp-d155b-firebase-adminsdk-fbsvc-f0721e098a.json'

try:
    # Загрузка данных сервисного аккаунта из JSON файла
    with open(service_account_path, 'r') as f:
        service_account_info = json.load(f)
        
    cred = credentials.Certificate(service_account_info)
    
    # Initialize Firebase Admin
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    
    # Initialize Storage
    storage_client = storage.Client.from_service_account_info(service_account_info)
    
    # Helper functions for authentication
    def sign_in_anonymous():
        try:
            # Create an anonymous user
            user = admin_auth.create_user()
            return {'localId': user.uid}
        except Exception as e:
            print(f"Error creating anonymous user: {e}")
            return None
    
    # Initialize anonymous auth by default
    current_user = sign_in_anonymous()
    
except Exception as e:
    print(f"Error initializing Firebase: {e}")
    db = None
    storage_client = None
    current_user = None 