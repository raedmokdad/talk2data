"""
Talk2Data Streamlit App with AWS Cognito Authentication
Complete UI with Login, Signup, Password Reset, and SQL Generation
"""

import streamlit as st
import requests
import json
from auth_service import (
    signup_user, confirm_signup, resend_confirmation_code,
    login_user, logout_user, forgot_password, confirm_forgot_password,
    change_password, get_user_info
)

# Page Configuration
st.set_page_config(
    page_title="Talk2Data - SQL Generator",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API Configuration
#API_URL = "https://talk2data-production.up.railway.app"
API_URL = "http://localhost:8000"  # Für lokale Entwicklung

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


def get_auth_header():
    """ Get authorisation headers with Token"""
    if st.session_state.user_tokens:
        return {"Authorization": f"Bearer {st.session_state.user_tokens['access_token']}"}
    return {}

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
    st.title("📊 Talk2Data - SQL Generator")
    st.markdown("### Transform your business questions into SQL queries!")
    
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
    
    # Schema Selection
    st.markdown("### 1️⃣ Select Your Schema")
    
    # Fetch user's schemas
    try:
        access_token = st.session_state.user_tokens.get('access_token')
        if access_token:
            headers = {"Authorization": f"Bearer {access_token}"}
            username = st.session_state.user_email.split('@')[0]
            
            response = requests.get(
                f"{API_URL}/schemas/{username}",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                available_schemas = data.get('schemas', [])
                
                if available_schemas:
                    selected_schema = st.selectbox(
                        "📋 Choose a schema:",
                        options=available_schemas,
                        help="Select the database schema you want to query"
                    )
                    
                    # Store selected schema in session state
                    st.session_state.selected_schema = selected_schema
                    st.info(f"✅ Using schema: **{selected_schema}**")
                else:
                    st.warning("⚠️ No schemas found. Please upload a schema first in Schema Management below.")
                    st.session_state.selected_schema = None
            else:
                st.error("Failed to load schemas")
                st.session_state.selected_schema = None
        else:
            st.error("No access token. Please login again.")
            st.session_state.selected_schema = None
    except Exception as e:
        st.error(f"Error loading schemas: {str(e)}")
        st.session_state.selected_schema = None
    
    st.markdown("### 2️⃣ Ask Your Question")
    
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
    
    # Check if schema is selected
    schema_selected = st.session_state.get('selected_schema') is not None
    
    if not schema_selected:
        st.warning("⚠️ Please select a schema first!")
    
    if st.button("🚀 Generate SQL", use_container_width=True, disabled=not schema_selected):
        if question.strip():
            if not schema_selected:
                st.error("❌ No schema selected. Please select a schema first.")
            else:
                selected_schema_name = st.session_state.selected_schema
                
                with st.spinner("⚡ Generating SQL..."):
                    try:
                        # Get auth headers with JWT token
                        headers = get_auth_header()
                        
                        response = requests.post(
                            f"{API_URL}/generate-sql",
                            json={
                                "question": question,
                                "max_retries": max_retries,
                                "confidence_threshold": confidence_threshold,
                                "schema_name": selected_schema_name  # Pass selected schema
                            },
                            headers=headers,  # Add JWT token
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
    
    # Schema Management UI
    with st.expander("🗂️ Schema Management", expanded=False):
        st.markdown("### Manage Your Database Schemas")
        
        # Tabs for different schema operations
        tab_view, tab_upload, tab_delete, tab_builder = st.tabs([
            "📋 View Schemas", 
            "⬆️ Upload Schema", 
            "🗑️ Delete Schema",
            "🏗️ Schema Builder"
        ])
        
        # TAB 1: View Schemas
        with tab_view:
            if st.button("🔄 Refresh Schemas", use_container_width=True):
                try:
                    # Get the access token from session state
                    access_token = st.session_state.user_tokens.get('access_token')
                    
                    if not access_token:
                        st.error("No access token found. Please login again.")
                    else:
                        # Make authenticated request to list schemas
                        headers = {
                            "Authorization": f"Bearer {access_token}"
                        }
                        
                        # Get username from session state
                        username = st.session_state.user_email.split('@')[0]
                        
                        response = requests.get(
                            f"{API_URL}/schemas/{username}",
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            schemas = data.get('schemas', [])
                            
                            if schemas:
                                st.success(f"Found {len(schemas)} schema(s):")
                                for schema in schemas:
                                    st.write(f"- {schema}")
                            else:
                                st.info("No schemas found.")
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                
                except Exception as e:
                    st.error(f"Error loading schemas: {str(e)}")
        
        # TAB 2: Upload Schema
        with tab_upload:
            schema_name = st.text_input("Schema Name", key="schema_name_input")
            schema_file = st.file_uploader("Upload JSON Schema", type=['json'], key="schema_uploader")
            
            if st.button("⬆️ Upload Schema"):
                if not schema_name:
                    st.error("Please enter a schema name.")
                elif not schema_file:
                    st.error("Please upload a schema file.")
                else:
                    try:
                        # Read and parse the JSON file
                        schema_data = json.loads(schema_file.read())
                        
                        # Get the access token
                        access_token = st.session_state.user_tokens.get('access_token')
                        
                        if not access_token:
                            st.error("No access token found. Please login again.")
                        else:
                            headers = {
                                "Authorization": f"Bearer {access_token}",
                                "Content-Type": "application/json"
                            }
                            
                            # Get username
                            username = st.session_state.user_email.split('@')[0]
                            
                            # POST request to create schema
                            response = requests.post(
                                f"{API_URL}/schemas/{username}/{schema_name}",
                                headers=headers,
                                json={"schema_data": schema_data},
                                timeout=30
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                st.success(f"✅ Schema '{schema_name}' uploaded successfully!")
                                st.json(result)
                            else:
                                st.error(f"❌ Error {response.status_code}")
                                st.code(response.text)
                    
                    except json.JSONDecodeError as e:
                        st.error(f"Invalid JSON file: {str(e)}")
                    except requests.exceptions.RequestException as e:
                        st.error(f"Network error: {str(e)}")
                    except Exception as e:
                        st.error(f"Unexpected error: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        
        # TAB 3: Delete Schema
        with tab_delete:
            delete_schema_name = st.text_input("Schema Name to Delete", key="delete_schema_input")
            
            # Checkbox for confirmation
            confirm_delete = st.checkbox(f"⚠️ I confirm deletion of '{delete_schema_name}'", key="confirm_checkbox")
            
            if st.button("🗑️ Delete Schema", disabled=not confirm_delete):
                if not delete_schema_name:
                    st.error("Please enter a schema name.")
                else:
                    try:
                        access_token = st.session_state.user_tokens.get('access_token')
                        
                        if not access_token:
                            st.error("No access token found. Please login again.")
                        else:
                            headers = {
                                "Authorization": f"Bearer {access_token}"
                            }
                            
                            username = st.session_state.user_email.split('@')[0]
                            
                            st.info(f"Deleting: {API_URL}/schemas/{username}/{delete_schema_name}")
                            
                            response = requests.delete(
                                f"{API_URL}/schemas/{username}/{delete_schema_name}",
                                headers=headers,
                                timeout=30
                            )
                            
                            st.info(f"Response Status: {response.status_code}")
                            
                            if response.status_code == 200:
                                result = response.json()
                                st.success(f"✅ Schema '{delete_schema_name}' deleted successfully!")
                                st.json(result)
                            else:
                                st.error(f"❌ Error {response.status_code}")
                                st.code(response.text)
                    
                    except requests.exceptions.RequestException as e:
                        st.error(f"Network error: {str(e)}")
                    except Exception as e:
                        st.error(f"Unexpected error: {str(e)}")
                        import traceback
                        st.code(traceback.format_exc())
        
        # TAB 4: Schema Builder
        with tab_builder:
            st.markdown("### 🏗️ Visual Schema Builder")
            st.info("💡 Create star schemas visually with tables, relationships, metrics, and examples")
            
            # Initialize builder session state
            if 'builder_schema' not in st.session_state:
                st.session_state.builder_schema = {
                    "schema": {
                        "tables": [],
                        "relationships": [],
                        "notes": []
                    },
                    "synonyms": {},
                    "kpis": {},
                    "examples": [],
                    "glossary": {}
                }
            
            # Builder tabs
            builder_tab1, builder_tab2, builder_tab3, builder_tab4 = st.tabs([
                "📊 Tables",
                "📈 Metrics",
                "💡 Examples",
                "💾 Save & Download"
            ])
            
            # BUILDER TAB 1: Tables
            with builder_tab1:
                st.markdown("#### Add Tables to Your Schema")
                
                col_add1, col_add2 = st.columns([1, 1])
                
                with col_add1:
                    new_table_name = st.text_input("Table Name", placeholder="fact_sales", key="new_table_name")
                    table_role = st.selectbox("Table Role", ["fact", "dimension"], key="table_role")
                
                with col_add2:
                    table_grain = st.text_input("Grain", placeholder="one row per sale", key="table_grain")
                    
                    if st.button("➕ Add Table", use_container_width=True):
                        if new_table_name:
                            new_table = {
                                "name": new_table_name,
                                "role": table_role,
                                "grain": table_grain,
                                "columns": {},
                                "primary_key": ""
                            }
                            if table_role == "fact":
                                new_table["foreign_keys"] = {}
                            
                            st.session_state.builder_schema["schema"]["tables"].append(new_table)
                            st.success(f"✅ Table '{new_table_name}' added!")
                            st.rerun()
                        else:
                            st.warning("Please enter a table name")
                
                st.markdown("---")
                
                # Display existing tables
                tables = st.session_state.builder_schema["schema"]["tables"]
                if tables:
                    for idx, table in enumerate(tables):
                        with st.expander(f"**{table['name']}** ({table['role']})", expanded=False):
                            # Edit table properties
                            table['name'] = st.text_input("Name", value=table['name'], key=f"edit_name_{idx}")
                            table['grain'] = st.text_input("Grain", value=table['grain'], key=f"edit_grain_{idx}")
                            table['primary_key'] = st.text_input("Primary Key", value=table.get('primary_key', ''), key=f"edit_pk_{idx}")
                            
                            # Add columns
                            st.markdown("**Columns:**")
                            col_c1, col_c2, col_c3 = st.columns([2, 4, 1])
                            with col_c1:
                                new_col = st.text_input("Column", key=f"new_col_{idx}", placeholder="column_name")
                            with col_c2:
                                new_col_desc = st.text_input("Description", key=f"new_col_desc_{idx}", placeholder="INT - Description")
                            with col_c3:
                                if st.button("➕", key=f"add_col_btn_{idx}"):
                                    if new_col and new_col_desc:
                                        if 'columns' not in table:
                                            table['columns'] = {}
                                        table['columns'][new_col] = new_col_desc
                                        st.rerun()
                            
                            # Show existing columns
                            if table.get('columns'):
                                for col_name, col_desc in table['columns'].items():
                                    st.text(f"• {col_name}: {col_desc}")
                            
                            # Foreign keys for fact tables
                            if table['role'] == 'fact':
                                st.markdown("**Foreign Keys:**")
                                col_f1, col_f2, col_f3 = st.columns([2, 4, 1])
                                with col_f1:
                                    new_fk = st.text_input("FK Column", key=f"new_fk_{idx}", placeholder="store_key")
                                with col_f2:
                                    new_fk_ref = st.text_input("References", key=f"new_fk_ref_{idx}", placeholder="dim_store.store_key")
                                with col_f3:
                                    if st.button("➕", key=f"add_fk_btn_{idx}"):
                                        if new_fk and new_fk_ref:
                                            if 'foreign_keys' not in table:
                                                table['foreign_keys'] = {}
                                            table['foreign_keys'][new_fk] = new_fk_ref
                                            st.rerun()
                                
                                # Show existing FKs
                                if table.get('foreign_keys'):
                                    for fk_col, fk_ref in table['foreign_keys'].items():
                                        st.text(f"• {fk_col} → {fk_ref}")
                            
                            # Delete table
                            if st.button(f"🗑️ Delete Table", key=f"del_table_{idx}", type="secondary"):
                                st.session_state.builder_schema["schema"]["tables"].pop(idx)
                                st.rerun()
                else:
                    st.info("No tables yet. Add your first table above!")
            
            # BUILDER TAB 2: Metrics
            with builder_tab2:
                st.markdown("#### Define Common Metrics/KPIs")
                
                col_m1, col_m2 = st.columns([1, 1])
                with col_m1:
                    metric_key = st.text_input("Metric Key", placeholder="total_revenue", key="metric_key")
                    metric_formula = st.text_input("Formula", placeholder="SUM(fact_sales.amount)", key="metric_formula")
                with col_m2:
                    metric_desc = st.text_input("Description", placeholder="Total revenue", key="metric_desc")
                    metric_keywords = st.text_input("Keywords (comma-separated)", placeholder="umsatz, revenue", key="metric_keywords")
                
                if st.button("➕ Add Metric", use_container_width=True):
                    if metric_key and metric_formula:
                        if 'kpis' not in st.session_state.builder_schema:
                            st.session_state.builder_schema['kpis'] = {}
                        
                        st.session_state.builder_schema['kpis'][metric_key] = {
                            "formula": metric_formula,
                            "description": metric_desc,
                            "keywords": [k.strip() for k in metric_keywords.split(",") if k.strip()]
                        }
                        st.success(f"✅ Metric '{metric_key}' added!")
                        st.rerun()
                
                st.markdown("---")
                
                # Show existing metrics
                if st.session_state.builder_schema.get('kpis'):
                    for key, value in st.session_state.builder_schema['kpis'].items():
                        with st.expander(f"**{key}**"):
                            st.code(value.get('formula', ''), language='sql')
                            st.text(f"Description: {value.get('description', '')}")
                            st.text(f"Keywords: {', '.join(value.get('keywords', []))}")
            
            # BUILDER TAB 3: Examples
            with builder_tab3:
                st.markdown("#### Add SQL Example Queries")
                
                example_desc = st.text_input("Description", placeholder="Monthly sales by region", key="example_desc")
                example_sql = st.text_area("SQL Pattern", placeholder="SELECT ... FROM ... WHERE ...", height=100, key="example_sql")
                
                if st.button("➕ Add Example", use_container_width=True):
                    if example_desc and example_sql:
                        if 'examples' not in st.session_state.builder_schema:
                            st.session_state.builder_schema['examples'] = []
                        
                        st.session_state.builder_schema['examples'].append({
                            "description": example_desc,
                            "pattern": example_sql
                        })
                        st.success("✅ Example added!")
                        st.rerun()
                
                st.markdown("---")
                
                # Show existing examples
                if st.session_state.builder_schema.get('examples'):
                    for idx, ex in enumerate(st.session_state.builder_schema['examples']):
                        with st.expander(f"**{ex['description']}**"):
                            st.code(ex['pattern'], language='sql')
            
            # BUILDER TAB 4: Save & Download
            with builder_tab4:
                st.markdown("#### Save Your Schema")
                
                save_schema_name = st.text_input(
                    "Schema Name",
                    value="my_custom_schema",
                    key="save_schema_name"
                )
                
                col_s1, col_s2 = st.columns(2)
                
                with col_s1:
                    # Upload to S3
                    if st.button("☁️ Upload to S3", use_container_width=True, type="primary"):
                        try:
                            from src.s3_service import upload_user_schema
                            username = st.session_state.user_email.split('@')[0] if st.session_state.user_email else "demo_user"
                            
                            success, message = upload_user_schema(
                                username,
                                save_schema_name,
                                st.session_state.builder_schema
                            )
                            
                            if success:
                                st.success(f"✅ {message}")
                            else:
                                st.error(f"❌ {message}")
                        except Exception as e:
                            st.error(f"Upload failed: {str(e)}")
                
                with col_s2:
                    # Download JSON
                    schema_json = json.dumps(st.session_state.builder_schema, indent=2)
                    st.download_button(
                        label="📥 Download JSON",
                        data=schema_json,
                        file_name=f"{save_schema_name}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                
                # Preview JSON
                with st.expander("📄 JSON Preview"):
                    st.json(st.session_state.builder_schema)
                
                # Reset button
                if st.button("🆕 Start New Schema", use_container_width=True):
                    st.session_state.builder_schema = {
                        "schema": {
                            "tables": [],
                            "relationships": [],
                            "notes": []
                        },
                        "synonyms": {},
                        "kpis": {},
                        "examples": [],
                        "glossary": {}
                    }
                    st.success("Schema cleared!")
                    st.rerun()


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
