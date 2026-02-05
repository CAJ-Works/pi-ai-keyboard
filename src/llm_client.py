import os
from openai import OpenAI
from dotenv import load_dotenv

# Load env variables
load_dotenv()

class LLMClient:
    def __init__(self):
        # LLM Configuration (for Chat/Completion)
        # Default to a placeholder or localhost if not set, but user usually sets these in .env
        self.llm_base_url = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
        self.llm_api_key = os.getenv("LLM_API_KEY", "ollama") # Many local servers accept any string
        self.llm_model = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")

        # STT Configuration (for Whisper)
        # Often provided by a different service or port (e.g. OpenAI Whisper or a local inference server)
        self.stt_base_url = os.getenv("STT_BASE_URL", self.llm_base_url)
        self.stt_api_key = os.getenv("STT_API_KEY", self.llm_api_key)
        self.stt_model = os.getenv("STT_MODEL", "whisper-large-v3-turbo")

        self.debug = os.getenv("DEBUG_LLM", "False").lower() == "true"

        print(f"LLM Client: {self.llm_base_url} (Model: {self.llm_model})")
        print(f"STT Client: {self.stt_base_url} (Model: {self.stt_model})")

        self.llm_client = OpenAI(base_url=self.llm_base_url, api_key=self.llm_api_key)
        
        if self.stt_base_url == self.llm_base_url and self.stt_api_key == self.llm_api_key:
            self.stt_client = self.llm_client
        else:
            self.stt_client = OpenAI(base_url=self.stt_base_url, api_key=self.stt_api_key)

    def process_audio(self, audio_path, instruction):
        """
        Transcribes audio using a local Whisper model and then processes the text with a local LLM.
        """
        if not os.path.exists(audio_path):
            return "Error: Audio file not found."
            
        try:
            print(f"Reading audio: {audio_path} (Size: {os.path.getsize(audio_path)} bytes)...")
            
            # 1. Transcribe Audio
            print(f"DEBUG: Starting STT (Model: {self.stt_model})...")
            with open(audio_path, "rb") as file:
                transcription_response = self.stt_client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), file.read()),
                    model=self.stt_model,
                    response_format="text"
                )
            print("DEBUG: STT Complete.")

            transcription = transcription_response
            
            if self.debug:
                print(f"DEBUG: Transcription: {transcription}")
            
            if not transcription or isinstance(transcription, str) and not transcription.strip():
                 print("Warning: Empty transcription.")
                 return "Error: Could not transcribe audio."

            # 2. Process with LLM
            print(f"DEBUG: Starting LLM (Model: {self.llm_model})...")
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

            completion = self.llm_client.chat.completions.create(
                model=self.llm_model,
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
            print(f"Error calling LLM/STT provider: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                 print(f"DEBUG: Remote Error Details: {e.response.text}")
            return f"Error: {str(e)}"

if __name__ == "__main__":
    # Test stub
    # client = LLMClient()
    pass
