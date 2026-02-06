import os
from dotenv import load_dotenv

def require_env(name: str) -> str:
    load_dotenv()
    value = os.getenv(name)
    if value is None:
        raise RuntimeError(f"Missing required env var: {name}")
    
    return value
