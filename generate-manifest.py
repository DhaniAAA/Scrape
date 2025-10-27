"""
Generate comics-list.json manifest file from Supabase bucket
Upload this file to bucket root to enable frontend listing
"""

from supabase import create_client
import json

# Supabase Configuration
SUPABASE_URL = "https://nnaizqqgdtqmfpwzcspe.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im5uYWl6cXFnZHRxbWZwd3pjc3BlIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDY1NDA4NiwiZXhwIjoyMDc2MjMwMDg2fQ.Kn87MMhIbIK83_JBV6wqHKWQkMmmtjTqbFUrn6W-KBQ"
BUCKET_NAME = "manga-data"

def generate_manifest():
    """Generate comics-list.json from bucket"""
    print("🔍 Connecting to Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    print("📁 Listing folders in bucket...")
    
    # Try different list methods
    try:
        # Method 1: List with path
        result = supabase.storage.from_(BUCKET_NAME).list('', {"limit": 1000})
        print(f"   List result type: {type(result)}")
        print(f"   List result: {result}")
        
        # Check if result is a dict with 'data' key
        if isinstance(result, dict) and 'data' in result:
            folders = result['data']
        else:
            folders = result if isinstance(result, list) else []
            
    except Exception as e:
        print(f"   ⚠️  List error: {e}")
        folders = []
    
    # Extract folder names (comic slugs)
    comic_slugs = []
    for folder in folders:
        if isinstance(folder, dict):
            name = folder.get('name', '')
            # Skip files, only get folders
            if name and not name.endswith('.json'):
                comic_slugs.append(name)
                print(f"   ✓ {name}")
    
    print(f"\n✅ Found {len(comic_slugs)} comics")
    
    # Save to JSON
    manifest_data = comic_slugs
    
    with open('comics-list.json', 'w', encoding='utf-8') as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Saved to comics-list.json")
    
    # Upload to Supabase
    print("📤 Uploading to Supabase...")
    with open('comics-list.json', 'rb') as f:
        supabase.storage.from_(BUCKET_NAME).upload(
            'comics-list.json',
            f,
            {"content-type": "application/json", "upsert": "true"}
        )
    
    print("✅ Upload complete!")
    print(f"\n📋 Manifest contains {len(comic_slugs)} comics:")
    for slug in comic_slugs[:10]:
        print(f"   - {slug}")
    if len(comic_slugs) > 10:
        print(f"   ... and {len(comic_slugs) - 10} more")

if __name__ == '__main__':
    generate_manifest()
