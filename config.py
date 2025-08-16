# config.py 
#    + load all of the .env variables 
#    + define all constants for model name, etc 

# library for loading .env variables 
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
######################################################################################################################
''' 
    Load LLm providers + define constants for different types of LLM here
        -The line LLM_PROVIDER would be changed if we need to set llm provider to be another
'''
LLM_PROVIDER = "gemini" 
CLAUDE_LLM_PROVIDER = "claude"
GEMINI_LLM_PROVIDER = "gemini"

######################################################################################################################
'''
    Config for LLM model + API key loading
'''
# define model + load API key for Claude 
CLAUDE_MODEL= ""
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

# define model + load API key for Gemini
GEMINI_MODEL = "gemini-1.5-pro"
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")


######################################################################################################################
'''
    Config for TOOL such as NOTION, ... (to be updated in the future --> fill below)
'''
# Config for NOTION here
NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"
NOTION_API_TOKEN = os.getenv("NOTION_API_TOKEN")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")


# config for other tools in the future will be added below this line


######################################################################################################################
'''
    Randome stuff, should be named / checked later
'''
# define constants for usi g uv for subprocess installs 
USE_UV = 0

# Optional: used by demo scripts, load github token from .env
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN='")

######################################################################################################################