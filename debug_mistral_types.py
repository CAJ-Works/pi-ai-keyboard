
import inspect
from mistralai.models import UserMessage, TextChunk
try:
    # Try importing typical location for content types
    from mistralai.models import InputAudioChunk, AudioChunk
    print("Found InputAudioChunk")
    print(InputAudioChunk.model_json_schema())
except ImportError:
    print("Could not import InputAudioChunk directly.")
    
try:
    # generic search in models
    import mistralai.models as models
    for name, obj in inspect.getmembers(models):
        if "Audio" in name:
            print(f"Found {name}: {obj}")
            if hasattr(obj, 'model_json_schema'):
                print(obj.model_json_schema())
except Exception as e:
    print(f"Error inspecting models: {e}")

try:
    # client chat method inspection could help too
    from mistralai import Mistral
    print("Mistral client imported")
except:
    pass
