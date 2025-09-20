# FHIR Integration Setup Guide

## Project Structure
```
NewProject/
└── NewProject/
    ├── app.py
    ├── fhir_mapping.py
    ├── db.py
    ├── s.py
    └── debug_fhir_test.py
```

## Setup Instructions

1. **Activate Virtual Environment**
   ```powershell
   # Navigate to project root
   cd C:\Users\DY15D\OneDrive\Desktop\NewProject

   # Create virtual environment (if not exists)
   python -m venv .venv
   ```

2. **Install Dependencies**
   ```powershell
   # Using the .venv Python
   C:\Users\DY15D\OneDrive\Desktop\NewProject\.venv\Scripts\python.exe -m pip install fastapi uvicorn sqlalchemy pydantic openpyxl pandas fuzzywuzzy python-Levenshtein fhir.resources requests xlrd>=2.0.1
   ```

## Running the Server

1. **Navigate to the Correct Directory**
   ```powershell
   cd C:\Users\DY15D\OneDrive\Desktop\NewProject\NewProject
   ```

2. **Start FastAPI Server**
   ```powershell
   # Using explicit path to uvicorn
   C:\Users\DY15D\OneDrive\Desktop\NewProject\.venv\Scripts\uvicorn.exe app:app --reload
   ```

   Or using Python module:
   ```powershell
   C:\Users\DY15D\OneDrive\Desktop\NewProject\.venv\Scripts\python.exe -m uvicorn app:app --reload
   ```

3. **Access the API**
   - Swagger UI Documentation: http://127.0.0.1:8000/docs
   - API Endpoint: http://127.0.0.1:8000/fhir_resource

## Testing the FHIR Integration

1. **Open a New Terminal**
2. **Run the Test Script**
   ```powershell
   cd C:\Users\DY15D\OneDrive\Desktop\NewProject\NewProject
   C:\Users\DY15D\OneDrive\Desktop\NewProject\.venv\Scripts\python.exe debug_fhir_test.py
   ```

## Troubleshooting

If you see "Error loading ASGI app":
1. Verify you're in the correct directory (NewProject/NewProject)
2. Try setting PYTHONPATH:
   ```powershell
   $env:PYTHONPATH = 'C:\Users\DY15D\OneDrive\Desktop\NewProject\NewProject'
   C:\Users\DY15D\OneDrive\Desktop\NewProject\.venv\Scripts\uvicorn.exe app:app --reload
   ```

## Important Notes

- Always use the Python interpreter from the `.venv` directory
- Make sure to run commands from the correct directory (NewProject/NewProject)
- The server must be running before executing the test script
- Keep the server terminal open while testing