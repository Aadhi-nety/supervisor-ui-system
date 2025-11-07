import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # LiveKit Configuration
    LIVEKIT_URL = os.getenv('LIVEKIT_URL', 'ws://localhost:7880')
    LIVEKIT_API_KEY = os.getenv('LIVEKIT_API_KEY')
    LIVEKIT_API_SECRET = os.getenv('LIVEKIT_API_SECRET')
    
    # Groq Configuration
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    
    # OpenAI Configuration (for LiveKit STT/TTS)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    
    # Redis Configuration
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    
    # Supervisor Configuration
    SUPERVISOR_PHONE = os.getenv('SUPERVISOR_PHONE', '+1234567890')
    
    # Application Configuration
    REQUEST_TIMEOUT_MINUTES = int(os.getenv('REQUEST_TIMEOUT_MINUTES', '60'))