import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

print("Environment variables:")
print(f"LIVEKIT_API_KEY: {'set' if os.getenv('LIVEKIT_API_KEY') else 'not set'}")
print(f"LIVEKIT_API_SECRET: {'set' if os.getenv('LIVEKIT_API_SECRET') else 'not set'}")
print(f"GOOGLE_API_KEY: {'set' if os.getenv('GOOGLE_API_KEY') else 'not set'}")
print(f"DEEPGRAM_API_KEY: {'set' if os.getenv('DEEPGRAM_API_KEY') else 'not set'}")
print(f"CARTESIA_API_KEY: {'set' if os.getenv('CARTESIA_API_KEY') else 'not set'}")
print(f"PINECONE_API_KEY: {'set' if os.getenv('PINECONE_API_KEY') else 'not set'}")
print(f"ASSISTANT_NAME: {'set' if os.getenv('ASSISTANT_NAME') else 'not set'}")
print(f"ANAM_API_KEY: {'set' if os.getenv('ANAM_API_KEY') else 'not set'}")
print(f"ANAM_AVATAR_ID: {'set' if os.getenv('ANAM_AVATAR_ID') else 'not set'}")
print(f"AVATAR_IMAGE_PATH: {'set' if os.getenv('AVATAR_IMAGE_PATH') else 'not set'}")

try:
    from core.config import settings
    print("\nSettings loaded successfully!")
    print(f"HOST: {settings.HOST}")
    print(f"PORT: {settings.PORT}")
    print(f"DEBUG: {settings.DEBUG}")
    print(f"LOG_LEVEL: {settings.LOG_LEVEL}")
    print(f"ANAM_API_KEY: {'set' if settings.ANAM_API_KEY else 'not set'}")
    print(f"ANAM_AVATAR_ID: {'set' if settings.ANAM_AVATAR_ID else 'not set'}")
    print(f"AVATAR_IMAGE_PATH: {'set' if settings.AVATAR_IMAGE_PATH else 'not set'}")
except Exception as e:
    print(f"\nError loading settings: {e}")
    import traceback
    traceback.print_exc()