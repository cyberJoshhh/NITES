import subprocess
import os

def run_command(command):
    try:
        print(f"Running: {command}")
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: {e}")

def main():
    print("Setting up the Django Chat System...")
    
    # Create MySQL database
    run_command("python create_database.py")
    
    # Make migrations
    run_command("python manage.py makemigrations")
    
    # Apply migrations
    run_command("python manage.py migrate")
    
    # Create superuser
    print("\nCreating admin user...")
    run_command("python manage.py createsuperuser")
    
    print("\nSetup completed! You can now run the server with:")
    print("python manage.py runserver")

if __name__ == "__main__":
    main() 