import os
import sys

print("Python version:", sys.version)
print("Current directory:", os.getcwd())

# Test .env file
print("\n--- Testing .env file ---")
env_file = ".env"
if os.path.exists(env_file):
    print("✓ .env file exists")
    with open(env_file, 'r') as f:
        content = f.read()
        print("File content preview:")
        print(content[:200] + "..." if len(content) > 200 else content)
else:
    print("✗ .env file not found")

# Test python-dotenv
print("\n--- Testing python-dotenv ---")
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✓ python-dotenv imported successfully")
    
    # Check environment variables
    secret_key = os.environ.get('SECRET_KEY')
    openai_key = os.environ.get('OPENAI_API_KEY')
    
    print(f"SECRET_KEY: {'Set' if secret_key else 'Not set'}")
    print(f"OPENAI_API_KEY: {'Set' if openai_key else 'Not set'}")
    
except ImportError as e:
    print(f"✗ python-dotenv import failed: {e}")

# Test Flask
print("\n--- Testing Flask ---")
try:
    from flask import Flask
    print("✓ Flask imported successfully")
except ImportError as e:
    print(f"✗ Flask import failed: {e}")

# Test OpenAI
print("\n--- Testing OpenAI ---")
try:
    import openai
    print("✓ OpenAI imported successfully")
except ImportError as e:
    print(f"✗ OpenAI import failed: {e}")

# Test other dependencies
print("\n--- Testing other dependencies ---")
dependencies = ['PyPDF2', 'pdfplumber', 'requests']
for dep in dependencies:
    try:
        __import__(dep)
        print(f"✓ {dep} imported successfully")
    except ImportError as e:
        print(f"✗ {dep} import failed: {e}")
