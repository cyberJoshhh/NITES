#!/usr/bin/env python
import os
import sys
import subprocess
import importlib
from importlib.util import find_spec

def print_header(text):
    print("\n" + "=" * 60)
    print(f" {text} ".center(60, "-"))
    print("=" * 60)

def check_installation(package):
    try:
        spec = find_spec(package)
        if spec is not None:
            module = importlib.import_module(package)
            version = getattr(module, '__version__', 'Unknown')
            print(f"✅ {package} is installed (version {version})")
            return True
        else:
            print(f"❌ {package} is NOT installed")
            return False
    except ImportError:
        print(f"❌ {package} is NOT installed")
        return False

def check_redis():
    try:
        import redis
        client = redis.Redis(host='127.0.0.1', port=6379, db=0)
        client.ping()
        print(f"✅ Redis server is running at 127.0.0.1:6379")
        return True
    except Exception as e:
        print(f"❌ Redis server issue: {e}")
        return False

def install_package(package):
    print(f"Installing {package}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        print(f"✅ Successfully installed {package}")
        return True
    except Exception as e:
        print(f"❌ Failed to install {package}: {e}")
        return False

def check_asgi_config():
    asgi_path = os.path.join('chat_project', 'asgi.py')
    if not os.path.exists(asgi_path):
        print(f"❌ Could not find {asgi_path}")
        return False
    
    with open(asgi_path, 'r') as f:
        content = f.read()
    
    if 'ProtocolTypeRouter' in content and 'AuthMiddlewareStack' in content and 'URLRouter' in content:
        print("✅ ASGI file appears to be correctly configured for Channels")
        return True
    else:
        print("❌ ASGI file might not be correctly configured for Channels")
        return False

def check_settings():
    settings_path = os.path.join('chat_project', 'settings.py')
    if not os.path.exists(settings_path):
        print(f"❌ Could not find {settings_path}")
        return False
    
    with open(settings_path, 'r') as f:
        content = f.read()
    
    issues = []
    if "'channels'" not in content:
        issues.append("'channels' is not in INSTALLED_APPS")
    
    if "ASGI_APPLICATION" not in content:
        issues.append("ASGI_APPLICATION is not defined")
    
    if "CHANNEL_LAYERS" not in content:
        issues.append("CHANNEL_LAYERS is not defined")
    
    if issues:
        print("❌ Issues found in settings.py:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("✅ settings.py appears to be correctly configured")
        return True

def run_daphne():
    print("Starting Daphne ASGI server...")
    try:
        # Save the command for the user to run
        with open('run_daphne.bat', 'w') as f:
            f.write('@echo off\n')
            f.write('echo Starting Daphne ASGI server...\n')
            f.write('daphne -p 8000 chat_project.asgi:application\n')
            f.write('pause\n')
        
        print("✅ Created run_daphne.bat - run this script to start the server with WebSocket support")
        return True
    except Exception as e:
        print(f"❌ Failed to create Daphne script: {e}")
        return False

def main():
    print_header("WebSocket Diagnostics")
    
    # Check Django and Channels installations
    django_ok = check_installation('django')
    channels_ok = check_installation('channels')
    channels_redis_ok = check_installation('channels_redis')
    redis_client_ok = check_installation('redis')
    
    # Check Redis server
    redis_server_ok = check_redis()
    
    print_header("Configuration Checks")
    
    # Check ASGI and settings configuration
    asgi_ok = check_asgi_config()
    settings_ok = check_settings()
    
    print_header("Results Summary")
    
    issues = []
    
    if not channels_ok:
        issues.append("Channels not installed")
    
    if not channels_redis_ok:
        issues.append("channels-redis not installed")
    
    if not redis_client_ok:
        issues.append("Redis client not installed")
    
    if not redis_server_ok:
        issues.append("Redis server not running")
    
    if not asgi_ok:
        issues.append("ASGI configuration issue")
    
    if not settings_ok:
        issues.append("Django settings configuration issue")
    
    if issues:
        print("❌ WebSocket issues found:")
        for issue in issues:
            print(f"  - {issue}")
        
        print_header("Automatic Fixes")
        
        # Fix installation issues
        if not channels_ok:
            install_package('channels')
        
        if not channels_redis_ok:
            install_package('channels_redis')
        
        if not redis_client_ok:
            install_package('redis')
        
        # Create Daphne runner
        run_daphne()
        
        print_header("Manual Steps")
        
        if not redis_server_ok:
            print("1. Install and start Redis server:")
            print("   - Windows: https://github.com/tporadowski/redis/releases")
            print("   - Linux: sudo apt install redis-server && sudo service redis-server start")
            print("   - macOS: brew install redis && brew services start redis")
        
        print("\n2. Run your Django server using Daphne ASGI server:")
        print("   - Run the created run_daphne.bat file or")
        print("   - Execute: daphne -p 8000 chat_project.asgi:application")
        
        print("\n3. Check your browser console for WebSocket connection errors")
        
    else:
        print("✅ All WebSocket components appear to be correctly configured")
        print("\nTo run the server with WebSocket support, use:")
        print("   daphne -p 8000 chat_project.asgi:application")
        
        # Create Daphne runner anyway
        run_daphne()

if __name__ == "__main__":
    main() 