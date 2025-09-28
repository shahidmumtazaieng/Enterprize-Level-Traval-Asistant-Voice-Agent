import sys

required_packages = [
    "fastapi",
    "uvicorn",
    "livekit",
    "livekit-agents",
    "livekit-plugins-deepgram",
    "livekit-plugins-google",
    "livekit-plugins-cartesia",
    "livekit-plugins-silero",
    "python-dotenv",
    "pydantic",
    "pydantic-settings"
]

missing_packages = []

for package in required_packages:
    try:
        __import__(package.replace("-", "_"))
        print(f"✓ {package} is installed")
    except ImportError:
        print(f"✗ {package} is missing")
        missing_packages.append(package)

if missing_packages:
    print(f"\nMissing packages: {', '.join(missing_packages)}")
    print("Please install them with: pip install " + " ".join(missing_packages))
else:
    print("\nAll required packages are installed!")