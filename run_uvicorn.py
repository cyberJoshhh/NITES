import os
import sys
import subprocess

def check_redis():
    """Check if Redis server is running"""
    try:
        import redis
        client = redis.Redis(host='127.0.0.1', port=6379, db=0)
        client.ping()
        print("✅ Redis server is running")
        return True
    except Exception as e:
        print(f"❌ Redis server error: {e}")
        print("Make sure Redis server is installed and running")
        return False

def run_uvicorn(port=8002):
    """Run the ASGI application with Uvicorn"""
    try:
        import uvicorn
        print(f"Starting Uvicorn ASGI server on port {port}...")
        uvicorn.run(
            "chat_project.asgi:application",
            host="127.0.0.1",
            port=port,
            reload=False,  # Set to False to avoid import issues
            log_level="info"
        )
    except ImportError as e:
        print(f"Uvicorn not installed: {e}")
        print("Installing uvicorn...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "uvicorn[standard]"])
            print("Uvicorn installed, please run this script again")
        except Exception as e:
            print(f"Error installing uvicorn: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error running Uvicorn: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    print("=== Django Channels Chat Server ===")
    
    # Check Redis first
    if not check_redis():
        print("\nWARNING: Redis server appears to be unavailable.")
        print("WebSockets might not work without Redis running.")
        input("Press Enter to continue anyway or Ctrl+C to cancel...")
    
    # Run Uvicorn
    port = 8002
    run_uvicorn(port=port) 