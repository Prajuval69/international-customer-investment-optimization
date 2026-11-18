"""Print portable manual screenshot instructions; no extra browser dependency."""

from pathlib import Path

if __name__ == "__main__":
    destination = Path(__file__).parents[1] / "reports" / "screenshots"
    destination.mkdir(parents=True, exist_ok=True)
    print("Start: streamlit run app/Home.py")
    print("Open http://127.0.0.1:8501 and use your browser's screenshot command.")
    print(f"Save one real screenshot per page under {destination}")
    print("Automated page rendering and interactions: pytest -q tests/test_dashboard.py")
