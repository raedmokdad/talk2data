"""
Talk2Data Streamlit App with AWS Cognito Authentication
Complete UI with Login, Signup, Password Reset, and SQL Generation
"""

import streamlit as st
import requests
from auth_service import (
    signup_user, confirm_signup, resend_confirmation_code,
    login_user, logout_user, forgot_password, confirm_forgot_password,
    change_password, get_user_info
)

# Page Configuration
st.set_page_config(
    page_title="Talk2Data - AI SQL Generator",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
API_URL = "https://talk2data-production.up.railway.app"

# ============================================
# Session State Initialization
# ============================================
def init_session_state():
    """Initialize session state variables"""
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'user_tokens' not in st.session_state:
        st.session_state.user_tokens = None
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'user_email' not in st.session_state:
        st.session_state.user_email = None
    if 'pending_verification' not in st.session_state:
        st.session_state.pending_verification = None

init_session_state()


# ============================================
# Authentication Pages
# ============================================
def show_login_page():
    """Login page"""
    st.title("🔐 Talk2Data Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Welcome Back!")
        
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("🚀 Login", use_container_width=True):
                if username and password:
                    with st.spinner("Logging in..."):
                        success, result = login_user(username, password)
                        
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user_tokens = result
                            st.session_state.username = result['username']
                            
                            # Get user info
                            info_success, user_info = get_user_info(result['access_token'])
                            if info_success:
                                st.session_state.user_email = user_info.get('email')
                            
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
                else:
                    st.warning("Please enter username and password")
        
        with col_b:
            if st.button("📝 Sign Up", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()
        
        st.markdown("---")
        
        if st.button("🔑 Forgot Password?"):
            st.session_state.page = "forgot_password"
            st.rerun()


def show_signup_page():
    """Sign up page"""
    st.title("📝 Create Account")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Back button
        if st.button("← Back to Login"):
            st.session_state.page = "login"
            st.rerun()
        
        st.markdown("### Join Talk2Data")
        
        username = st.text_input("Username", key="signup_username")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        confirm_password = st.text_input("Confirm Password", type="password", key="signup_confirm")
        
        st.info("**Password Requirements:**\n- At least 8 characters\n- Uppercase and lowercase letters\n- At least one number")
        
        if st.button("✨ Create Account", use_container_width=True):
            if not all([username, email, password, confirm_password]):
                st.warning("Please fill in all fields")
            elif password != confirm_password:
                st.error("❌ Passwords don't match!")
            else:
                with st.spinner("Creating account..."):
                    success, message = signup_user(username, password, email)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.session_state.pending_verification = username
                        st.session_state.page = "verify"
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")


def show_verification_page():
    """Email verification page"""
    st.title("📧 Verify Your Email")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        username = st.session_state.get('pending_verification')
        
        st.info(f"📬 Verification code sent to your email for user: **{username}**")
        
        verification_code = st.text_input("Enter Verification Code", key="verify_code")
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            if st.button("✅ Verify", use_container_width=True):
                if verification_code:
                    with st.spinner("Verifying..."):
                        success, message = confirm_signup(username, verification_code)
                        
                        if success:
                            st.success(f"✅ {message}")
                            st.session_state.pending_verification = None
                            st.session_state.page = "login"
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
                else:
                    st.warning("Please enter verification code")
        
        with col_b:
            if st.button("🔄 Resend Code", use_container_width=True):
                with st.spinner("Resending..."):
                    success, message = resend_confirmation_code(username)
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
        
        st.markdown("---")
        
        if st.button("← Back to Login"):
            st.session_state.page = "login"
            st.rerun()


def show_forgot_password_page():
    """Forgot password page"""
    st.title("🔑 Reset Password")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        # Back button
        if st.button("← Back to Login"):
            st.session_state.page = "login"
            st.rerun()
        
        st.markdown("### Step 1: Request Reset Code")
        
        username = st.text_input("Username", key="forgot_username")
        
        if st.button("📧 Send Reset Code", use_container_width=True):
            if username:
                with st.spinner("Sending reset code..."):
                    success, message = forgot_password(username)
                    
                    if success:
                        st.success(f"✅ {message}")
                        st.session_state.reset_username = username
                    else:
                        st.error(f"❌ {message}")
            else:
                st.warning("Please enter username")
        
        st.markdown("---")
        
        if 'reset_username' in st.session_state:
            st.markdown("### Step 2: Enter New Password")
            
            reset_code = st.text_input("Reset Code", key="reset_code")
            new_password = st.text_input("New Password", type="password", key="reset_new_pass")
            confirm_new = st.text_input("Confirm New Password", type="password", key="reset_confirm")
            
            if st.button("🔓 Reset Password", use_container_width=True):
                if not all([reset_code, new_password, confirm_new]):
                    st.warning("Please fill in all fields")
                elif new_password != confirm_new:
                    st.error("❌ Passwords don't match!")
                else:
                    with st.spinner("Resetting password..."):
                        success, message = confirm_forgot_password(
                            st.session_state.reset_username,
                            reset_code,
                            new_password
                        )
                        
                        if success:
                            st.success(f"✅ {message}")
                            del st.session_state.reset_username
                            st.session_state.page = "login"
                            st.balloons()
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")


# ============================================
# Main Application (After Login)
# ============================================
def show_main_app():
    """Main Talk2Data application"""
    
    # Sidebar - User Info & Logout
    with st.sidebar:
        st.markdown("### 👤 User Profile")
        st.write(f"**Username:** {st.session_state.username}")
        if st.session_state.user_email:
            st.write(f"**Email:** {st.session_state.user_email}")
        
        st.markdown("---")
        
        # Logout button
        if st.button("🚪 Logout", use_container_width=True):
            if st.session_state.user_tokens:
                logout_user(st.session_state.user_tokens['access_token'])
            
            # Clear session
            st.session_state.authenticated = False
            st.session_state.user_tokens = None
            st.session_state.username = None
            st.session_state.user_email = None
            st.success("Logged out successfully!")
            st.rerun()
        
        st.markdown("---")
        
        # Change Password
        with st.expander("🔐 Change Password"):
            old_pass = st.text_input("Current Password", type="password", key="change_old")
            new_pass = st.text_input("New Password", type="password", key="change_new")
            confirm_pass = st.text_input("Confirm New", type="password", key="change_confirm")
            
            if st.button("Update Password"):
                if not all([old_pass, new_pass, confirm_pass]):
                    st.warning("Fill all fields")
                elif new_pass != confirm_pass:
                    st.error("Passwords don't match")
                else:
                    success, message = change_password(
                        st.session_state.user_tokens['access_token'],
                        old_pass,
                        new_pass
                    )
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
    
    # Main Content
    st.title("🤖 Talk2Data - AI SQL Generator")
    st.markdown("### Ask questions in natural language, get SQL queries!")
    
    # API Health Check
    col1, col2 = st.columns([3, 1])
    with col2:
        try:
            response = requests.get(f"{API_URL}/health", timeout=5)
            if response.status_code == 200:
                st.success("✅ API Online")
            else:
                st.error("❌ API Offline")
        except:
            st.error("❌ API Offline")
    
    # SQL Generation Interface
    st.markdown("---")
    
    question = st.text_area(
        "💬 Your Question:",
        placeholder="e.g., Show me total sales by store in 2015",
        height=100
    )
    
    col_a, col_b, col_c = st.columns([2, 1, 1])
    
    with col_b:
        confidence_threshold = st.slider("Confidence", 0.5, 1.0, 0.7, 0.05)
    
    with col_c:
        max_retries = st.number_input("Max Retries", 1, 5, 3)
    
    if st.button("🚀 Generate SQL", use_container_width=True):
        if question.strip():
            with st.spinner("🤖 Generating SQL..."):
                try:
                    response = requests.post(
                        f"{API_URL}/generate-sql",
                        json={
                            "question": question,
                            "max_retries": max_retries,
                            "confidence_threshold": confidence_threshold
                        },
                        timeout=30
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        
                        # Display Results
                        st.success("✅ SQL Generated Successfully!")
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Confidence", f"{result['confidence']:.0%}")
                        with col2:
                            st.metric("Validation", "✅ Passed" if result['validation_passed'] else "❌ Failed")
                        with col3:
                            st.metric("Time", f"{result['processing_time']:.2f}s")
                        
                        st.markdown("### 📝 Generated SQL:")
                        st.code(result['sql_query'], language='sql')
                        
                        # Copy button
                        st.markdown(f"```sql\n{result['sql_query']}\n```")
                        
                    else:
                        st.error(f"❌ Error {response.status_code}: {response.text}")
                        
                except requests.exceptions.Timeout:
                    st.error("❌ Request timeout. Please try again.")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        else:
            st.warning("⚠️ Please enter a question")
    
    # Examples
    with st.expander("💡 Example Questions"):
        st.markdown("""
        - Show me total sales by store
        - What are the top 5 stores by revenue?
        - Calculate average sales per day
        - Which stores had sales greater than 10000?
        - Show sales trends for store 1
        """)


# ============================================
# Page Router
# ============================================
def main():
    """Main application router"""
    
    # Initialize page state
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    
    # Route to appropriate page
    if st.session_state.authenticated:
        show_main_app()
    else:
        if st.session_state.page == "login":
            show_login_page()
        elif st.session_state.page == "signup":
            show_signup_page()
        elif st.session_state.page == "verify":
            show_verification_page()
        elif st.session_state.page == "forgot_password":
            show_forgot_password_page()


if __name__ == "__main__":
    main()
