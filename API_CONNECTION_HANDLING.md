# API Connection Handling

## Issue Fixed

The application was crashing with connection errors when the FastAPI server was not running:

```
Error loading template main_template: HTTPConnectionPool(host='localhost', port=8000): 
Max retries exceeded with url: /api/email-templates/user@example.com/by-type/0 
(Caused by NewConnectionError: Failed to establish a new connection: 
[WinError 10061] No connection could be made because the target machine actively refused it)
```

## Solution

The application now gracefully handles API unavailability:

1. **Connection Check**: Added `is_available()` method to check if API server is running
2. **Silent Failure**: Template loading fails silently if API is unavailable
3. **Offline Mode**: Application continues to work in offline mode
4. **Timeout**: Added request timeouts to prevent hanging
5. **Better Error Handling**: Connection errors are caught and handled gracefully

## Changes Made

### 1. `api_client.py`

**Added:**
- `is_available()` method to check API server status
- `timeout` parameter to all requests (default: 5 seconds)
- Connection check before making requests

**Before:**
```python
def __init__(self, base_url: str = "http://localhost:8000"):
    self.base_url = base_url.rstrip('/')
    self.session = requests.Session()
```

**After:**
```python
def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 5):
    self.base_url = base_url.rstrip('/')
    self.timeout = timeout
    self.session = requests.Session()

def is_available(self) -> bool:
    """Check if API server is available"""
    try:
        response = self.session.get(f"{self.base_url}/health", timeout=2)
        return response.status_code == 200
    except (requests.exceptions.RequestException, requests.exceptions.Timeout):
        return False
```

### 2. `view/main_ui.py`

**Added:**
- Connection check during initialization
- Silent failure for connection errors
- Better error handling in `_load_templates_from_db()`

**Before:**
```python
try:
    self.api_client = ApplyCheAPIClient("http://localhost:8000")
except Exception as e:
    print(f"Warning: Could not connect to API: {e}")
    self.api_client = None
```

**After:**
```python
try:
    self.api_client = ApplyCheAPIClient("http://localhost:8000", timeout=3)
    # Check if API is available (don't fail if it's not)
    if not self.api_client.is_available():
        print("Info: FastAPI server is not running. Templates will be saved locally only.")
        self.api_client = None
except Exception as e:
    print(f"Info: API client initialization failed: {e}")
    self.api_client = None
```

**Template Loading:**
```python
def _load_templates_from_db(self):
    """Load email templates from database and populate UI
    Silently fails if API is not available - app continues to work in offline mode
    """
    if not self.api_client:
        return
    
    # Check if API is actually available before trying to load
    try:
        if not self.api_client.is_available():
            return  # Silently continue
    except Exception:
        return  # Silently continue
    
    try:
        # ... load templates ...
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
        # API server is not available - silently continue (offline mode)
        pass
    except Exception as e:
        # Other errors - log but don't crash
        print(f"Info: Could not load templates from database: {type(e).__name__}")
```

## Behavior

### When API Server is Running ✅
- Templates load from database on startup
- Templates save to database when saved
- Full functionality available

### When API Server is NOT Running ✅
- Application starts normally (no crashes)
- Templates load as empty (can be created fresh)
- Templates save locally only
- User can still use the application
- No error messages shown to user (silent failure)

## Usage

### Starting the Application

**Option 1: With API Server**
```bash
# Terminal 1: Start FastAPI server
cd api
python -m uvicorn main:app --reload

# Terminal 2: Start PyQt6 application
python view/main_ui.py
```

**Option 2: Without API Server (Offline Mode)**
```bash
# Just start the PyQt6 application
python view/main_ui.py
# Application will work in offline mode - templates saved locally only
```

## Error Messages

The application now handles errors gracefully:

- **Connection Errors**: Silently ignored (offline mode)
- **Timeout Errors**: Silently ignored (server too slow)
- **Other Errors**: Logged but don't crash the app

## Benefits

1. ✅ **No Crashes**: Application never crashes due to API unavailability
2. ✅ **Offline Mode**: Application works without API server
3. ✅ **Better UX**: No scary error messages for users
4. ✅ **Faster Startup**: Connection check is quick (2 second timeout)
5. ✅ **Graceful Degradation**: Features work locally when API unavailable

## Testing

### Test Offline Mode
1. Don't start the FastAPI server
2. Run the PyQt6 application
3. Application should start without errors
4. Templates should be empty (can create new ones)
5. Saving templates should work (saved locally)

### Test Online Mode
1. Start the FastAPI server: `python -m uvicorn api.main:app --reload`
2. Run the PyQt6 application
3. Templates should load from database
4. Saving templates should save to database

## Notes

- Connection check uses `/health` endpoint (must be available)
- Timeout is configurable (default: 5 seconds for requests, 2 seconds for health check)
- All connection errors are caught and handled gracefully
- Application continues to work in offline mode

