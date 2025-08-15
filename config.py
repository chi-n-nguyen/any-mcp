# config.py 
#    + load all of the .env variables 
#    + define all constants for model name, etc 

# library for loading .env variables 
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Load LLm providers + define constants for different types of LLM here
LLM_PROVIDER = "gemini" # this line would be changed if we need to set llm provider to be another
CLAUDE_LLM_PROVIDER = "claude"
GEMINI_LLM_PROVIDER = "gemini"

# define model + load API key for Claude 
CLAUDE_MODEL= ""
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# define model + load API key for Gemini
GEMINI_MODEL = "gemini-1.5-pro"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# define constants for usi g uv for subprocess installs 
USE_UV = 0

# Optional: used by demo scripts, load github token from .env
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN='")
