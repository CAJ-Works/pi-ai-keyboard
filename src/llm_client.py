import os
from groq import Groq
from dotenv import load_dotenv

# Load env variables
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

class LLMClient:
    def __init__(self):
        if not API_KEY:
            print("WARNING: GROQ_API_KEY not found in environment.")
        
        self.client = Groq(api_key=API_KEY)

    def process_audio(self, audio_path, instruction):
        """
        Transcribes audio using Groq (Whisper) and then processes the text with an LLM.
        """
        if not os.path.exists(audio_path):
            return "Error: Audio file not found."
            
        try:
            print(f"Reading audio: {audio_path}...")
            
            # 1. Transcribe Audio
            with open(audio_path, "rb") as file:
                transcription = self.client.audio.transcriptions.create(
                    file=(audio_path, file.read()),
                    model="whisper-large-v3-turbo",
                    response_format="text"
                )
            
            print(f"DEBUG: Transcription: {transcription}")

            # 2. Process with LLM
            # We treat the instruction as the system prompt (or context) and the transcription as the user input?
            # Or vice versa? 
            # The instruction is like "Summarize this". 
            # So: User says: [Audio Content]. System/Prompt says: "Summarize the following text..."
            
            messages = [
                {
                    "role": "system",
                    "content": instruction
                },
                {
                    "role": "user",
                    "content": transcription
                }
            ]

            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=messages,
                temperature=0.5,
                max_completion_tokens=1024,
                top_p=1,
                stop=None,
                stream=False,
            )
            
            if completion.choices:
                return completion.choices[0].message.content
            return "No response content."

        except Exception as e:
            print(f"Error calling Groq: {e}")
            return f"Error: {str(e)}"
    # Test stub
    # client = LLMClient()
    pass
