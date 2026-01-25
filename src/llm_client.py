
import os
import os
import base64
from mistralai import Mistral
from dotenv import load_dotenv

# Load env variables
load_dotenv()

API_KEY = os.getenv("MISTRAL_API_KEY")

class LLMClient:
    def __init__(self):
        if not API_KEY:
            print("WARNING: MISTRAL_API_KEY not found in environment.")
        
        self.client = Mistral(api_key=API_KEY)

    def process_audio(self, audio_path, instruction):
        """
        Uploads audio (base64) and asks Mistral to process it.
        """
        if not os.path.exists(audio_path):
            return "Error: Audio file not found."
            
        try:
            print(f"Reading audio: {audio_path}...")
            
            with open(audio_path, "rb") as f:
                audio_bytes = f.read()
                
            base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            
            print(f"DEBUG: Read {len(audio_bytes)} bytes. Sending to Mistral...")
            
            # Construct message with mixed content (text + audio)
            # Using 'pixtral-large-latest' or similar multimodal; 
            # ideally 'voxtral' if specific, but pixtral handles multimodal inputs in many contexts.
            # Adjust model name as needed based on availability.
            model = "mistral-small-latest" 
            
            messages = [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": instruction
                        },
                        {
                            "type": "image_url", # Note: Some SDKs use consistent naming, but for audio specifically:
                            # If using specific audio model, format might differ. 
                            # Sticking to the standard chat completion with audio if supported.
                            # Re-verification: Mistral API often uses 'audio_url' or specific audio messages.
                            # Let's try the standard multimodal 'image_url' pattern but for audio? 
                            # actually, standard is usually separate.
                            # Let's use the patterns found in search: "type": "audio_url"
                            "type": "input_audio", 
                            "input_audio": f"data:audio/wav;base64,{base64_audio}"
                        }
                    ]
                }
            ]

            response = self.client.chat.complete(
                model=model,
                messages=messages
            )
            
            if response.choices:
                return response.choices[0].message.content
            return "No response content."

        except Exception as e:
            print(f"Error calling Mistral: {e}")
            return f"Error: {str(e)}"

if __name__ == "__main__":
    # Test stub
    # client = LLMClient()
    pass
