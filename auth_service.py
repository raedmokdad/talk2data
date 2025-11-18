"""
AWS Cognito Authentication Service
Handles user signup, login, password reset, and verification
"""

import boto3
import os
import hmac
import hashlib
import base64
from botocore.exceptions import ClientError
from dotenv import load_dotenv

load_dotenv()

# Cognito Configuration
COGNITO_REGION = os.getenv('COGNITO_REGION', 'us-east-1')
USER_POOL_ID = os.getenv('COGNITO_USER_POOL_ID', 'us-east-1_1WET5qWMS')
APP_CLIENT_ID = os.getenv('COGNITO_APP_CLIENT_ID', '6dst32npudvcr207ufsacfavui')
APP_CLIENT_SECRET = os.getenv('COGNITO_APP_CLIENT_SECRET', None)

# Initialize Cognito Client
cognito_client = boto3.client('cognito-idp', region_name=COGNITO_REGION)


def get_secret_hash(username: str) -> str:
    """
    Calculate SECRET_HASH for Cognito app client with secret
    Required when app client has a client secret configured
    """
    if not APP_CLIENT_SECRET:
        return None
    
    message = bytes(username + APP_CLIENT_ID, 'utf-8')
    secret = bytes(APP_CLIENT_SECRET, 'utf-8')
    dig = hmac.new(secret, message, hashlib.sha256).digest()
    return base64.b64encode(dig).decode()


def signup_user(username: str, password: str, email: str) -> tuple[bool, str]:
    """
    Register a new user
    
    Args:
        username: Unique username
        password: User password (must meet policy requirements)
        email: User email for verification
    
    Returns:
        (success, message)
    """
    try:
        params = {
            'ClientId': APP_CLIENT_ID,
            'Username': username,
            'Password': password,
            'UserAttributes': [
                {'Name': 'email', 'Value': email}
            ]
        }
        
        # Add SECRET_HASH if client secret is configured
        secret_hash = get_secret_hash(username)
        if secret_hash:
            params['SecretHash'] = secret_hash
        
        response = cognito_client.sign_up(**params)
        return True, "Registration successful! Check your email for verification code."
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'UsernameExistsException':
            return False, "Username already exists. Please choose a different username."
        elif error_code == 'InvalidPasswordException':
            return False, "Password does not meet requirements. Use at least 8 characters with uppercase, lowercase, and numbers."
        elif error_code == 'InvalidParameterException':
            return False, f"Invalid input: {error_message}"
        else:
            return False, f"Registration failed: {error_message}"


def confirm_signup(username: str, confirmation_code: str) -> tuple[bool, str]:
    """
    Confirm user registration with email verification code
    
    Args:
        username: Username to confirm
        confirmation_code: Code sent to user's email
    
    Returns:
        (success, message)
    """
    try:
        params = {
            'ClientId': APP_CLIENT_ID,
            'Username': username,
            'ConfirmationCode': confirmation_code
        }
        
        secret_hash = get_secret_hash(username)
        if secret_hash:
            params['SecretHash'] = secret_hash
        
        cognito_client.confirm_sign_up(**params)
        return True, "Account verified successfully! You can now login."
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'CodeMismatchException':
            return False, "Invalid verification code. Please try again."
        elif error_code == 'ExpiredCodeException':
            return False, "Verification code expired. Please request a new code."
        else:
            return False, f"Verification failed: {error_message}"


def resend_confirmation_code(username: str) -> tuple[bool, str]:
    """
    Resend verification code to user's email
    
    Args:
        username: Username to resend code for
    
    Returns:
        (success, message)
    """
    try:
        params = {
            'ClientId': APP_CLIENT_ID,
            'Username': username
        }
        
        secret_hash = get_secret_hash(username)
        if secret_hash:
            params['SecretHash'] = secret_hash
        
        cognito_client.resend_confirmation_code(**params)
        return True, "Verification code resent to your email."
    except ClientError as e:
        return False, f"Failed to resend code: {e.response['Error']['Message']}"


def login_user(username: str, password: str) -> tuple[bool, dict | str]:
    """
    Authenticate user and get tokens
    
    Args:
        username: Username
        password: User password
    
    Returns:
        (success, tokens_dict or error_message)
    """
    try:
        auth_params = {
            'USERNAME': username,
            'PASSWORD': password
        }
        
        secret_hash = get_secret_hash(username)
        if secret_hash:
            auth_params['SECRET_HASH'] = secret_hash
        
        response = cognito_client.initiate_auth(
            ClientId=APP_CLIENT_ID,
            AuthFlow='USER_PASSWORD_AUTH',
            AuthParameters=auth_params
        )
        
        # Return authentication tokens
        auth_result = response['AuthenticationResult']
        return True, {
            'access_token': auth_result['AccessToken'],
            'id_token': auth_result['IdToken'],
            'refresh_token': auth_result['RefreshToken'],
            'username': username
        }
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        
        if error_code == 'NotAuthorizedException':
            return False, "Incorrect username or password."
        elif error_code == 'UserNotConfirmedException':
            return False, "Account not verified. Please check your email for verification code."
        else:
            return False, f"Login failed: {error_message}"


def change_password(access_token: str, old_password: str, new_password: str) -> tuple[bool, str]:
    """
    Change user password
    
    Args:
        access_token: User's access token from login
        old_password: Current password
        new_password: New password
    
    Returns:
        (success, message)
    """
    try:
        cognito_client.change_password(
            AccessToken=access_token,
            PreviousPassword=old_password,
            ProposedPassword=new_password
        )
        return True, "Password changed successfully!"
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == 'NotAuthorizedException':
            return False, "Current password is incorrect."
        elif error_code == 'InvalidPasswordException':
            return False, "New password does not meet requirements."
        else:
            return False, f"Password change failed: {e.response['Error']['Message']}"


def forgot_password(username: str) -> tuple[bool, str]:
    """
    Initiate password reset flow
    
    Args:
        username: Username to reset password for
    
    Returns:
        (success, message)
    """
    try:
        params = {
            'ClientId': APP_CLIENT_ID,
            'Username': username
        }
        
        secret_hash = get_secret_hash(username)
        if secret_hash:
            params['SecretHash'] = secret_hash
        
        cognito_client.forgot_password(**params)
        return True, "Password reset code sent to your email."
    except ClientError as e:
        return False, f"Failed to send reset code: {e.response['Error']['Message']}"


def confirm_forgot_password(username: str, confirmation_code: str, new_password: str) -> tuple[bool, str]:
    """
    Complete password reset with confirmation code
    
    Args:
        username: Username
        confirmation_code: Code sent to user's email
        new_password: New password
    
    Returns:
        (success, message)
    """
    try:
        params = {
            'ClientId': APP_CLIENT_ID,
            'Username': username,
            'ConfirmationCode': confirmation_code,
            'Password': new_password
        }
        
        secret_hash = get_secret_hash(username)
        if secret_hash:
            params['SecretHash'] = secret_hash
        
        cognito_client.confirm_forgot_password(**params)
        return True, "Password reset successful! You can now login."
    except ClientError as e:
        error_code = e.response['Error']['Code']
        
        if error_code == 'CodeMismatchException':
            return False, "Invalid reset code. Please try again."
        elif error_code == 'ExpiredCodeException':
            return False, "Reset code expired. Please request a new one."
        elif error_code == 'InvalidPasswordException':
            return False, "Password does not meet requirements."
        else:
            return False, f"Password reset failed: {e.response['Error']['Message']}"


def logout_user(access_token: str) -> tuple[bool, str]:
    """
    Sign out user globally (invalidate tokens)
    
    Args:
        access_token: User's access token
    
    Returns:
        (success, message)
    """
    try:
        cognito_client.global_sign_out(
            AccessToken=access_token
        )
        return True, "Logged out successfully."
    except ClientError as e:
        return False, f"Logout failed: {e.response['Error']['Message']}"


def get_user_info(access_token: str) -> tuple[bool, dict | str]:
    """
    Get authenticated user's information
    
    Args:
        access_token: User's access token
    
    Returns:
        (success, user_info_dict or error_message)
    """
    try:
        response = cognito_client.get_user(
            AccessToken=access_token
        )
        
        # Parse user attributes
        user_info = {
            'username': response['Username'],
            'email': None
        }
        
        for attr in response['UserAttributes']:
            if attr['Name'] == 'email':
                user_info['email'] = attr['Value']
        
        return True, user_info
    except ClientError as e:
        return False, f"Failed to get user info: {e.response['Error']['Message']}"
