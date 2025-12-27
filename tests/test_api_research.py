"""
Integration tests for Research API.
"""
import pytest
from fastapi.testclient import TestClient
import tempfile
import os
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

# Set test environment before imports
os.environ["SQLITE_PATH"] = str(Path(tempfile.mkdtemp()) / "test.db")
os.environ["CHROMA_DIR"] = tempfile.mkdtemp()

from app.main import app


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


class TestHealthEndpoints:
    """Test health check endpoints."""
    
    def test_root(self, client):
        """Test root endpoint."""
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Agentic Research Copilot"
        assert data["status"] == "running"
    
    def test_health(self, client):
        """Test health endpoint."""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "components" in data


class TestResearchAPI:
    """Test research endpoints."""
    
    def test_create_research_run(self, client):
        """Test creating a research run."""
        response = client.post(
            "/v1/research",
            json={
                "topic": "Transformer attention mechanisms",
                "depth": "quick",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
        assert data["status"] == "pending"
    
    def test_create_research_with_constraints(self, client):
        """Test creating research with constraints."""
        response = client.post(
            "/v1/research",
            json={
                "topic": "Neural network optimization",
                "constraints": "Focus on papers from 2023",
                "depth": "normal",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "run_id" in data
    
    def test_create_research_validation(self, client):
        """Test validation of research request."""
        # Topic too short
        response = client.post(
            "/v1/research",
            json={"topic": "ab", "depth": "quick"}
        )
        
        assert response.status_code == 422
    
    def test_list_runs(self, client):
        """Test listing runs."""
        # Create a run first
        client.post("/v1/research", json={"topic": "Test topic", "depth": "quick"})
        
        response = client.get("/v1/runs")
        
        assert response.status_code == 200
        data = response.json()
        assert "runs" in data
        assert "total" in data


class TestRunStatus:
    """Test run status endpoints."""
    
    def test_get_run_not_found(self, client):
        """Test getting non-existent run."""
        response = client.get("/v1/runs/nonexistent-id")
        
        assert response.status_code == 404
    
    def test_get_run_after_create(self, client):
        """Test getting run after creation."""
        # Create run
        create_response = client.post(
            "/v1/research",
            json={"topic": "Machine learning basics", "depth": "quick"}
        )
        run_id = create_response.json()["run_id"]
        
        # Get run
        response = client.get(f"/v1/runs/{run_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == run_id
        assert data["objective"] == "Machine learning basics"


class TestFeedbackAPI:
    """Test feedback endpoints."""
    
    def test_submit_feedback(self, client):
        """Test submitting feedback."""
        # Create run first
        create_response = client.post(
            "/v1/research",
            json={"topic": "Test for feedback", "depth": "quick"}
        )
        run_id = create_response.json()["run_id"]
        
        # Submit feedback
        response = client.post(
            "/v1/feedback",
            json={
                "run_id": run_id,
                "rating": 4,
                "comment": "Good results!",
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 4
    
    def test_submit_feedback_invalid_rating(self, client):
        """Test submitting feedback with invalid rating."""
        response = client.post(
            "/v1/feedback",
            json={
                "run_id": "some-id",
                "rating": 6,  # Invalid: must be 1-5
            }
        )
        
        assert response.status_code == 422
    
    def test_submit_feedback_run_not_found(self, client):
        """Test submitting feedback for non-existent run."""
        response = client.post(
            "/v1/feedback",
            json={
                "run_id": "nonexistent-id",
                "rating": 3,
            }
        )
        
        assert response.status_code == 404


class TestExportAPI:
    """Test export endpoints."""
    
    def test_export_not_found(self, client):
        """Test exporting non-existent run."""
        response = client.get("/v1/runs/nonexistent/export?format=markdown")
        
        assert response.status_code == 404
    
    def test_export_invalid_format(self, client):
        """Test exporting with invalid format."""
        # Create run
        create_response = client.post(
            "/v1/research",
            json={"topic": "Export test", "depth": "quick"}
        )
        run_id = create_response.json()["run_id"]
        
        response = client.get(f"/v1/runs/{run_id}/export?format=invalid")
        
        assert response.status_code == 400
