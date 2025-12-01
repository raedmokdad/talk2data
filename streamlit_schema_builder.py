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
import os
from pathlib import Path
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
    st.warning("⚠️ Authentication module not available. Running in demo mode.")

# Initialize session state
if 'schema_data' not in st.session_state:
    st.session_state.schema_data = {
        "schema": {
            "tables": [],
            "relationships": [],
            "metrics": {},
            "examples": [],
            "glossary": {}
        }
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
        API_URL = "http://localhost:8000"
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
        
        st.markdown("---")
        st.info("💡 **Demo Mode**: You can also skip login and use the builder without authentication.")


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
    col1, col2 = st.columns([3, 1])
    with col1:
        show_login_page()
    with col2:
        st.markdown("### Quick Start")
        if st.button("🚀 Skip Login (Demo Mode)", use_container_width=True):
            st.session_state.authenticated = True
            st.session_state.username = "raedmokdad"  # Fixed: Match S3 username
            st.rerun()
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


# --- Sidebar: Data source selection ---
st.sidebar.header("1. Data Source")

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
if st.sidebar.button("Connect"):
    try:
        selection = DBSelection(**selection_kwargs)
        connector = create_connector(selection)
        st.session_state["connector"] = connector
        st.success("✅ Connected successfully!")
        st.write("Available tables:", ", ".join(connector.list_tables()))
    except Exception as e:
        st.error(f"❌ Connection failed: {e}")

connector = get_connector()                

# ============================================================================
# MAIN CONTENT TABS
# ============================================================================

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Tables", 
    "🔗 Relationships", 
    "📈 Metrics", 
    "💡 Examples", 
    "📖 Glossary",
    "🧪 Test SQL",
    "🗂️ Schema Explorer", 
    "💻 SQL Playground"
])

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
# TAB 2: RELATIONSHIPS
# ============================================================================
with tab2:
    st.header("🔗 Table Relationships")
    st.info("Relationships are auto-generated from foreign keys, but you can add custom notes here")
    
    # Display auto-detected relationships
    st.subheader("Auto-Detected Relationships")
    relationships = []
    for table in st.session_state.schema_data["schema"]["tables"]:
        if table['role'] == 'fact' and 'foreign_keys' in table:
            for fk_col, fk_ref in table['foreign_keys'].items():
                relationships.append({
                    "from": f"{table['name']}.{fk_col}",
                    "to": fk_ref,
                    "type": "many-to-one"
                })
    
    if relationships:
        for rel in relationships:
            st.markdown(f"- `{rel['from']}` → `{rel['to']}` ({rel['type']})")
    else:
        st.warning("No relationships found. Add foreign keys in the Tables tab.")

# ============================================================================
# TAB 3: METRICS
# ============================================================================
with tab3:
    st.header("📈 Predefined Metrics")
    st.info("Define common calculations for your schema")
    
    # Add new metric
    with st.expander("➕ Add New Metric", expanded=False):
        metric_key = st.text_input("Metric Key", placeholder="total_revenue")
        metric_formula = st.text_input("Formula", placeholder="SUM(fact_sales.sales_amount)")
        metric_desc = st.text_input("Description", placeholder="Total revenue across all sales")
        metric_tables = st.text_input("Required Tables (comma-separated)", placeholder="fact_sales, dim_date")
        metric_keywords = st.text_input("Keywords (comma-separated)", placeholder="umsatz, revenue, total")
        
        if st.button("Add Metric"):
            if metric_key and metric_formula:
                if 'metrics' not in st.session_state.schema_data["schema"]:
                    st.session_state.schema_data["schema"]["metrics"] = {}
                
                st.session_state.schema_data["schema"]["metrics"][metric_key] = {
                    "formula": metric_formula,
                    "description": metric_desc,
                    "required_tables": [t.strip() for t in metric_tables.split(",") if t.strip()],
                    "keywords": [k.strip() for k in metric_keywords.split(",") if k.strip()]
                }
                st.success(f"Metric '{metric_key}' added!")
                st.rerun()
    
    # Display existing metrics
    metrics = st.session_state.schema_data["schema"].get("metrics", {})
    if metrics:
        metrics_to_delete = []
        for key, value in metrics.items():
            with st.expander(f"**{key}**"):
                st.code(value.get('formula', ''), language='sql')
                st.markdown(f"**Description:** {value.get('description', '')}")
                st.markdown(f"**Tables:** {', '.join(value.get('required_tables', []))}")
                st.markdown(f"**Keywords:** {', '.join(value.get('keywords', []))}")
                
                if st.button(f"🗑️ Delete", key=f"del_metric_{key}"):
                    metrics_to_delete.append(key)
        
        for key in metrics_to_delete:
            del st.session_state.schema_data["schema"]["metrics"][key]
            st.rerun()

# ============================================================================
# TAB 4: EXAMPLES
# ============================================================================
with tab4:
    st.header("💡 SQL Examples")
    st.info("Provide example queries to help the LLM understand your schema")
    
    # Add new example
    with st.expander("➕ Add New Example", expanded=False):
        example_desc = st.text_input("Description", placeholder="Monthly sales by region")
        example_sql = st.text_area("SQL Pattern", placeholder="SELECT ... FROM ... WHERE ...", height=100)
        
        if st.button("Add Example"):
            if example_desc and example_sql:
                if 'examples' not in st.session_state.schema_data["schema"]:
                    st.session_state.schema_data["schema"]["examples"] = []
                
                st.session_state.schema_data["schema"]["examples"].append({
                    "description": example_desc,
                    "pattern": example_sql
                })
                st.success("Example added!")
                st.rerun()
    
    # Display existing examples
    examples = st.session_state.schema_data["schema"].get("examples", [])
    if examples:
        examples_to_delete = []
        for idx, example in enumerate(examples):
            with st.expander(f"**{example['description']}**"):
                st.code(example['pattern'], language='sql')
                
                if st.button(f"🗑️ Delete", key=f"del_example_{idx}"):
                    examples_to_delete.append(idx)
        
        for idx in reversed(examples_to_delete):
            st.session_state.schema_data["schema"]["examples"].pop(idx)
            st.rerun()

# ============================================================================
# TAB 5: GLOSSARY
# ============================================================================
with tab5:
    st.header("📖 Glossary")
    st.info("Define business terms and their meanings")
    
    # Add new term
    col_a, col_b, col_c = st.columns([2, 5, 1])
    with col_a:
        new_term = st.text_input("Term", placeholder="net_sales")
    with col_b:
        new_definition = st.text_input("Definition", placeholder="Sales after discounts and returns")
    with col_c:
        if st.button("➕ Add"):
            if new_term and new_definition:
                if 'glossary' not in st.session_state.schema_data["schema"]:
                    st.session_state.schema_data["schema"]["glossary"] = {}
                
                st.session_state.schema_data["schema"]["glossary"][new_term] = new_definition
                st.rerun()
    
    # Display existing terms
    glossary = st.session_state.schema_data["schema"].get("glossary", {})
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
            del st.session_state.schema_data["schema"]["glossary"][term]
            st.rerun()

# ============================================================================
# TAB 6: TEST SQL
# ============================================================================
with tab6:
    st.header("🧪 Test Your Schema with SQL Generation")
    st.info("Upload schema to S3, select it, and ask questions to generate SQL")
    
    if not st.session_state.schema_data["schema"]["tables"]:
        st.warning("⚠️ No tables defined. Add tables first in the Tables tab.")
    else:
        # Step 1: Upload Schema to S3
        st.markdown("### 1️⃣ Upload Schema to S3")
        
        col_upload_a, col_upload_b = st.columns([2, 1])
        
        with col_upload_a:
            upload_schema_name = st.text_input(
                "Schema Name for Upload",
                value=schema_name,
                key="upload_schema_name"
            )
            st.caption("This will be saved on S3 for testing")
        
        with col_upload_b:
            if st.button("☁️ Upload to S3 for Testing", use_container_width=True, type="primary"):
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
        
        st.markdown("---")
        
        # Step 2: Select Schema from S3 (or use current)
        st.markdown("### 2️⃣ Select Schema for Testing")
        
        tab_current, tab_s3 = st.tabs(["📄 Current Schema", "☁️ S3 Schemas"])
        
        with tab_current:
            st.info(f"**Current Schema:** {schema_name}")
            st.caption("This is the schema you're currently editing")
            
            if st.button("✅ Use Current Schema", use_container_width=True, type="primary"):
                # Save current schema to S3 first
                username = st.session_state.username or "raedmokdad"
                
                with st.spinner("Uploading current schema to S3..."):
                    success = upload_schema_to_s3(
                        st.session_state.schema_data, 
                        schema_name, 
                        username
                    )
                    
                    if success:
                        st.session_state['selected_test_schema'] = schema_name
                        st.success(f"✅ Using: **{schema_name}**")
        
        with tab_s3:
            try:
                from src.s3_service import list_user_schema
                
                username = st.session_state.username or "raedmokdad"
                
                # Debug info
                st.caption(f"🔍 Loading schemas for user: **{username}**")
                
                col_list_a, col_list_b = st.columns([3, 1])
                
                with col_list_b:
                    if st.button("🔄 Refresh", use_container_width=True, key="refresh_test_schemas"):
                        st.rerun()
                
                with col_list_a:
                    with st.spinner("Loading from S3..."):
                        success, schemas = list_user_schema(username)
                        
                        # More debug info
                        st.caption(f"📊 Result: Success={success}, Found={len(schemas) if schemas else 0} schemas")
                        
                        if success and schemas:
                            selected_schema_name = st.selectbox(
                                "📋 Your Schemas on S3:",
                                options=schemas,
                                index=schemas.index(st.session_state.get('selected_test_schema', schemas[0])) 
                                    if st.session_state.get('selected_test_schema') in schemas else 0,
                                help="Select a schema to test",
                                key="s3_test_schema_select"
                            )
                            
                            if st.button("✅ Use Selected", use_container_width=True, key="use_selected_test"):
                                st.session_state['selected_test_schema'] = selected_schema_name
                                st.success(f"✅ Using: **{selected_schema_name}**")
                            
                        elif success:
                            st.info(f"No schemas found on S3 for user '{username}'. Upload a schema first!")
                        else:
                            st.error("Error loading schemas from S3")
            
            except Exception as e:
                st.error(f"Error accessing S3: {str(e)}")
                st.info("💡 Make sure AWS credentials are configured in .env file")
        
        st.markdown("---")
        
        # Step 3: Ask Questions
        if st.session_state.get('selected_test_schema'):
            st.markdown("### 3️⃣ Ask Questions")
            
            # API Health Check
            col_health_a, col_health_b = st.columns([3, 1])
            
            with col_health_b:
                try:
                    API_URL = "http://localhost:8000"
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
            
            # Example Questions
            st.markdown("**💡 Quick Examples:**")
            
            example_questions = [
                "Wie viel Umsatz insgesamt?",
                "Top 10 Produkte nach Umsatz",
                "Umsatz pro Store in 2023",
                "Durchschnittlicher Umsatz pro Tag"
            ]
            
            col_ex1, col_ex2, col_ex3, col_ex4 = st.columns(4)
            
            for idx, (col, question) in enumerate(zip([col_ex1, col_ex2, col_ex3, col_ex4], example_questions)):
                with col:
                    if st.button(question, key=f"example_{idx}", use_container_width=True):
                        st.session_state['test_question'] = question
            
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
                            API_URL = "http://localhost:8000"
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
                    st.warning("Please enter a question")
        
        else:
            st.info("👆 Please upload and select a schema first")
        
        st.markdown("---")
        
        # Schema Validation
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



if connector is not None:
     
    with tab7:
        st.subheader("Schema Explorer")

        tables = connector.list_tables()
        if not tables:
            st.warning("No tables available.")
        else:
            table_name = st.selectbox("Select a table", tables)
            schema = connector.get_table_schema(table_name)
            st.write(f"Schema for **{table_name}**")
            st.dataframe(schema)

    with tab8:
            
            st.subheader("SQL Playground")

            default_sql = ""
            tables = connector.list_tables()
            if tables:
                default_sql = f"SELECT * FROM {tables[0]} LIMIT 10;"

            user_sql = st.text_area(
                "Enter SQL query",
                value=default_sql,
                height=160,
                key="sql_input",
            )

            run_clicked = st.button("Run query")

            # --- 1) Run the query and store result in session_state ---
            if run_clicked:
                lowered = user_sql.strip().lower()
                try:
                    if lowered.startswith("select"):
                        rows = connector.run_query(user_sql)
                        df = pd.DataFrame(rows)
                        st.session_state["last_df"] = df
                        st.session_state["last_sql"] = user_sql
                        st.session_state["last_msg"] = f"Returned {len(df)} rows"
                    else:
                        connector.execute(user_sql)
                        st.session_state["last_df"] = None
                        st.session_state["last_sql"] = user_sql
                        st.session_state["last_msg"] = "✅ Statement executed successfully."
                except Exception as e:
                    st.session_state["last_df"] = None
                    st.session_state["last_sql"] = user_sql
                    st.session_state["last_msg"] = f"❌ Error: {e}"

            # --- 2) Always display last result + charts (independent of button) ---
            last_msg = st.session_state.get("last_msg")
            if last_msg:
                st.write(last_msg)

            df = st.session_state.get("last_df")

            if isinstance(df, pd.DataFrame) and not df.empty:
                st.dataframe(df)

                with st.expander("📊 Visualize this result"):
                    # Detect numeric columns for Y axis
                    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
                    all_cols = df.columns.tolist()

                    chart_type = st.selectbox(
                        "Chart type",
                        ["Line", "Bar", "Area", "Pie", "Donut", "Funnel"],
                        index=0,
                        key="chart_type_selector",
                    )

                    x_col = st.selectbox(
                        "X axis",
                        options=all_cols,
                        key="x_axis_selector",
                    )

                    y_col = st.selectbox(
                        "Y axis (numeric)",
                        options=numeric_cols,
                        index=0 if numeric_cols else None,
                        key="y_axis_selector",
                    )

                    if not numeric_cols:
                        st.warning("No numeric columns available for Y axis.")
                    elif x_col == y_col:
                        st.warning("X axis and Y axis must be different columns.")
                    else:
                    
                        if chart_type == "Line":
                            st.line_chart(df, x=x_col, y=y_col)
                        elif chart_type == "Bar":
                            st.bar_chart(df, x=x_col, y=y_col)
                        elif chart_type == "Donut":
                            # Donut charts need categorical x and a numeric y (aggregated)
                            if not numeric_cols:
                                st.warning("No numeric column available for Donut chart.")
                            else:
                                st.write(f"Showing Donut chart for **{y_col}** grouped by **{x_col}**")

                                # Aggregate data for donut
                                donut_df = df.groupby(x_col)[y_col].sum().reset_index()

                                donut_chart = (
                                    alt.Chart(donut_df)
                                    .mark_arc(innerRadius=70)  # innerRadius > 0 → donut
                                    .encode(
                                        theta=f"{y_col}:Q",
                                        color=f"{x_col}:N",
                                        tooltip=[x_col, y_col],
                                    )
                                    .properties(width=350, height=350)
                                )

                                st.altair_chart(donut_chart, use_container_width=False)    
                        elif chart_type == "Pie":
                            if not numeric_cols:
                                st.warning("No numeric column available for Pie chart.")
                            else:
                                st.write(f"Showing Pie chart for **{y_col}** grouped by **{x_col}**")

                                # Prepare data for Pie: group by x_col
                                pie_df = df.groupby(x_col)[y_col].sum().reset_index()

                                pie_chart = (
                                    alt.Chart(pie_df)
                                    .mark_arc()     # pie chart (no inner radius)
                                    .encode(
                                        theta=f"{y_col}:Q",
                                        color=f"{x_col}:N",
                                        tooltip=[x_col, y_col],
                                    )
                                    .properties(width=350, height=350)
                                )

                                st.altair_chart(pie_chart, use_container_width=False)    
                        elif chart_type == "Funnel":
                            if not numeric_cols:
                                st.warning("No numeric column available for Funnel chart.")
                            else:
                                st.write(f"Showing Funnel chart for **{y_col}** by **{x_col}**")

                                # Aggregate by stage (x_col)
                                funnel_df = df.groupby(x_col)[y_col].sum().reset_index()

                                # Sort from largest to smallest (typical funnel)
                                funnel_df = funnel_df.sort_values(by=y_col, ascending=False)

                                funnel_chart = (
                                    alt.Chart(funnel_df)
                                    .mark_bar()
                                    .encode(
                                        x=alt.X(f"{y_col}:Q", title=y_col),
                                        y=alt.Y(f"{x_col}:N",
                                                sort=funnel_df[x_col].tolist(),  # keep our sorted order
                                                title=x_col),
                                        tooltip=[x_col, y_col],
                                    )
                                    .properties(
                                        width=500,
                                        height=300,
                                    )
                                )

                                st.altair_chart(funnel_chart, use_container_width=True)  
                        
                        else:  # Area
                            st.area_chart(df, x=x_col, y=y_col)


# ============================================================================
# JSON PREVIEW
# ============================================================================
st.markdown("---")
st.subheader("📄 JSON Preview")
with st.expander("View Raw JSON", expanded=False):
    st.json(st.session_state.schema_data)
