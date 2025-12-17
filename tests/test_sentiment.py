
import pytest
from unittest.mock import patch
import os
import sys

# Add the project root to sys.path so we can import modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from general_functions import get_mood_from_text

class TestSentimentAnalysis:

    @patch.dict(os.environ, {"APP_LANG": "ENG"})
    def test_eng_positive(self):
        # We need to ensure general_functions re-reads the env var or we pass it
        # Actually general_functions reads env at module level. 
        # This is tricky for testing if logic relies on module-level global constant.
        # Let's inspect general_functions.py again. 
        # It reads APP_LANG once at top level.
        # To test different languages properly, we might need to reload the module or 
        # modify the global variable in the module directly.
        import general_functions
        general_functions.APP_LANG = "ENG"
        
        assert get_mood_from_text("I am so happy!") == "happy"
        # Wait, get_mood_from_text doesn't take override_lang yet. 
        # It uses the global. We can just set the global.
        
    def test_basic_moods(self):
        # Assuming default is ENG from .env or we mock it.
        # Let's try to test the logic that is currently active (ENG)
        import general_functions
        general_functions.APP_LANG = "ENG"
        
        assert get_mood_from_text("I am overjoyed with this result!") == "happy"
        assert get_mood_from_text("This is heartbreaking and sad.") == "sad"
        assert get_mood_from_text("The table is made of wood.") == "neutral"

    def test_angry_mapping(self):
        import general_functions
        general_functions.APP_LANG = "ENG"
        # "angry" maps to "sad" in our current logic
        assert get_mood_from_text("I am furious about this error!") == "sad" 
