"""
Schema Builder Dashboard for Talk2Data
Create and manage star schema JSON files with visual interface
"""
from __future__ import annotations

import streamlit as st
import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import sys
import requests
from typing import List
import pandas as pd
from src.models import DBType, DBSelection, FileItem, FileType
from src.factory import create_connector
from src.base_connector import BaseConnector
import altair as alt

# Add src to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.s3_service import upload_user_schema, get_current_user, get_s3_client
import boto3

# API Configuration - Use Railway URL or localhost for development
API_URL = os.environ.get("API_URL", "https://talk2data-production.up.railway.app")

# Page config
st.set_page_config(
    page_title="Schema Builder - Talk2Data",
    page_icon="🏗️",
    layout="wide"
)


# Add authentication import
try:
    from auth_service import (
        login_user, signup_user, logout_user, 
        get_user_info, confirm_signup
    )
    AUTH_AVAILABLE = True
except ImportError:
    AUTH_AVAILABLE = False

# Initialize session state
if 'schema_data' not in st.session_state:
    st.session_state.schema_data = {
        "schema": {
            "tables": [],
            "notes": [],
            "relationships": []
        },
        "synonyms": {},
        "kpis": {},
        "examples": [],
        "glossary": {}
    }

if 'current_table' not in st.session_state:
    st.session_state.current_table = None

if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if 'username' not in st.session_state:
    st.session_state.username = "raedmokdad"  # Fixed: Set to match S3 username

if 'user_tokens' not in st.session_state:
    st.session_state.user_tokens = None

if 'current_schema_name' not in st.session_state:
    st.session_state.current_schema_name = "my_star_schema"

def get_connector() -> BaseConnector | None:
    return st.session_state.get("connector")

def create_default_table(table_type: str = "fact") -> Dict[str, Any]:
    """Create a default table template"""
    if table_type == "fact":
        return {
            "name": "fact_",
            "role": "fact",
            "grain": "one row per ",
            "columns": {},
            "primary_key": "",
            "foreign_keys": {}
        }
    else:  # dimension
        return {
            "name": "dim_",
            "role": "dimension",
            "grain": "one row per ",
            "columns": {},
            "primary_key": ""
        }


def save_schema_locally(schema_data: Dict, filename: str):
    """Save schema to local file"""
    try:
        # Create schemas directory if not exists
        schemas_dir = Path("schemas")
        schemas_dir.mkdir(exist_ok=True)
        
        filepath = schemas_dir / f"{filename}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(schema_data, f, indent=2, ensure_ascii=False)
        
        st.success(f"✅ Schema saved locally to: {filepath}")
        return True
    except Exception as e:
        st.error(f"❌ Error saving locally: {str(e)}")
        return False


def upload_schema_to_s3(schema_data: Dict, schema_name: str, username: str):
    """Upload schema to S3"""
    try:
        success, message = upload_user_schema(username, schema_name, schema_data)
        if success:
            st.success(f"✅ {message}")
        else:
            st.error(f"❌ {message}")
        return success
    except Exception as e:
        st.error(f"❌ S3 Upload failed: {str(e)}")
        return False


def test_schema_with_sql(question: str, schema_name: str) -> tuple[bool, str]:
    """Test the schema by generating SQL from a question"""
    try:
        response = requests.post(
            f"{API_URL}/generate-sql",
            json={
                "question": question,
                "schema_name": schema_name
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return True, data.get('sql_query', '')
        else:
            return False, f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return False, f"API Error: {str(e)}"


def show_login_page():
    """Show login interface"""
    st.title("🔐 Schema Builder - Login")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("### Welcome to Schema Builder")
        
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        
        with tab1:
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            
            if st.button("🚀 Login", use_container_width=True):
                if username and password:
                    with st.spinner("Logging in..."):
                        success, result = login_user(username, password)
                        
                        if success:
                            st.session_state.authenticated = True
                            st.session_state.user_tokens = result
                            st.session_state.username = result.get('username', username)
                            st.success("✅ Login successful!")
                            st.rerun()
                        else:
                            st.error(f"❌ {result}")
                else:
                    st.warning("Please enter username and password")
        
        with tab2:
            new_username = st.text_input("Username", key="signup_username")
            new_email = st.text_input("Email", key="signup_email")
            new_password = st.text_input("Password", type="password", key="signup_password")
            new_password_confirm = st.text_input("Confirm Password", type="password", key="signup_password_confirm")
            
            if st.button("📝 Create Account", use_container_width=True):
                if new_username and new_email and new_password:
                    if new_password == new_password_confirm:
                        with st.spinner("Creating account..."):
                            success, result = signup_user(new_username, new_password, new_email)
                            
                            if success:
                                st.success("✅ Account created! Please check your email for verification code.")
                                st.info("After verification, go back to Login tab.")
                            else:
                                st.error(f"❌ {result}")
                    else:
                        st.error("Passwords don't match!")
                else:
                    st.warning("Please fill all fields")


def load_schema_template():
    """Load the retail star schema as template"""
    try:
        template_path = Path("src/config/retial_star_schema.json")
        with open(template_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        st.error(f"Could not load template: {str(e)}")
        return None


# ============================================================================
# AUTHENTICATION CHECK
# ============================================================================

# Show login page if auth is available and user not authenticated
if AUTH_AVAILABLE and not st.session_state.authenticated:
    show_login_page()
    st.stop()

# ============================================================================
# MAIN APP
# ============================================================================

# Header with user info
col_h1, col_h2, col_h3 = st.columns([4, 2, 1])
with col_h1:
    st.title("🏗️ Schema Builder - Talk2Data")
    st.markdown("Create and manage star schema definitions for your data warehouse")
with col_h2:
    if st.session_state.username:
        st.markdown(f"**👤 User:** {st.session_state.username}")
        
        # Show current schema info
        tables = st.session_state.schema_data["schema"]["tables"]
        if tables:
            st.caption(f"📊 {len(tables)} tables | Schema: {st.session_state.current_schema_name}")
        else:
            st.caption(f"Schema: {st.session_state.current_schema_name}")
with col_h3:
    if st.session_state.username:
        if st.button("🚪 Logout"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.user_tokens = None
            st.rerun()

# ============================================================================
# MODUS-AUSWAHL
# ============================================================================
st.sidebar.title("🎯 Modus")
app_mode = st.sidebar.radio(
    "Wähle eine Funktion:",
    ["📝 Schema Builder", "🔍 Database Query"],
    label_visibility="collapsed"
)
st.sidebar.markdown("---")

# ============================================================================
# SCHEMA BUILDER MODUS
# ============================================================================
if app_mode == "📝 Schema Builder":
    # Sidebar for schema management
    st.sidebar.header("📋 Schema Management")

# Load from S3
    st.sidebar.subheader("☁️ Load from S3")
    try:
        from src.s3_service import list_user_schema, get_user_schema
    
        # Use raedmokdad as default username to match S3 structure
        username = st.session_state.username or "raedmokdad"
    
        col_s3_a, col_s3_b = st.sidebar.columns([3, 1])
    
        with col_s3_b:
            if st.button("🔄", help="Refresh schemas from S3"):
                st.rerun()
    
        with col_s3_a:
            with st.spinner("Loading from S3..."):
                success, s3_schemas = list_user_schema(username)
            
                # Debug info
                st.sidebar.caption(f"🔍 User: '{username}' | Success: {success} | Found: {len(s3_schemas) if s3_schemas else 0} schemas")
            
                if success and s3_schemas:
                    selected_s3_schema = st.selectbox(
                        "Your Schemas:",
                        options=["-- Select Schema --"] + s3_schemas,
                        key="s3_schema_selector"
                    )
                
                    if selected_s3_schema != "-- Select Schema --":
                        if st.button("📥 Load Selected", use_container_width=True):
                            with st.spinner(f"Loading {selected_s3_schema}..."):
                                load_success, schema_data = get_user_schema(username, selected_s3_schema)
                            
                                if load_success:
                                    st.session_state.schema_data = schema_data
                                    st.session_state.current_schema_name = selected_s3_schema
                                    st.sidebar.success(f"✅ Loaded: {selected_s3_schema}")
                                    st.rerun()
                                else:
                                    st.sidebar.error(f"❌ Failed to load schema")
                elif success:
                    st.sidebar.info(f"No schemas on S3 for user: {username}")
                else:
                    st.sidebar.warning("S3 not configured or error")
                
    except Exception as e:
        st.sidebar.error(f"⚠️ S3 error: {str(e)}")

    st.sidebar.markdown("---")

    # Load template button
    if st.sidebar.button("📥 Load Retail Template", use_container_width=True):
        template = load_schema_template()
        if template:
            st.session_state.schema_data = template
            st.session_state.current_schema_name = "retial_star_schema"
            st.sidebar.success("Template loaded!")
            st.rerun()

    # New schema button
    if st.sidebar.button("🆕 New Empty Schema", use_container_width=True):
        st.session_state.schema_data = {
            "schema": {
                "tables": [],
                "relationships": [],
                "metrics": {},
                "examples": [],
                "glossary": {}
            }
        }
        st.session_state.current_schema_name = "new_schema"
        st.sidebar.success("New schema created!")
        st.rerun()

    # Schema name input
    schema_name = st.sidebar.text_input(
        "Schema Name", 
        value=st.session_state.current_schema_name,
        key="schema_name_input"
    )
    st.session_state.current_schema_name = schema_name

    st.sidebar.markdown("---")
    st.sidebar.subheader("💾 Save Options")

    # Save locally
    if st.sidebar.button("💾 Save Locally", use_container_width=True):
        save_schema_locally(st.session_state.schema_data, schema_name)

    # Save to S3
    if st.sidebar.button("☁️ Upload to S3", use_container_width=True):
        username = st.session_state.username or "raedmokdad"
        success = upload_schema_to_s3(st.session_state.schema_data, schema_name, username)
        if success:
            st.sidebar.info("💡 Reload to see in S3 list")

    # Download button
    schema_json = json.dumps(st.session_state.schema_data, indent=2)
    st.sidebar.download_button(
        label="📥 Download JSON",
        data=schema_json,
        file_name=f"{schema_name}.json",
        mime="application/json",
        use_container_width=True
    )

    # Upload JSON file to S3
    st.sidebar.markdown("---")
    with st.sidebar.expander("📤 Upload JSON File to S3"):
        uploaded_file = st.file_uploader(
            "Choose a JSON schema file",
            type=['json'],
            key="json_uploader",
            help="Upload a local JSON schema file to S3"
        )
        
        if uploaded_file is not None:
            try:
                # Read the uploaded JSON file
                file_content = uploaded_file.read()
                schema_data = json.loads(file_content)
                
                # Preview the schema
                st.caption(f"📄 File: {uploaded_file.name}")
                with st.expander("Preview JSON"):
                    st.json(schema_data)
                
                # Schema name input
                default_name = uploaded_file.name.replace('.json', '')
                upload_name = st.text_input(
                    "Schema name for S3:",
                    value=default_name,
                    key="upload_json_name"
                )
                
                # Upload button
                if st.button("☁️ Upload to S3", use_container_width=True, key="upload_json_btn"):
                    username = st.session_state.username or "raedmokdad"
                    success = upload_schema_to_s3(schema_data, upload_name, username)
                    if success:
                        st.success(f"✅ '{upload_name}' uploaded to S3!")
                        st.info("💡 Click 'Reload to see in S3 list' to refresh")
            
            except json.JSONDecodeError as e:
                st.error(f"❌ Invalid JSON file: {str(e)}")
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Delete from S3
    st.sidebar.markdown("---")
    with st.sidebar.expander("🗑️ Delete from S3"):
        try:
            from src.s3_service import delete_user_schema, list_user_schema
        
            username = st.session_state.username or "raedmokdad"
            success, s3_schemas = list_user_schema(username)
        
            if success and s3_schemas:
                schema_to_delete = st.selectbox(
                    "Select schema to delete:",
                    options=s3_schemas,
                    key="delete_schema_selector"
                )
            
                if st.button("🗑️ Delete Selected", type="secondary", use_container_width=True):
                    if st.checkbox("Confirm deletion", key="confirm_delete"):
                        del_success, del_message = delete_user_schema(username, schema_to_delete)
                        if del_success:
                            st.success(del_message)
                            st.rerun()
                        else:
                            st.error(del_message)
            else:
                st.info("No schemas to delete")
        except Exception as e:
            st.warning("S3 not available")

# ============================================================================
# DATABASE QUERY MODUS
# ============================================================================
else:  # app_mode == "🔍 Database Query"
    # --- Sidebar: Data source selection ---
    st.sidebar.header("🔌 Data Source")

    db_type_label_to_enum = {
        "PostgreSQL": DBType.POSTGRES,
        "MySQL": DBType.MYSQL,
        "Amazon Redshift": DBType.REDSHIFT,
        "CSV / Excel Files": DBType.FILES,
    }

    db_choice = st.sidebar.selectbox(
        "Select data source type",
        list(db_type_label_to_enum.keys()),
    )

    selected_db_type = db_type_label_to_enum[db_choice]

    selection_kwargs = {"db_type": selected_db_type}

    # SQL DB configuration
    if selected_db_type in {DBType.POSTGRES, DBType.MYSQL, DBType.REDSHIFT}:
        st.sidebar.subheader("SQL Connection Details")

        host = st.sidebar.text_input("Host", value="localhost")
        port_default = 5432 if selected_db_type != DBType.MYSQL else 3306
        port = st.sidebar.number_input("Port", value=port_default, step=1)
        database = st.sidebar.text_input("Database name")
        user = st.sidebar.text_input("User")
        password = st.sidebar.text_input("Password", type="password")

        selection_kwargs.update(
            {
                "host": host,
                "port": port,
                "database": database,
                "user": user,
                "password": password,
            }
        )

    # File-based configuration
    elif selected_db_type == DBType.FILES:
        st.sidebar.subheader("S3 paths (no listing)")

        s3_paths = st.sidebar.text_area(
            "Enter S3 paths (one per line), e.g.\n"
            "s3://excel-bucket-fortest/rossmann/rossmann_2013.xlsx\n"
            "s3://excel-bucket-fortest/rossmann/rossmann_2014.csv"
        )

        file_items: list[FileItem] = []

        for line in s3_paths.splitlines():
            line = line.strip()
            if not line:
                continue

            lower = line.lower()
            if lower.endswith(".csv"):
                file_items.append(
                    FileItem(
                        s3_uri=line,
                        type=FileType.CSV,
                    )
                )
            elif lower.endswith((".xlsx", ".xls")):
                sheet_input_key = f"sheet_{line}"
                sheet_name = st.sidebar.text_input(
                    f"Sheet name for {line} (optional, default first sheet)",
                    key=sheet_input_key,
                )
                file_items.append(
                    FileItem(
                        s3_uri=line,
                        type=FileType.EXCEL,
                        sheet_name=sheet_name or None,
                    )
                )
            else:
                st.sidebar.warning(f"Unsupported file type: {line}")

        selection_kwargs["files"] = file_items if file_items else None


    # --- Connect button ---
    col1, col2 = st.sidebar.columns([2, 1])
    
    with col1:
        connect_clicked = st.button("Connect", use_container_width=True)
    
    with col2:
        if st.session_state.get("connector"):
            disconnect_clicked = st.button("Disconnect", use_container_width=True)
        else:
            disconnect_clicked = False
    
    if connect_clicked:
        try:
            selection = DBSelection(**selection_kwargs)
            connector = create_connector(selection)
            st.session_state["connector"] = connector
            st.success("✅ Connected successfully!")
            st.write("Available tables:", ", ".join(connector.list_tables()))
        except Exception as e:
            st.error(f"❌ Connection failed: {e}")
    
    if disconnect_clicked:
        st.session_state["connector"] = None
        st.session_state["last_df"] = None
        st.session_state["last_sql"] = None
        st.session_state["last_msg"] = None
        st.info("🔌 Disconnected from database")
        st.rerun()
    
    # --- Schema Selection for AI Query ---
    st.sidebar.markdown("---")
    st.sidebar.subheader("🤖 AI Query Schema")
    
    try:
        from src.s3_service import list_user_schema
        
        username = st.session_state.username or "raedmokdad"
        
        col_db_s3_a, col_db_s3_b = st.sidebar.columns([3, 1])
        
        with col_db_s3_b:
            if st.button("🔄", help="Refresh schemas", key="refresh_db_schemas"):
                st.rerun()
        
        with col_db_s3_a:
            with st.spinner("Loading..."):
                success, db_schemas = list_user_schema(username)
                
                if success and db_schemas:
                    selected_db_schema = st.selectbox(
                        "Schema for AI:",
                        options=db_schemas,
                        index=db_schemas.index(st.session_state.get('db_query_schema', db_schemas[0])) 
                            if st.session_state.get('db_query_schema') in db_schemas else 0,
                        help="Select schema for natural language queries",
                        key="db_schema_selector"
                    )
                    
                    # Automatically set the selected schema
                    st.session_state['db_query_schema'] = selected_db_schema
                    st.sidebar.caption(f"✅ Using: {selected_db_schema}")
                else:
                    st.sidebar.info("No schemas found on S3")
    except Exception as e:
        st.sidebar.warning(f"Schema load error: {str(e)}")

# ============================================================================
# MAIN CONTENT AREA
# ============================================================================

if app_mode == "📝 Schema Builder":
    # ============================================================================
    # SCHEMA BUILDER: MAIN CONTENT TABS
    # ============================================================================
    
    # Auto-detect schema type: flat table (1 table) vs OLAP (multiple tables)
    num_tables = len(st.session_state.schema_data["schema"]["tables"])
    is_flat_table = num_tables == 1
    
    # Conditionally show Relationships tab only for multi-table schemas
    if is_flat_table:
        tab_names = [
            "📊 Tables", 
            "📝 Notes",
            "🔄 Synonyms",
            "📈 KPIs", 
            "💡 Examples", 
            "📖 Glossary",
            "🧪 Test SQL"
        ]
        tab1, tab2, tab4, tab5, tab6, tab7, tab8 = st.tabs(tab_names)
        tab3 = None  # Relationships tab doesn't exist for flat tables
    else:
        tab_names = [
            "📊 Tables", 
            "📝 Notes",
            "🔗 Relationships", 
            "🔄 Synonyms",
            "📈 KPIs", 
            "💡 Examples", 
            "📖 Glossary",
            "🧪 Test SQL"
        ]
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(tab_names)

# ============================================================================
    # TAB 1: TABLES
    # ============================================================================
    with tab1:
        st.header("📊 Table Definitions")
    
        col1, col2 = st.columns([2, 1])
    
        with col2:
            st.subheader("Add New Table")
            table_type = st.radio("Table Type", ["fact", "dimension"])
        
            if st.button("➕ Add Table", use_container_width=True):
                new_table = create_default_table(table_type)
                st.session_state.schema_data["schema"]["tables"].append(new_table)
                st.rerun()
    
        with col1:
            st.subheader("Existing Tables")
        
            tables = st.session_state.schema_data["schema"]["tables"]
        
            if not tables:
                st.info("No tables defined yet. Add a table to get started!")
            else:
                for idx, table in enumerate(tables):
                    with st.expander(f"**{table['name']}** ({table['role']})", expanded=False):
                        # Basic info
                        col_a, col_b = st.columns(2)
                        with col_a:
                            table['name'] = st.text_input(
                                "Table Name", 
                                value=table['name'], 
                                key=f"name_{idx}"
                            )
                            table['role'] = st.selectbox(
                                "Role",
                                options=["fact", "dimension"],
                                index=0 if table['role'] == "fact" else 1,
                                key=f"role_{idx}"
                            )
                        with col_b:
                            table['grain'] = st.text_input(
                                "Grain", 
                                value=table['grain'], 
                                key=f"grain_{idx}"
                            )
                            table['primary_key'] = st.text_input(
                                "Primary Key", 
                                value=table.get('primary_key', ''), 
                                key=f"pk_{idx}"
                            )
                    
                        # Columns
                        st.markdown("**Columns:**")
                    
                        # Add new column
                        col_new_a, col_new_b, col_new_c = st.columns([2, 3, 1])
                        with col_new_a:
                            new_col_name = st.text_input(
                                "Column name", 
                                key=f"new_col_name_{idx}",
                                placeholder="column_name"
                            )
                        with col_new_b:
                            new_col_desc = st.text_input(
                                "Description", 
                                key=f"new_col_desc_{idx}",
                                placeholder="VARCHAR - Description"
                            )
                        with col_new_c:
                            if st.button("➕", key=f"add_col_{idx}"):
                                if new_col_name and new_col_desc:
                                    if 'columns' not in table:
                                        table['columns'] = {}
                                    table['columns'][new_col_name] = new_col_desc
                                    st.rerun()
                    
                        # Display existing columns
                        if 'columns' in table and table['columns']:
                            cols_to_delete = []
                            for col_name, col_desc in table['columns'].items():
                                col_x, col_y, col_z = st.columns([2, 6, 1])
                                with col_x:
                                    st.text(col_name)
                                with col_y:
                                    st.text(col_desc)
                                with col_z:
                                    if st.button("🗑️", key=f"del_col_{idx}_{col_name}"):
                                        cols_to_delete.append(col_name)
                        
                            for col_name in cols_to_delete:
                                del table['columns'][col_name]
                                st.rerun()
                    
                        # Foreign keys (only for fact tables)
                        if table['role'] == 'fact':
                            st.markdown("**Foreign Keys:**")
                        
                            # Add new FK
                            col_fk_a, col_fk_b, col_fk_c = st.columns([2, 3, 1])
                            with col_fk_a:
                                new_fk_col = st.text_input(
                                    "FK Column", 
                                    key=f"new_fk_col_{idx}",
                                    placeholder="date_key"
                                )
                            with col_fk_b:
                                new_fk_ref = st.text_input(
                                    "References", 
                                    key=f"new_fk_ref_{idx}",
                                    placeholder="dim_date.date_key"
                                )
                            with col_fk_c:
                                if st.button("➕", key=f"add_fk_{idx}"):
                                    if new_fk_col and new_fk_ref:
                                        if 'foreign_keys' not in table:
                                            table['foreign_keys'] = {}
                                        table['foreign_keys'][new_fk_col] = new_fk_ref
                                        st.rerun()
                        
                            # Display existing FKs
                            if 'foreign_keys' in table and table['foreign_keys']:
                                fks_to_delete = []
                                for fk_col, fk_ref in table['foreign_keys'].items():
                                    col_x, col_y, col_z = st.columns([2, 6, 1])
                                    with col_x:
                                        st.text(fk_col)
                                    with col_y:
                                        st.text(f"→ {fk_ref}")
                                    with col_z:
                                        if st.button("🗑️", key=f"del_fk_{idx}_{fk_col}"):
                                            fks_to_delete.append(fk_col)
                            
                                for fk_col in fks_to_delete:
                                    del table['foreign_keys'][fk_col]
                                    st.rerun()
                    
                        # Delete table button
                        if st.button(f"🗑️ Delete Table", key=f"del_table_{idx}", type="secondary"):
                            st.session_state.schema_data["schema"]["tables"].pop(idx)
                            st.rerun()

    # ============================================================================
    # TAB 2: NOTES
    # ============================================================================
    with tab2:
        st.header("📝 Schema Notes")
        st.info("Add important notes about your schema (SQL hints, date formats, best practices)")
        
        # Add new note
        col_note_a, col_note_b = st.columns([5, 1])
        with col_note_a:
            new_note = st.text_input(
                "New Note",
                placeholder="e.g., Always include LIMIT clause for large result sets",
                key="new_note_input"
            )
        with col_note_b:
            if st.button("➕ Add", key="add_note_btn", use_container_width=True):
                if new_note:
                    if 'notes' not in st.session_state.schema_data["schema"]:
                        st.session_state.schema_data["schema"]["notes"] = []
                    st.session_state.schema_data["schema"]["notes"].append(new_note)
                    st.rerun()
        
        # Display existing notes
        notes = st.session_state.schema_data["schema"].get("notes", [])
        if notes:
            st.subheader("Current Notes")
            notes_to_delete = []
            for idx, note in enumerate(notes):
                col_x, col_y = st.columns([6, 1])
                with col_x:
                    st.markdown(f"• {note}")
                with col_y:
                    if st.button("🗑️", key=f"del_note_{idx}"):
                        notes_to_delete.append(idx)
            
            for idx in reversed(notes_to_delete):
                st.session_state.schema_data["schema"]["notes"].pop(idx)
                st.rerun()
        else:
            st.warning("No notes yet. Add some hints for better SQL generation!")

    # ============================================================================
    # TAB 3: RELATIONSHIPS (only visible for multi-table schemas)
    # ============================================================================
    if tab3:  # Only render if tab exists (multi-table schema)
        with tab3:
            st.header("🔗 Table Relationships")
            st.info("Define JOIN relationships between tables")
        
        # Add new relationship
        with st.expander("➕ Add New Relationship", expanded=True):
            col_rel_a, col_rel_b = st.columns(2)
            with col_rel_a:
                rel_from = st.text_input(
                    "From (table.column)",
                    placeholder="fact_sales.date_key",
                    key="rel_from_input"
                )
            with col_rel_b:
                rel_to = st.text_input(
                    "To (table.column)",
                    placeholder="dim_date.date_key",
                    key="rel_to_input"
                )
            
            col_rel_c, col_rel_d = st.columns(2)
            with col_rel_c:
                rel_join_type = st.selectbox(
                    "Join Type",
                    options=["LEFT JOIN", "INNER JOIN", "RIGHT JOIN", "FULL OUTER JOIN"],
                    key="rel_join_type"
                )
            with col_rel_d:
                rel_description = st.text_input(
                    "Description",
                    placeholder="Links sales to date dimension",
                    key="rel_description"
                )
            
            if st.button("➕ Add Relationship", use_container_width=True):
                if rel_from and rel_to:
                    if 'relationships' not in st.session_state.schema_data["schema"]:
                        st.session_state.schema_data["schema"]["relationships"] = []
                    
                    st.session_state.schema_data["schema"]["relationships"].append({
                        "from": rel_from,
                        "to": rel_to,
                        "join_type": rel_join_type,
                        "description": rel_description
                    })
                    st.success("Relationship added!")
                    st.rerun()
        
        # Display existing relationships
        st.subheader("Defined Relationships")
        relationships = st.session_state.schema_data["schema"].get("relationships", [])
        
        if relationships:
            rels_to_delete = []
            for idx, rel in enumerate(relationships):
                col_x, col_y, col_z = st.columns([5, 4, 1])
                with col_x:
                    st.markdown(f"`{rel.get('from', '')}` → `{rel.get('to', '')}`")
                with col_y:
                    st.caption(f"{rel.get('join_type', 'LEFT JOIN')} | {rel.get('description', '')}")
                with col_z:
                    if st.button("🗑️", key=f"del_rel_{idx}"):
                        rels_to_delete.append(idx)
            
            for idx in reversed(rels_to_delete):
                st.session_state.schema_data["schema"]["relationships"].pop(idx)
                st.rerun()
        else:
            st.warning("No relationships defined yet.")
    
    # ============================================================================
    # TAB 4: SYNONYMS
    # ============================================================================
    with tab4:
        st.header("🔄 Synonyms")
        st.info("Map natural language terms to database columns (important for German/English support)")
        
        # Add new synonym
        with st.expander("➕ Add New Synonym", expanded=True):
            col_syn_a, col_syn_b = st.columns(2)
            with col_syn_a:
                syn_term = st.text_input(
                    "Term (natural language)",
                    placeholder="umsatz",
                    key="syn_term_input"
                )
            with col_syn_b:
                syn_column = st.text_input(
                    "Column",
                    placeholder="sales_amount",
                    key="syn_column_input"
                )
            
            col_syn_c, col_syn_d = st.columns(2)
            with col_syn_c:
                syn_table = st.text_input(
                    "Table",
                    placeholder="fact_sales",
                    key="syn_table_input"
                )
            with col_syn_d:
                syn_desc = st.text_input(
                    "Description",
                    placeholder="Gross sales amount",
                    key="syn_desc_input"
                )
            
            if st.button("➕ Add Synonym", use_container_width=True):
                if syn_term and syn_column and syn_table:
                    if 'synonyms' not in st.session_state.schema_data:
                        st.session_state.schema_data["synonyms"] = {}
                    
                    st.session_state.schema_data["synonyms"][syn_term.lower()] = {
                        "column": syn_column,
                        "table": syn_table,
                        "description": syn_desc
                    }
                    st.success(f"Synonym '{syn_term}' added!")
                    st.rerun()
        
        # Display existing synonyms
        st.subheader("Defined Synonyms")
        synonyms = st.session_state.schema_data.get("synonyms", {})
        
        if synonyms:
            syns_to_delete = []
            for term, details in synonyms.items():
                col_x, col_y, col_z = st.columns([2, 5, 1])
                with col_x:
                    st.markdown(f"**{term}**")
                with col_y:
                    st.caption(f"→ {details.get('table', '')}.{details.get('column', '')} ({details.get('description', '')})")
                with col_z:
                    if st.button("🗑️", key=f"del_syn_{term}"):
                        syns_to_delete.append(term)
            
            for term in syns_to_delete:
                del st.session_state.schema_data["synonyms"][term]
                st.rerun()
        else:
            st.warning("No synonyms defined yet. Add terms like 'umsatz' → 'sales_amount'")

    # ============================================================================
    # TAB 5: KPIs
    # ============================================================================
    with tab5:
        st.header("📈 KPIs (Key Performance Indicators)")
        st.info("Define common business calculations")
    
        # Add new KPI
        with st.expander("➕ Add New KPI", expanded=False):
            kpi_key = st.text_input("KPI Key", placeholder="net_sales", key="kpi_key_input")
            kpi_formula = st.text_input("Formula", placeholder="SUM(fact_sales.sales_amount - fact_sales.discount_amount)", key="kpi_formula_input")
            kpi_desc = st.text_input("Description", placeholder="Total sales after discounts", key="kpi_desc_input")
            kpi_group_by = st.text_input("Group By (optional)", placeholder="dim_store.store_name", key="kpi_groupby_input")
            kpi_tables = st.text_input("Required Tables (comma-separated)", placeholder="fact_sales, dim_store", key="kpi_tables_input")
            kpi_keywords = st.text_input("Keywords (comma-separated)", placeholder="nettoumsatz, netto, bereinigter umsatz", key="kpi_keywords_input")
        
            if st.button("Add KPI", key="add_kpi_btn"):
                if kpi_key and kpi_formula:
                    if 'kpis' not in st.session_state.schema_data:
                        st.session_state.schema_data["kpis"] = {}
                    
                    kpi_data = {
                        "formula": kpi_formula,
                        "description": kpi_desc,
                        "required_tables": [t.strip() for t in kpi_tables.split(",") if t.strip()],
                        "keywords": [k.strip() for k in kpi_keywords.split(",") if k.strip()]
                    }
                    if kpi_group_by:
                        kpi_data["group_by"] = kpi_group_by
                    
                    st.session_state.schema_data["kpis"][kpi_key] = kpi_data
                    st.success(f"KPI '{kpi_key}' added!")
                    st.rerun()
    
        # Display existing KPIs
        kpis = st.session_state.schema_data.get("kpis", {})
        if kpis:
            kpis_to_delete = []
            for key, value in kpis.items():
                with st.expander(f"**{key}**"):
                    st.code(value.get('formula', ''), language='sql')
                    st.markdown(f"**Description:** {value.get('description', '')}")
                    if value.get('group_by'):
                        st.markdown(f"**Group By:** {value.get('group_by')}")
                    st.markdown(f"**Tables:** {', '.join(value.get('required_tables', []))}")
                    st.markdown(f"**Keywords:** {', '.join(value.get('keywords', []))}")
                
                    if st.button(f"🗑️ Delete", key=f"del_kpi_{key}"):
                        kpis_to_delete.append(key)
        
            for key in kpis_to_delete:
                del st.session_state.schema_data["kpis"][key]
                st.rerun()
        else:
            st.info("No KPIs defined yet. Add common business calculations!")

    # ============================================================================
    # TAB 6: EXAMPLES
    # ============================================================================
    with tab6:
        st.header("💡 SQL Examples")
        st.info("Provide example queries to help the LLM understand your schema")
    
        # Add new example
        with st.expander("➕ Add New Example", expanded=False):
            example_desc = st.text_input("Description", placeholder="Monthly sales by region", key="example_desc_input")
            example_sql = st.text_area("SQL Pattern", placeholder="SELECT ... FROM ... WHERE ...", height=100, key="example_sql_input")
        
            if st.button("Add Example", key="add_example_btn"):
                if example_desc and example_sql:
                    if 'examples' not in st.session_state.schema_data:
                        st.session_state.schema_data["examples"] = []
                
                    st.session_state.schema_data["examples"].append({
                        "description": example_desc,
                        "pattern": example_sql
                    })
                    st.success("Example added!")
                    st.rerun()
    
        # Display existing examples
        examples = st.session_state.schema_data.get("examples", [])
        if examples:
            examples_to_delete = []
            for idx, example in enumerate(examples):
                with st.expander(f"**{example['description']}**"):
                    st.code(example['pattern'], language='sql')
                
                    if st.button(f"🗑️ Delete", key=f"del_example_{idx}"):
                        examples_to_delete.append(idx)
        
            for idx in reversed(examples_to_delete):
                st.session_state.schema_data["examples"].pop(idx)
                st.rerun()
        else:
            st.info("No examples yet. Add SQL patterns to help with query generation!")

    # ============================================================================
    # TAB 7: GLOSSARY
    # ============================================================================
    with tab7:
        st.header("📖 Glossary")
        st.info("Define business terms and their meanings")
    
        # Add new term
        col_a, col_b, col_c = st.columns([2, 5, 1])
        with col_a:
            new_term = st.text_input("Term", placeholder="net_sales", key="glossary_term_input")
        with col_b:
            new_definition = st.text_input("Definition", placeholder="Sales after discounts and returns", key="glossary_def_input")
        with col_c:
            if st.button("➕ Add", key="add_glossary_btn"):
                if new_term and new_definition:
                    if 'glossary' not in st.session_state.schema_data:
                        st.session_state.schema_data["glossary"] = {}
                
                    st.session_state.schema_data["glossary"][new_term] = new_definition
                    st.rerun()
    
        # Display existing terms
        glossary = st.session_state.schema_data.get("glossary", {})
        if glossary:
            terms_to_delete = []
            for term, definition in glossary.items():
                col_x, col_y, col_z = st.columns([2, 6, 1])
                with col_x:
                    st.markdown(f"**{term}**")
                with col_y:
                    st.text(definition)
                with col_z:
                    if st.button("🗑️", key=f"del_term_{term}"):
                        terms_to_delete.append(term)
        
            for term in terms_to_delete:
                del st.session_state.schema_data["glossary"][term]
                st.rerun()
        else:
            st.info("No glossary terms yet. Define business terms!")

    # ============================================================================
    # TAB 8: TEST SQL
    # ============================================================================
    with tab8:
        st.header("🧪 Test Your Schema with SQL Generation")
        st.info("Select a schema from S3 and ask questions to generate SQL")
    
        # Step 1: Upload Current Schema to S3 (optional, if tables exist)
        if st.session_state.schema_data["schema"]["tables"]:
            st.markdown("### 1️⃣ Upload Current Schema to S3 (Optional)")
        
            col_upload_a, col_upload_b = st.columns([2, 1])
        
            with col_upload_a:
                upload_schema_name = st.text_input(
                    "Schema Name for Upload",
                    value=schema_name,
                    key="upload_schema_name"
                )
                st.caption("Upload your current schema to S3 for testing")
        
            with col_upload_b:
                if st.button("☁️ Upload to S3", use_container_width=True, type="secondary"):
                    username = st.session_state.username or "raedmokdad"
                
                    with st.spinner("Uploading to S3..."):
                        success = upload_schema_to_s3(
                            st.session_state.schema_data, 
                            upload_schema_name, 
                            username
                        )
                    
                        if success:
                            st.session_state['uploaded_schema'] = upload_schema_name
                            st.session_state['uploaded_username'] = username
                            st.success(f"✅ Schema '{upload_schema_name}' uploaded!")
            
            st.markdown("---")
        
        # Step 2: Select Schema from S3
        try:
            from src.s3_service import list_user_schema
            
            username = st.session_state.username or "raedmokdad"
            
            col_list_a, col_list_b = st.columns([3, 1])
            
            with col_list_b:
                if st.button("🔄 Refresh", use_container_width=True, key="refresh_test_schemas"):
                    st.rerun()
            
            with col_list_a:
                with st.spinner("Loading from S3..."):
                    success, schemas = list_user_schema(username)
                    
                    if success and schemas:
                        selected_schema_name = st.selectbox(
                            "📋 Your Schemas on S3:",
                            options=schemas,
                            index=schemas.index(st.session_state.get('selected_test_schema', schemas[0])) 
                                if st.session_state.get('selected_test_schema') in schemas else 0,
                            help="Select a schema to test",
                            key="s3_test_schema_select"
                        )
                        
                        # Automatically set the selected schema (no button needed)
                        st.session_state['selected_test_schema'] = selected_schema_name
                        st.success(f"✅ Using Schema: **{selected_schema_name}**")
                    
                    elif success:
                        st.info(f"No schemas found on S3 for user '{username}'. Upload a schema first in the Tables tab!")
                    else:
                        st.error("Error loading schemas from S3")
        
        except Exception as e:
            st.error(f"Error accessing S3: {str(e)}")
            st.info("💡 Make sure AWS credentials are configured in .env file")
        
        st.markdown("---")
        
        # Step 3: Ask Questions
        if st.session_state.get('selected_test_schema'):
            st.markdown("### 2️⃣ Ask Questions")
            st.success(f"📋 Selected Schema: **{st.session_state['selected_test_schema']}**")
            
            # API Health Check
            col_health_a, col_health_b = st.columns([3, 1])
            
            with col_health_b:
                try:
                    response = requests.get(f"{API_URL}/health", timeout=5)
                    if response.status_code == 200:
                        st.success("✅ API Online")
                    else:
                        st.error("❌ API Offline")
                except:
                    st.error("❌ API Offline")
                    st.caption("Start: `uvicorn api_service:app --port 8000`")
            
            # Configuration
            with st.expander("⚙️ Advanced Settings"):
                col_conf_a, col_conf_b = st.columns(2)
                with col_conf_a:
                    confidence_threshold = st.slider(
                        "Confidence Threshold",
                        min_value=0.0,
                        max_value=1.0,
                        value=0.7,
                        step=0.05
                    )
                with col_conf_b:
                    max_retries = st.number_input(
                        "Max Retries",
                        min_value=1,
                        max_value=5,
                        value=2
                    )
            
            # Question Input
            test_question = st.text_area(
                "Your Question (German or English):",
                value=st.session_state.get('test_question', ''),
                height=100,
                placeholder="z.B.: Wie viel Umsatz hatte Store Hamburg im Januar 2023?",
                key="question_input"
            )
            
            # Generate SQL Button
            if st.button("🚀 Generate SQL", type="primary", use_container_width=True):
                if test_question:
                    with st.spinner("Generating SQL..."):
                        try:
                            username = st.session_state.username or "raedmokdad"
                            selected_schema = st.session_state['selected_test_schema']
                            
                            response = requests.post(
                                f"{API_URL}/generate-sql",
                                json={
                                    "question": test_question,
                                    "max_retries": max_retries,
                                    "confidence_threshold": confidence_threshold,
                                    "schema_name": selected_schema,
                                    "username": username
                                },
                                timeout=30
                            )
                            
                            if response.status_code == 200:
                                result = response.json()
                                
                                # Display Results
                                st.success("✅ SQL Generated Successfully!")
                                
                                # Metrics
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    confidence = result.get('confidence', 0)
                                    st.metric("Confidence", f"{confidence:.0%}")
                                with col2:
                                    validation = result.get('validation_passed', True)
                                    st.metric("Validation", "✅ Passed" if validation else "❌ Failed")
                                with col3:
                                    processing_time = result.get('processing_time', 0)
                                    st.metric("Time", f"{processing_time:.2f}s")
                                
                                # SQL Query
                                st.markdown("### 📝 Generated SQL:")
                                sql_query = result.get('sql_query', '')
                                st.code(sql_query, language='sql')
                                
                                # Download Button
                                st.download_button(
                                    label="📥 Download SQL",
                                    data=sql_query,
                                    file_name=f"query_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql",
                                    mime="text/plain"
                                )
                                
                                # Schema Info
                                with st.expander("ℹ️ Schema Information"):
                                    st.markdown(f"**Schema Used:** {selected_schema}")
                                    st.markdown(f"**Username:** {username}")
                                    tables = st.session_state.schema_data["schema"]["tables"]
                                    table_names = [t['name'] for t in tables]
                                    st.markdown(f"**Tables:** {', '.join(table_names)}")
                            
                            else:
                                st.error(f"❌ Error {response.status_code}: {response.text}")
                        
                        except requests.exceptions.Timeout:
                            st.error("❌ Request timeout. Please try again.")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                            
                            # Troubleshooting
                            with st.expander("🔧 Troubleshooting"):
                                st.markdown("""
                                **Common Issues:**
                                1. API not running: `uvicorn api_service:app --port 8000`
                                2. Schema not on S3: Upload schema in Step 1
                                3. AWS credentials missing: Check `.env` file
                                4. Wrong schema name: Verify in Step 2
                                """)
                else:
                    st.warning("⚠️ Please enter a question")
        else:
            st.info("👆 Please select a schema from S3 first using Step 1")
        
        st.markdown("---")
        
        # Schema Validation (always visible)
        st.markdown("### 4️⃣ Schema Validation")
        
        col_val_a, col_val_b = st.columns(2)
        
        tables = st.session_state.schema_data["schema"]["tables"]
        
        with col_val_a:
            st.markdown("**✅ Schema Checklist:**")
            
            checks = []
            checks.append(("At least 1 fact table", any(t['role'] == 'fact' for t in tables)))
            checks.append(("At least 1 dimension table", any(t['role'] == 'dimension' for t in tables)))
            
            fact_tables_with_fks = [t for t in tables if t['role'] == 'fact' and t.get('foreign_keys')]
            checks.append(("Fact tables have foreign keys", len(fact_tables_with_fks) > 0))
            
            checks.append(("Metrics defined", len(st.session_state.schema_data['schema'].get('metrics', {})) > 0))
            checks.append(("Examples provided", len(st.session_state.schema_data['schema'].get('examples', [])) > 0))
            
            for check_name, passed in checks:
                icon = "✅" if passed else "❌"
                st.markdown(f"{icon} {check_name}")
        
        with col_val_b:
            st.markdown("**📊 Schema Statistics:**")
            st.metric("Total Tables", len(tables))
            st.metric("Fact Tables", len([t for t in tables if t['role'] == 'fact']))
            st.metric("Dimension Tables", len([t for t in tables if t['role'] == 'dimension']))
            
            total_columns = sum(len(t.get('columns', {})) for t in tables)
            st.metric("Total Columns", total_columns)

    # ============================================================================
    # SCHEMA BUILDER: JSON PREVIEW
    # ============================================================================
    st.markdown("---")
    st.subheader("📄 JSON Preview")
    with st.expander("View Raw JSON", expanded=False):
        st.json(st.session_state.schema_data)

# ============================================================================
# DATABASE QUERY MODUS: MAIN CONTENT
# ============================================================================
else:  # app_mode == "🔍 Database Query"
    
    connector = get_connector()
    
    if connector is None:
        st.info("👆 Please configure and connect to a data source in the sidebar first.")
    else:
        # Database Query Tabs - nur noch 2 Tabs
        tab_explorer, tab_playground = st.tabs([
            "🗂️ Schema Explorer", 
            "💻 SQL Playground"
        ])
        
        # ============================================================================
        # TAB: SCHEMA EXPLORER
        # ============================================================================
        with tab_explorer:
            st.subheader("Schema Explorer")

            tables = connector.list_tables()
            if not tables:
                st.warning("No tables available.")
            else:
                table_name = st.selectbox("Select a table", tables)
                schema = connector.get_table_schema(table_name)
                st.write(f"Schema for **{table_name}**")
                st.dataframe(schema)

        # ============================================================================
        # TAB: SQL PLAYGROUND (mit Natural Language Integration)
        # ============================================================================
        with tab_playground:
            st.subheader("💻 SQL Playground")
            
            # Input Mode Selector
            input_mode = st.radio(
                "Input Mode:",
                ["📝 SQL", "🤖 Natural Language"],
                horizontal=True,
                key="playground_input_mode"
            )
            
            tables = connector.list_tables()
            default_sql = f"SELECT * FROM {tables[0]} LIMIT 10;" if tables else ""
            
            # ============================================
            # SQL MODE
            # ============================================
            if input_mode == "📝 SQL":
                user_sql = st.text_area(
                    "Enter SQL query:",
                    value=st.session_state.get("current_sql", default_sql),
                    height=160,
                    key="sql_input",
                )
                
                run_clicked = st.button("▶️ Run Query", type="primary")
                
                if run_clicked:
                    lowered = user_sql.strip().lower()
                    try:
                        if lowered.startswith("select"):
                            rows = connector.run_query(user_sql)
                            df = pd.DataFrame(rows)
                            st.session_state["last_df"] = df
                            st.session_state["last_sql"] = user_sql
                            st.session_state["last_msg"] = f"✅ Returned {len(df)} rows"
                        else:
                            connector.execute(user_sql)
                            st.session_state["last_df"] = None
                            st.session_state["last_sql"] = user_sql
                            st.session_state["last_msg"] = "✅ Statement executed successfully."
                    except Exception as e:
                        st.session_state["last_df"] = None
                        st.session_state["last_sql"] = user_sql
                        st.session_state["last_msg"] = f"❌ Error: {e}"
            
            # ============================================
            # NATURAL LANGUAGE MODE
            # ============================================
            else:  # Natural Language Mode
                selected_schema = st.session_state.get('db_query_schema')
                
                if not selected_schema:
                    st.warning("⚠️ Please select a schema in the sidebar (🤖 AI Query Schema section) to use Natural Language mode")
                else:
                    st.success(f"📚 Using schema: **{selected_schema}**")
                    
                    user_question = st.text_area(
                        "Ask your question in natural language:",
                        placeholder="Example: What were the total sales by product category last month?",
                        height=100,
                        key="nl_question_input"
                    )
                    
                    col_gen, col_info = st.columns([1, 3])
                    with col_gen:
                        generate_clicked = st.button("🚀 Generate SQL", type="primary", use_container_width=True)
                    with col_info:
                        st.caption("💡 Tip: You can ask questions in German or English")
                    
                    if generate_clicked and user_question:
                        with st.spinner("🤖 Generating SQL from your question..."):
                            try:
                                username = st.session_state.get('username', 'raedmokdad')
                                
                                # Get actual table names from connector
                                table_names = None
                                if st.session_state.get('connector'):
                                    try:
                                        table_names = st.session_state['connector'].list_tables()
                                    except:
                                        pass
                                
                                payload = {
                                    "question": user_question,
                                    "schema_name": selected_schema,
                                    "username": username,
                                    "table_names": table_names
                                }
                                
                                response = requests.post(f"{API_URL}/generate-sql", json=payload, timeout=30)
                                
                                if response.status_code == 200:
                                    result = response.json()
                                    
                                    # Store results in session state
                                    st.session_state["nl_confidence"] = result.get('confidence', 0)
                                    st.session_state["nl_validation"] = result.get('validation_passed', True)
                                    st.session_state["nl_processing_time"] = result.get('processing_time', 0)
                                    st.session_state["generated_sql"] = result.get('sql_query', '')
                                    st.session_state["nl_generated"] = True
                                    st.rerun()
                                
                                else:
                                    st.error(f"❌ API Error {response.status_code}: {response.text}")
                            
                            except requests.exceptions.Timeout:
                                st.error("❌ Request timeout. Please check if the API is running.")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                                st.info("💡 Make sure the API server is running: `uvicorn api_service:app --port 8000`")
                    
                    elif generate_clicked:
                        st.warning("⚠️ Please enter a question first")
                    
                    # Display generated SQL and metrics (persistent)
                    if st.session_state.get("nl_generated") and st.session_state.get("generated_sql"):
                        st.markdown("---")
                        
                        # Display Metrics
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            confidence = st.session_state.get('nl_confidence', 0)
                            st.metric("Confidence", f"{confidence:.0%}")
                        with col2:
                            validation = st.session_state.get('nl_validation', True)
                            st.metric("Validation", "✅ Passed" if validation else "❌ Failed")
                        with col3:
                            processing_time = st.session_state.get('nl_processing_time', 0)
                            st.metric("Time", f"{processing_time:.2f}s")
                        
                        # Generated SQL
                        generated_sql = st.session_state.get("generated_sql", "")
                        st.markdown("### Generated SQL:")
                        st.code(generated_sql, language='sql')
                        
                        # Run Query Button (same as SQL mode)
                        run_nl_query = st.button("▶️ Run Query", type="primary", key="run_nl_query")
                        
                        if run_nl_query:
                            try:
                                lowered = generated_sql.strip().lower()
                                if lowered.startswith("select"):
                                    rows = connector.run_query(generated_sql)
                                    df = pd.DataFrame(rows)
                                    st.session_state["last_df"] = df
                                    st.session_state["last_sql"] = generated_sql
                                    st.session_state["last_msg"] = f"✅ Returned {len(df)} rows"
                                else:
                                    connector.execute(generated_sql)
                                    st.session_state["last_df"] = None
                                    st.session_state["last_sql"] = generated_sql
                                    st.session_state["last_msg"] = "✅ Statement executed successfully."
                            except Exception as e:
                                st.session_state["last_df"] = None
                                st.session_state["last_sql"] = generated_sql
                                st.session_state["last_msg"] = f"❌ Error: {e}"
            
            # ============================================
            # RESULTS DISPLAY (Both Modes)
            # ============================================
            st.markdown("---")
            
            # Display last message
            last_msg = st.session_state.get("last_msg")
            if last_msg:
                if last_msg.startswith("✅"):
                    st.success(last_msg)
                elif last_msg.startswith("❌"):
                    st.error(last_msg)
                else:
                    st.info(last_msg)
            
            # Display DataFrame if available
            df = st.session_state.get("last_df")
            
            if isinstance(df, pd.DataFrame) and not df.empty:
                st.dataframe(df, use_container_width=True)
                
                # Visualization
                with st.expander("📊 Visualize Results"):
                    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                    all_cols = df.columns.tolist()
                    
                    if not numeric_cols:
                        st.warning("No numeric columns available for visualization.")
                    else:
                        chart_type = st.selectbox(
                            "Chart type",
                            ["Bar", "Line", "Area", "Pie", "Donut"],
                            key="result_chart_type"
                        )
                        
                        x_col = st.selectbox("X axis", options=all_cols, key="result_x_axis")
                        y_col = st.selectbox("Y axis (numeric)", options=numeric_cols, key="result_y_axis")
                        
                        if x_col != y_col:
                            if chart_type == "Line":
                                st.line_chart(df, x=x_col, y=y_col)
                            elif chart_type == "Bar":
                                st.bar_chart(df, x=x_col, y=y_col)
                            elif chart_type == "Area":
                                st.area_chart(df, x=x_col, y=y_col)
                            elif chart_type in ["Pie", "Donut"]:
                                agg_df = df.groupby(x_col)[y_col].sum().reset_index()
                                inner_radius = 70 if chart_type == "Donut" else 0
                                chart = (
                                    alt.Chart(agg_df)
                                    .mark_arc(innerRadius=inner_radius)
                                    .encode(
                                        theta=f"{y_col}:Q",
                                        color=f"{x_col}:N",
                                        tooltip=[x_col, y_col]
                                    )
                                    .properties(width=400, height=400)
                                )
                                st.altair_chart(chart, use_container_width=False)
                        else:
                            st.warning("X axis and Y axis must be different columns.")


