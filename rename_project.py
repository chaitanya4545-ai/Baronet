"""
Rename all references from OpenClaw to Baronet
"""
import os
from pathlib import Path

def rename_in_file(filepath):
    """Replace OpenClaw with Baronet in a file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace both OpenClaw and openclaw
        new_content = content.replace('OpenClaw', 'Baronet')
        new_content = new_content.replace('openclaw', 'baronet')
        
        if content != new_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            print(f"✓ Updated: {filepath}")
            return True
        return False
    except Exception as e:
        print(f"✗ Error in {filepath}: {e}")
        return False

# Directories to process
dirs_to_process = ['core', 'modules', 'tests']
extensions = ['.py']

# Also process root files
root_files = ['test_ai_integration.py', 'test_stability.py', 'test_torture.py']

updated_count = 0

# Process directories
for dir_name in dirs_to_process:
    dir_path = Path(dir_name)
    if dir_path.exists():
        for ext in extensions:
            for filepath in dir_path.rglob(f'*{ext}'):
                if rename_in_file(filepath):
                    updated_count += 1

# Process root files
for filename in root_files:
    filepath = Path(filename)
    if filepath.exists():
        if rename_in_file(filepath):
            updated_count += 1

print(f"\n✅ Renamed {updated_count} files")
