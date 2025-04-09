# Django Chat System

A real-time chat application built with Django, Channels, and MySQL.

## Features

- User registration and authentication
- Real-time messaging using WebSockets
- Chat rooms with support for spaces and special characters
- Message history stored in MySQL database
- Redis-based message broadcasting

## Requirements

- Python 3.8+
- MySQL
- Redis (for Channels)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/django-chat-system.git
   cd django-chat-system
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Make sure MySQL and Redis servers are running on your machine.
   - For Redis on Windows: Download from [Redis for Windows](https://github.com/tporadowski/redis/releases)
   - For MySQL: Make sure your MySQL server is running

4. Create the MySQL database:
   ```
   python create_database.py
   ```

5. Run migrations:
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

6. Create a superuser for admin access:
   ```
   python manage.py createsuperuser
   ```

## Running the Application

### Using the provided helper script (recommended)

```
python run_uvicorn.py
```

This will:
- Check if Redis is running
- Start an ASGI server (Uvicorn) on port 8002
- Run your application with proper WebSocket support

### Manual ASGI server start

```
uvicorn chat_project.asgi:application --host 127.0.0.1 --port 8002
```

Or with Daphne:
```
daphne -p 8002 chat_project.asgi:application
```

### Access the Application

Visit [http://127.0.0.1:8002/chat/](http://127.0.0.1:8002/chat/) in your browser.

## Usage

1. Register a new account or log in with an existing account.
2. Create a new chat room or join an existing one.
3. Start chatting in real-time with other users in the same room.

## Admin Access

You can access the admin panel at [http://127.0.0.1:8002/admin/](http://127.0.0.1:8002/admin/) using the superuser credentials created during setup.

## Troubleshooting

If you encounter WebSocket connection issues:

1. Visit the diagnostics page at [http://127.0.0.1:8002/chat/diagnostics/](http://127.0.0.1:8002/chat/diagnostics/)
2. Make sure Redis server is running
3. Ensure you're using an ASGI server (Uvicorn or Daphne), not Django's development server
4. Check the browser console for WebSocket connection errors

## Project Structure

- `chat/` - Main application directory
  - `consumers.py` - WebSocket consumers for real-time messaging
  - `models.py` - Database models (Room, Message)
  - `views.py` - Views for rendering templates
  - `routing.py` - WebSocket routing
  - `urls.py` - URL routing
  - `templates/` - HTML templates
  - `static/` - Static files
- `chat_project/` - Project configuration
  - `settings.py` - Django settings
  - `asgi.py` - ASGI configuration for Channels
  - `urls.py` - Main URL configuration 