"""clears all Gemini Context Caches"""

import os
import sys
from dotenv import load_dotenv
from google import genai

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("error: GEMINI_API_KEY not found in .env")
    sys.exit(1)

print("connecting to Gemini API...")
client = genai.Client(api_key=api_key)

try:
    print("fetching all active caches...")
    # list all caches
    caches = list(client.caches.list())
    
    if not caches:
        print("✅ no active caches found! You are safe from billing leaks.")
        sys.exit(0)
        
    print(f"⚠️ found {len(caches)} active caches lingering on Google's servers.")
    
    deleted_count = 0
    for cache in caches:
        print(f"🗑️ deleting cache: {cache.name} (created: {cache.create_time})")
        try:
            client.caches.delete(name=cache.name)
            deleted_count += 1
        except Exception as e:
            print(f"❌ failed to delete {cache.name}: {e}")
            
    print(f"\n✅ successfully deleted {deleted_count} out of {len(caches)} caches.")
    print("your Gemini API bill is now safe!")

except Exception as e:
    print(f"error communicating with Gemini API: {e}")
