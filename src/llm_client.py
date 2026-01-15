
import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load env variables
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if API_KEY:
    genai.configure(api_key=API_KEY)

class LLMClient:
    def __init__(self):
        if not API_KEY:
            print("WARNING: GOOGLE_API_KEY not found in environment.")
        
        # Flash Experimental models usually support multimodal best
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    def process_audio(self, audio_path, instruction):
        """
        Uploads audio and asks Gemini to process it with the instruction.
        """
        if not os.path.exists(audio_path):
            return "Error: Audio file not found."
            
        try:
            print(f"Uploading audio: {audio_path}...")
            # Upload the file
            audio_file = genai.upload_file(audio_path)
            
            print("Sending to Gemini...")
            # Generate content
            response = self.model.generate_content([instruction, audio_file])
            
            # Cleanup maybe? (Not strictly necessary for small usage, but good practice if needed)
            # genai.delete_file(audio_file.name)
            
            return response.text
        except Exception as e:
            print(f"Error calling Gemini: {e}")
            return f"Error: {str(e)}"

if __name__ == "__main__":
    # Test stub
    client = LLMClient()
    # print(client.process_audio("/tmp/test.wav", "Transcribe this"))
