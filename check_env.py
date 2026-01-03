"""Helper script to check if .env file is set up correctly."""

from pathlib import Path

env_file = Path(".env")

if not env_file.exists():
    print("❌ .env file not found!")
    print("\n📝 Please create a .env file in the project root with:")
    print("\nOPENAI_API_KEY=your_openai_api_key_here")
    print("\nOptional:")
    print("NEWSAPI_KEY=your_newsapi_key_here")
    print("SERPAPI_KEY=your_serpapi_key_here")
    print("\nSee SETUP.md for the complete template.")
else:
    print("✅ .env file found")
    
    # Check if OPENAI_API_KEY is set
    from dotenv import load_dotenv
    import os
    
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or api_key == "your_openai_api_key_here":
        print("❌ OPENAI_API_KEY not set or still has placeholder value")
        print("   Please set your actual OpenAI API key in the .env file")
    else:
        print(f"✅ OPENAI_API_KEY is set (starts with: {api_key[:7]}...)")

