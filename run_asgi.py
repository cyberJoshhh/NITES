import os
import sys
import django
from django.core.asgi import get_asgi_application

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'chat_project.settings')
django.setup()

# Import ASGI application from your project
try:
    from chat_project.asgi import application as asgi_app
    print("Successfully imported ASGI application")
except Exception as e:
    print(f"Error importing ASGI application: {e}")
    sys.exit(1)

# Try to import and set up Daphne
try:
    from daphne.server import Server
    from daphne.endpoints import build_endpoint_description_strings
    print("Successfully imported Daphne components")
except ImportError as e:
    print(f"Error importing Daphne: {e}")
    print("Make sure Daphne is installed with: pip install daphne")
    sys.exit(1)

# Run the server
if __name__ == "__main__":
    print("Starting ASGI server...")
    
    # Show what we're going to serve
    print(f"ASGI Application: {asgi_app}")
    
    # Set up server
    try:
        # Configure the server
        server = Server(
            application=asgi_app,
            endpoints=build_endpoint_description_strings(host="127.0.0.1", port=8000),
            signal_handlers=True,
            action_logger=None,
            http_timeout=None,
            websocket_timeout=None,
            ping_interval=None,
            ping_timeout=None,
            root_path="",
            websocket_handshake_timeout=None,
        )
        
        # Run the server
        print("Server configured. Starting...")
        server.run()
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc() 