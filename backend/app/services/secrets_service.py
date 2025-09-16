# app/services/secrets_service.py
import os
from typing import Optional
from google.cloud import secretmanager
from google.oauth2 import service_account
import json

class SecretsService:
    """Service for managing secrets using Google Cloud Secret Manager"""
    
    def __init__(self):
        self.project_id = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Secret Manager client"""
        try:
            # Option 1: Use service account key file
            service_account_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            if service_account_path and os.path.exists(service_account_path):
                credentials = service_account.Credentials.from_service_account_file(
                    service_account_path
                )
                self.client = secretmanager.SecretManagerServiceClient(credentials=credentials)
            
            # Option 2: Use default credentials (for GCP environments)
            elif os.getenv("GOOGLE_APPLICATION_CREDENTIALS") or os.getenv("GOOGLE_CLOUD_PROJECT"):
                self.client = secretmanager.SecretManagerServiceClient()
            
            else:
                print("⚠️ Google Cloud credentials not found. Falling back to environment variables.")
                self.client = None
                
        except Exception as e:
            print(f"⚠️ Failed to initialize Secret Manager client: {e}")
            self.client = None
    
    def get_secret(self, secret_name: str, version: str = "latest") -> Optional[str]:
        """Retrieve a secret from Google Secret Manager"""
        if not self.client or not self.project_id:
            return None
            
        try:
            # Build the resource name
            name = f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
            
            # Access the secret
            response = self.client.access_secret_version(request={"name": name})
            
            # Return the secret value
            return response.payload.data.decode("UTF-8")
            
        except Exception as e:
            print(f"⚠️ Failed to retrieve secret {secret_name}: {e}")
            return None
    
    def create_secret(self, secret_name: str, secret_value: str) -> bool:
        """Create a new secret in Google Secret Manager"""
        if not self.client or not self.project_id:
            return False
            
        try:
            # Create the secret
            parent = f"projects/{self.project_id}"
            secret = {"replication": {"automatic": {}}}
            
            response = self.client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": secret_name,
                    "secret": secret,
                }
            )
            
            # Add the secret version
            version = self.client.add_secret_version(
                request={
                    "parent": response.name,
                    "payload": {"data": secret_value.encode("UTF-8")},
                }
            )
            
            print(f"✅ Created secret {secret_name}")
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to create secret {secret_name}: {e}")
            return False
    
    def update_secret(self, secret_name: str, secret_value: str) -> bool:
        """Update an existing secret in Google Secret Manager"""
        if not self.client or not self.project_id:
            return False
            
        try:
            # Add a new version to the existing secret
            parent = f"projects/{self.project_id}/secrets/{secret_name}"
            
            version = self.client.add_secret_version(
                request={
                    "parent": parent,
                    "payload": {"data": secret_value.encode("UTF-8")},
                }
            )
            
            print(f"✅ Updated secret {secret_name}")
            return True
            
        except Exception as e:
            print(f"⚠️ Failed to update secret {secret_name}: {e}")
            return False

# Singleton instance
secrets_service = SecretsService()
