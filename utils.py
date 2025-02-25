import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

# Verify API key
if not os.getenv("GEMINI_API_KEY"):
    raise ValueError("Missing GEMINI_API_KEY in .env file")

# Initialize GenAI client
genai_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def summarize_common(
    system_prompt: str,
    parts: list[types.Part],
    analysis_mode: str = "Quick Scan",
    model_name: str = "gemini-2.0-flash"
) -> str:
    """
    Unified function for content generation
    """
    token_config = {
        "Quick Scan": 1024,
        "Detailed Analysis": 2048,
        "Deep Dive": 4096
    }
    
    try:
        response = genai_client.models.generate_content(
            model=model_name,
            contents=[types.Content(role="user", parts=parts)],
            config=types.GenerateContentConfig(
                temperature=0.3,
                max_output_tokens=token_config.get(analysis_mode, 2048),
                system_instruction=system_prompt
            )
        )
        return response.text
    
    except Exception as e:
        raise RuntimeError(f"API Error: {str(e)}")
