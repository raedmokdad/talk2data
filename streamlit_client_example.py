# Talk2Data Agent - Client Example for Streamlit App
# This is what your Mitarbeiter needs for their Streamlit App

import streamlit as st
import requests
import json
from typing import Dict, Any

class Talk2DataClient:
    """Client to communicate with Talk2Data Agent API"""
    
    def __init__(self, api_base_url: str = "http://your-vm-ip:8000"):
        self.api_base_url = api_base_url.rstrip('/')
        
    def health_check(self) -> bool:
        """Check if the API is healthy"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            return response.status_code == 200 and response.json().get("status") == "healthy"
        except:
            return False
    
    def generate_sql(self, question: str, max_retries: int = 3, confidence_threshold: float = 0.7) -> Dict[str, Any]:
        """Generate SQL from natural language question"""
        try:
            payload = {
                "question": question,
                "max_retries": max_retries,
                "confidence_threshold": confidence_threshold
            }
            
            response = requests.post(
                f"{self.api_base_url}/generate-sql",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "data": response.json()
                }
            else:
                return {
                    "success": False,
                    "error": f"API Error {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timeout - API took too long to respond"
            }
        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": "Connection error - Cannot reach API server"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }

# Streamlit App Configuration
st.set_page_config(
    page_title="Talk2Data Client",
    page_icon="🗣️",
    layout="wide"
)

# Initialize API client
API_URL = st.sidebar.text_input("API URL", value="http://localhost:8000", help="URL of your Talk2Data Agent")
client = Talk2DataClient(API_URL)

# Main UI
st.title("🗣️ Talk2Data Client")
st.markdown("Connect to Talk2Data Agent and generate SQL from natural language!")

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    max_retries = st.slider("Max Retries", 1, 5, 3)
    confidence_threshold = st.slider("Confidence Threshold", 0.1, 1.0, 0.7, 0.1)
    
    st.header("🔍 API Status")
    if st.button("Check API Health"):
        with st.spinner("Checking API..."):
            is_healthy = client.health_check()
            if is_healthy:
                st.success("✅ API is healthy!")
            else:
                st.error("❌ API is not responding")

# Main input area
st.header("💬 Ask your question")
question = st.text_area(
    "Enter your question in natural language:",
    placeholder="Show me sales for store 5 in January 2015",
    height=100
)

col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    generate_button = st.button("🚀 Generate SQL", type="primary", use_container_width=True)

with col2:
    if st.button("🧪 Test Connection", use_container_width=True):
        with st.spinner("Testing..."):
            is_healthy = client.health_check()
            if is_healthy:
                st.success("Connected!")
            else:
                st.error("Connection failed!")

with col3:
    clear_button = st.button("🗑️ Clear", use_container_width=True)
    if clear_button:
        st.rerun()

# Process the request
if generate_button and question:
    with st.spinner("🤖 Generating SQL..."):
        result = client.generate_sql(
            question=question,
            max_retries=max_retries,
            confidence_threshold=confidence_threshold
        )
    
    if result["success"]:
        data = result["data"]
        
        # Display results
        st.header("📊 Results")
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            confidence_color = "normal"
            if data["confidence"] >= 0.8:
                confidence_color = "normal"
            elif data["confidence"] >= 0.6:
                confidence_color = "normal"
            else:
                confidence_color = "inverse"
                
            st.metric(
                "Confidence",
                f"{data['confidence']:.1%}",
                delta=f"{data['confidence'] - confidence_threshold:.1%}" if data['confidence'] >= confidence_threshold else f"{data['confidence'] - confidence_threshold:.1%}"
            )
        
        with col2:
            status_icon = "✅" if data["validation_passed"] else "❌"
            st.metric("Validation", f"{status_icon}")
        
        with col3:
            st.metric("Processing Time", f"{data['processing_time']:.2f}s")
        
        with col4:
            quality_score = "Excellent" if data["confidence"] >= 0.8 and data["validation_passed"] else \
                           "Good" if data["confidence"] >= 0.6 and data["validation_passed"] else \
                           "Poor"
            quality_color = "🟢" if quality_score == "Excellent" else "🟡" if quality_score == "Good" else "🔴"
            st.metric("Quality", f"{quality_color} {quality_score}")
        
        # SQL Output
        st.subheader("🔍 Generated SQL")
        st.code(data["sql_query"], language="sql")
        
        # Additional info
        with st.expander("ℹ️ Additional Information"):
            st.json({
                "message": data["message"],
                "confidence": data["confidence"],
                "validation_passed": data["validation_passed"],
                "processing_time": data["processing_time"]
            })
        
        # Copy button
        if st.button("📋 Copy SQL to Clipboard"):
            st.write("SQL copied! (Note: Clipboard functionality requires browser permissions)")
            
    else:
        # Display error
        st.error(f"❌ Error: {result['error']}")
        
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common issues:**
            - Check if the API URL is correct
            - Ensure the Talk2Data Agent is running
            - Check firewall settings (port 8000)
            - Verify network connectivity between servers
            """)

elif generate_button and not question:
    st.warning("⚠️ Please enter a question first!")

# Footer with instructions
st.markdown("---")
st.markdown("""
### 📖 How to use:
1. **Configure API URL** in the sidebar (replace 'your-vm-ip' with actual IP)
2. **Check API Health** to ensure connection
3. **Enter your question** in natural language
4. **Click Generate SQL** to get results
5. **Copy the SQL** and use it in your database

### 🔗 API Endpoints:
- Health: `{API_URL}/health`
- Generate: `{API_URL}/generate-sql`
- Docs: `{API_URL}/docs`
""".replace("{API_URL}", API_URL))

# Example questions
with st.expander("💡 Example Questions"):
    examples = [
        "Show me sales for store 5",
        "What are the top 10 stores by revenue?",
        "Find average daily sales in January 2015",
        "Which stores had sales above 10000?",
        "Compare actual vs forecast sales for store 1"
    ]
    
    for example in examples:
        if st.button(f"Try: {example}", key=example):
            st.text_area("Question:", value=example, key=f"example_{example}")