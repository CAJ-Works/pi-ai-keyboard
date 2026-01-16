
import os
import base64
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load env variables
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

class LLMClient:
    def __init__(self):
        if not API_KEY:
            print("WARNING: GOOGLE_API_KEY not found in environment.")
        
        self.client = genai.Client(api_key=API_KEY)

    def process_audio(self, audio_path, instruction):
        """
        Uploads audio and asks Gemini to process it with the instruction.
        """
        if not os.path.exists(audio_path):
            return "Error: Audio file not found."
            
        try:
            print(f"Reading audio: {audio_path}...")
            # For the new SDK, we can often pass bytes or upload
            # Simplest for small audio clips is acting on bytes if small enough, or upload.
            # Using basic content generation with file path/bytes.
            
            # Read file as bytes
            with open(audio_path, "rb") as doc:
                audio_bytes = doc.read()
            
            print(f"DEBUG: Read {len(audio_bytes)} bytes from audio file.")
            
            print("Sending to Gemini...")
            
            # Reverting to gemini-1.5-flash for rate limits
            # Explicitly wrapping text in Part as well
            response = self.client.models.generate_content(
                model='gemini-2.0-flash-lite-preview-02-05',
                contents=[
                    types.Part.from_text(text=instruction),
                    types.Part.from_bytes(data=audio_bytes, mime_type="audio/wav")
                ]
            )
            
            return response.text
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            if "404" in str(e) or "NOT_FOUND" in str(e):
                print("\n--- DEBUG: Available Models ---")
                try:
                    for model in self.client.models.list():
                        print(f" - {model.name}")
                except Exception as list_err:
                    print(f"Could not list models: {list_err}")
                print("-------------------------------\n")
            return f"Error: {str(e)}"

if __name__ == "__main__":
    # Test stub
    # client = LLMClient()
    pass
