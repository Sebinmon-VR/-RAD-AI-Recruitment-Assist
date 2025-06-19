import os
import re

def check_for_credentials():
    """Scan files for potential credentials."""
    
    # Patterns that might indicate credentials
    patterns = [
        r'sk-[a-zA-Z0-9]{32,}',  # OpenAI API key pattern
        r'AIza[0-9A-Za-z-_]{35}',  # Google API key
        r'[Aa]ccess[Kk]ey[Ii]d.*["\']([A-Z0-9]{20})["\']',  # AWS Access Key
        r'[Ss]ecret[Aa]ccess[Kk]ey.*["\']([A-Za-z0-9/+=]{40})["\']',  # AWS Secret
        r'password\s*=\s*["\'][^"\']+["\']',  # Password assignments
        r'secret\s*=\s*["\'][^"\']+["\']',  # Secret assignments
    ]
    
    exclude_files = {'.gitignore', 'check_credentials.py', '.env.example'}
    exclude_dirs = {'.git', '.venv', '__pycache__', 'node_modules'}
    
    found_issues = []
    
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file in exclude_files:
                continue
                
            filepath = os.path.join(root, file)
            
            try:
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        found_issues.append(f"⚠️  {filepath}: Found potential credential pattern")
                        
            except Exception as e:
                continue
    
    if found_issues:
        print("🚨 POTENTIAL CREDENTIALS FOUND:")
        for issue in found_issues:
            print(f"  {issue}")
        print("\n❌ DO NOT COMMIT until these are resolved!")
        return False
    else:
        print("✅ No obvious credentials found in tracked files")
        return True

if __name__ == "__main__":
    check_for_credentials()
