import json
import os
import time
import re

# --- CONFIGURATION ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MEDIA_FOLDER = os.path.join(BASE_DIR, "static", "generated_files")

# *** CHANGED FILENAME TO FORCE A FRESH START ***
DATA_FILE = os.path.join(BASE_DIR, "my_notes.json")

os.makedirs(MEDIA_FOLDER, exist_ok=True)

def load_notes():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r') as f:
            content = f.read().strip()
            # Safety check: if file contains non-JSON text, return empty
            if not content or "Generate code" in content:
                return []
            return json.loads(content)
    except:
        return []

def save_new_note(title, content_or_file_data, note_type):
    notes = load_notes()
    saved_content = ""
    
    # Clean filename strictly
    safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '_')
    if not safe_title: safe_title = "untitled"
    
    if note_type == "TEXT":
        saved_content = content_or_file_data
    else:
        ext = "mp4" if note_type == "VIDEO" else "mp3"
        filename = f"{int(time.time())}_{safe_title}.{ext}"
        file_path = os.path.join(MEDIA_FOLDER, filename)
        
        try:
            with open(file_path, 'wb') as f:
                f.write(content_or_file_data)
            saved_content = f"static/generated_files/{filename}"
        except Exception as e:
            print(f"Error saving file: {e}")
            return

    new_entry = {
        "title": title,
        "content": saved_content,
        "type": note_type,
        "timestamp": time.time()
    }
    
    notes.insert(0, new_entry)
    
    # Save to the NEW file
    with open(DATA_FILE, 'w') as f:
        json.dump(notes, f, indent=4)

def get_notes_by_section(section_type):
    all_notes = load_notes()
    return [n for n in all_notes if isinstance(n, dict) and n.get('type') == section_type]