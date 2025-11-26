from pathlib import Path
import os, json, datetime
import boto3
from dotenv import load_dotenv, dotenv_values
from typing import Dict, Any, List, Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Force reload .env - override=True forces fresh load
load_dotenv(override=True)

S3_BUCKET = os.getenv("S3_BUCKET")   
AWS_REGION = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

_s3_client = None


security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Extract username from AWS Cognito JWT token"""
    try:
        token = credentials.credentials
        payload = jwt.decode(token, options={"verify_signature": False})
        username = payload.get("cognito:username") or payload.get("username")
        if not username:
            raise HTTPException(status_code=401, detail="Username not found in token")
        
        # if username is an email
        if '@' in username:
            username = username.split('@')[0]
        # For S3 : no points only lowercase
        username = username.lower().replace('.', '_')
        
        return username
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
        
   
def get_s3_client():
    global _s3_client
    # Always create a fresh client to ensure new credentials are used
    access_key = os.getenv("AWS_ACCESS_KEY_ID")
    secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    
    _s3_client = boto3.client(
        "s3",
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=AWS_REGION
    ) 
    return _s3_client 
        


def upload_user_schema(username: str, schema_name: str, schema_data: Dict[str, Any]) -> tuple[bool, str]:
    try:
        key = f"schemas/{username}/{schema_name}.json"
        client = get_s3_client()
        client.put_object(
            Body = json.dumps(schema_data),
            Bucket=S3_BUCKET,    
            Key=key,
            ContentType="application/json"
         )
        return True, f"{schema_name} uploaded"
    except Exception as e:
        return False, f"Upload Failed: {str(e)}"


def list_user_schema(username: str) -> tuple[bool, List[str]]:
    try:
        client = get_s3_client()
        response = client.list_objects_v2(
            Bucket=S3_BUCKET,
            Prefix=f"schemas/{username}/"
        )
        
        files = []
        if 'Contents' in response:
            files = [ obj['Key'].split('/')[-1].replace('.json','')  for obj in response['Contents']]
        return True, files
    except Exception as e:
        return False, []

def get_user_schema(username: str, schema_name: str) -> tuple[bool, Dict[str, Any]]:
    try:
        files = []
        client = get_s3_client()
        response = client.get_object(
            Bucket=S3_BUCKET,
            Key=f"schemas/{username}/{schema_name}.json"
        )

        content = response['Body'].read().decode('utf-8') 
        schema_data = json.loads(content)
        return True, schema_data
    except Exception as e:
        return False, {}

def delete_user_schema(username: str, schema_name: str) -> tuple[bool, str]:
    try:
        client = get_s3_client()
        key = f"schemas/{username}/{schema_name}.json"
        try:
            client.head_object(Bucket=S3_BUCKET, Key=key)
        except Exception as e:
            return False, f"Schema '{schema_name}' not found or error"
            
            
        client.delete_object(Bucket=S3_BUCKET, Key=key)  
        return True, f"Schema '{schema_name}' deleted successfully"
    except Exception as e:
        return False, f"Error {str(e)}"
    