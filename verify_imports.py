import sys
import os

# Add the project root to sys.path
sys.path.append('/Users/ilkaygirgin/Documents/repos/fastapi-llm-microservice')

print("Attempting to import app.services.llm_service...")
try:
    from app.services import llm_service
    print("Success: app.services.llm_service imported.")
except ImportError as e:
    print(f"Error importing llm_service: {e}")
    sys.exit(1)

print("Attempting to import app.workers.tasks...")
try:
    from app.workers import tasks
    print("Success: app.workers.tasks imported.")
except ImportError as e:
    print(f"Error importing tasks: {e}")
    sys.exit(1)

print("All imports successful. Circular dependency resolved.")
