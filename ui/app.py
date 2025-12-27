"""
Streamlit UI for Agentic Research Copilot.
Real-time visualization of the research workflow.
"""
import streamlit as st
import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE = "http://localhost:8000"

# Page config
st.set_page_config(
    page_title="Agentic Research Copilot",
    page_icon="🔬",
    layout="wide",
)

# Custom CSS
st.markdown("""
<style>
    .stProgress > div > div > div > div {
        background-color: #4a4a8a;
    }
    .success-box {
        padding: 10px;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        margin: 10px 0;
    }
    .info-box {
        padding: 10px;
        border-radius: 5px;
        background-color: #cce5ff;
        border: 1px solid #b8daff;
        margin: 10px 0;
    }
</style>
""", unsafe_allow_html=True)


def check_api():
    """Check if API is available."""
    try:
        response = requests.get(f"{API_BASE}/health", timeout=5)
        return response.status_code == 200
    except:
        return False


def start_research(topic: str, depth: str, constraints: str = None) -> dict:
    """Start a new research run."""
    payload = {
        "topic": topic,
        "depth": depth,
    }
    if constraints:
        payload["constraints"] = constraints
    
    response = requests.post(f"{API_BASE}/v1/research", json=payload)
    return response.json()


def get_run_status(run_id: str) -> dict:
    """Get run status."""
    response = requests.get(f"{API_BASE}/v1/runs/{run_id}")
    return response.json()


def get_recent_runs() -> list:
    """Get recent runs."""
    try:
        response = requests.get(f"{API_BASE}/v1/runs?limit=10")
        return response.json().get("runs", [])
    except:
        return []


# Main UI
st.title("🔬 Agentic Research Copilot")
st.caption("AI-powered research assistant • Local LLM • Multi-source retrieval")

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API status
    api_available = check_api()
    if api_available:
        st.success("✅ API Connected")
    else:
        st.error("❌ API Offline")
        st.info("Start the API with:\n```\nmake dev\n```")
    
    st.divider()
    
    # Recent runs
    st.header("📜 Recent Runs")
    runs = get_recent_runs()
    for run in runs[:5]:
        status_icon = "✅" if run.get("status") == "completed" else "⏳" if run.get("status") == "running" else "❌"
        with st.expander(f"{status_icon} {run.get('objective', 'Unknown')[:30]}..."):
            st.write(f"**Status:** {run.get('status')}")
            st.write(f"**Depth:** {run.get('depth')}")
            if run.get("created_at"):
                st.write(f"**Created:** {run.get('created_at')[:19]}")
            if st.button("View", key=run.get("id")):
                st.session_state.selected_run = run.get("id")

# Main content
tab1, tab2, tab3 = st.tabs(["🔍 New Research", "📊 Results", "📈 Analytics"])

with tab1:
    st.header("Start New Research")
    
    with st.form("research_form"):
        topic = st.text_area(
            "Research Topic",
            placeholder="e.g., What are the latest developments in transformer attention mechanisms?",
            height=100,
        )
        
        col1, col2 = st.columns(2)
        with col1:
            depth = st.select_slider(
                "Research Depth",
                options=["quick", "normal", "deep"],
                value="normal",
                help="Quick: 5 sources, Normal: 10 sources, Deep: 20 sources"
            )
        
        with col2:
            constraints = st.text_input(
                "Constraints (optional)",
                placeholder="e.g., Focus on papers from 2023-2024",
            )
        
        submitted = st.form_submit_button("🚀 Start Research", use_container_width=True)
    
    if submitted and topic:
        if not api_available:
            st.error("API is not available. Please start the server first.")
        else:
            with st.spinner("Starting research..."):
                result = start_research(topic, depth, constraints if constraints else None)
                run_id = result.get("run_id")
                
                if run_id:
                    st.session_state.current_run_id = run_id
                    st.success(f"Research started! Run ID: `{run_id}`")
                    
                    # Show progress
                    progress_placeholder = st.empty()
                    status_placeholder = st.empty()
                    
                    # Poll for updates
                    max_polls = 120  # 2 minutes max
                    for i in range(max_polls):
                        status = get_run_status(run_id)
                        current_status = status.get("status", "unknown")
                        
                        progress_placeholder.progress(
                            min((i + 1) / max_polls, 0.95),
                            f"Status: {current_status}"
                        )
                        
                        if current_status == "completed":
                            progress_placeholder.progress(1.0, "Complete!")
                            st.session_state.selected_run = run_id
                            st.balloons()
                            break
                        elif current_status == "failed":
                            st.error("Research failed. Check the Results tab for details.")
                            break
                        
                        time.sleep(1)
                else:
                    st.error(f"Failed to start research: {result}")

with tab2:
    st.header("Research Results")
    
    # Run selector
    run_id = st.text_input("Enter Run ID", value=st.session_state.get("selected_run", ""))
    
    if run_id:
        run = get_run_status(run_id)
        
        if "detail" in run:
            st.error(f"Run not found: {run_id}")
        else:
            # Status badges
            col1, col2, col3 = st.columns(3)
            with col1:
                status = run.get("status", "unknown")
                status_color = "green" if status == "completed" else "orange" if status == "running" else "red"
                st.metric("Status", status.upper())
            with col2:
                st.metric("Depth", run.get("depth", "normal").upper())
            with col3:
                sources_count = len(run.get("sources", []) or [])
                st.metric("Sources Found", sources_count)
            
            st.divider()
            
            # Objective
            st.subheader("📋 Objective")
            st.write(run.get("objective", "N/A"))
            
            if run.get("constraints"):
                st.write(f"**Constraints:** {run.get('constraints')}")
            
            # Sources
            if run.get("sources"):
                st.subheader("📚 Sources")
                for i, source in enumerate(run.get("sources", [])[:10], 1):
                    with st.expander(f"{i}. {source.get('title', 'Untitled')[:60]}..."):
                        st.write(f"**Source:** {source.get('source', 'unknown')}")
                        st.write(f"**Year:** {source.get('year', 'N/A')}")
                        st.write(f"**URL:** [{source.get('url', '')}]({source.get('url', '')})")
                        st.write(f"**Abstract:** {source.get('abstract', 'N/A')[:300]}...")
            
            # Final Report
            if run.get("final_report"):
                st.subheader("📄 Final Report")
                st.markdown(run.get("final_report"))
                
                # Export buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("📥 Download Markdown"):
                        st.download_button(
                            "Download",
                            run.get("final_report"),
                            f"research_{run_id}.md",
                            "text/markdown",
                        )
            
            # Timings
            if run.get("timings"):
                st.subheader("⏱️ Timings")
                timings = run.get("timings", {})
                for node, duration in timings.items():
                    st.write(f"- **{node}:** {duration:.2f}s")
            
            # Errors
            if run.get("errors"):
                st.subheader("⚠️ Errors")
                for error in run.get("errors", []):
                    st.error(error)

with tab3:
    st.header("Analytics")
    
    runs = get_recent_runs()
    
    if runs:
        col1, col2, col3 = st.columns(3)
        
        completed = len([r for r in runs if r.get("status") == "completed"])
        failed = len([r for r in runs if r.get("status") == "failed"])
        pending = len([r for r in runs if r.get("status") in ("pending", "running")])
        
        with col1:
            st.metric("Completed", completed)
        with col2:
            st.metric("Failed", failed)
        with col3:
            st.metric("In Progress", pending)
        
        # Depth distribution
        st.subheader("Research Depth Distribution")
        depth_counts = {}
        for r in runs:
            d = r.get("depth", "normal")
            depth_counts[d] = depth_counts.get(d, 0) + 1
        
        st.bar_chart(depth_counts)
    else:
        st.info("No research runs yet. Start your first research!")


# Footer
st.divider()
st.caption("Agentic Research Copilot • Powered by LangGraph + Ollama • Built for 8GB RAM")
