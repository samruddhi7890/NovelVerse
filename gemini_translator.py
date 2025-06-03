import google.generativeai as genai
import os
import json # For potential future use if API responses are complex

# --- Configuration ---
# IMPORTANT: Replace "YOUR_API_KEY" with the API key you got from Google AI Studio
# For better security, consider using environment variables later.
GOOGLE_API_KEY = "AIzaSyC-NuzlfdgWzxQAO0n4_Mx7yHyiXw-MjTs" # <--- PUT YOUR API KEY HERE!

# Configure the Gemini API client
try:
    genai.configure(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    print("Please ensure you have set your GOOGLE_API_KEY correctly.")
    exit()

# Select the Gemini model
MODEL_NAME = "gemini-pro"
generation_config = {
    "temperature": 0.7,
    "top_p": 1.0,
    "top_k": 0,
    "max_output_tokens": 2048,
}
# safety_settings = [ # Optional: Adjust safety settings if needed
#     {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
#     {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
#     {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
#     {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
# ]

try:
    model = genai.GenerativeModel(
        model_name=MODEL_NAME,
        generation_config=generation_config,
        # safety_settings=safety_settings # Uncomment if you want to explicitly set safety settings
    )
except Exception as e:
    print(f"Error initializing Gemini model: {e}")
    exit()


TARGET_INDIAN_LANGUAGE = "Hindi" # Example: Hindi, Tamil, Bengali, Marathi etc.

# --- Part 1: LLM for Character Analysis and Name Suggestions ---

def get_character_analysis_and_suggestions(character_name_original, context_text, target_language):
    """
    Uses Gemini to analyze a character and suggest Indian names.
    """
    print(f"\n--- Analyzing Character: {character_name_original} ---")

    # 1. Get Character Description
    prompt_analysis = f"""
    From the following text, analyze the character named "{character_name_original}".
    Describe their personality, key traits, role in the story, and any significant attributes.
    Focus only on the character "{character_name_original}".

    Text:
    \"\"\"
    {context_text}
    \"\"\"

    Character Analysis for "{character_name_original}":
    """
    try:
        print("Sending request for character analysis...")
        response_analysis = model.generate_content(prompt_analysis)
        character_description = response_analysis.text.strip()
        print(f"\nGemini Generated Character Description for {character_name_original}:\n{character_description}")
    except Exception as e:
        print(f"Error during character analysis API call: {e}")
        if hasattr(e, 'prompt_feedback') and response_analysis.prompt_feedback.block_reason:
             print(f"Request blocked. Reason: {response_analysis.prompt_feedback.block_reason}")
        elif hasattr(e, 'parts') and not response_analysis.parts:
             print("Request may have been blocked or resulted in an empty response.")
        return None, None

    # 2. Get Name Suggestions
    prompt_suggestions = f"""
    Based on the following character description of a fictional character, suggest 3-5 culturally appropriate {target_language} names
    that would fit this character. Provide a brief one-sentence reason for each suggestion.
    Ensure the names are suitable for a fictional story context.

    Character Description:
    \"\"\"
    {character_description}
    \"\"\"

    Suggested {target_language} names (with reasons):
    """
    try:
        print("\nSending request for name suggestions...")
        response_suggestions = model.generate_content(prompt_suggestions)
        name_suggestions = response_suggestions.text.strip()
        print(f"\nGemini Generated Name Suggestions ({target_language}):\n{name_suggestions}")
        return character_description, name_suggestions
    except Exception as e:
        print(f"Error during name suggestion API call: {e}")
        if hasattr(e, 'prompt_feedback') and response_suggestions.prompt_feedback.block_reason:
             print(f"Request blocked. Reason: {response_suggestions.prompt_feedback.block_reason}")
        elif hasattr(e, 'parts') and not response_suggestions.parts:
             print("Request may have been blocked or resulted in an empty response.")
        return character_description, None

# --- Part 2: LLM for Translation with Admin-Selected Mappings ---

def translate_text_with_mappings(original_text, mappings, source_language, target_language):
    """
    Translates text using Gemini, applying the provided mappings.
    """
    print(f"\n--- Translating Text to {target_language} with Mappings ---")

    substitution_instructions = "Apply the following substitutions strictly and ensure they appear in the translated text:\n"
    if not mappings:
        substitution_instructions = "No specific name substitutions provided. Translate names naturally if appropriate or keep them as is if they are well-known and the target language typically keeps them as is.\n"
    else:
        for original, new in mappings.items():
            substitution_instructions += f"- Replace every instance of the exact phrase \"{original}\" with \"{new}\".\n"

    prompt_translation = f"""
    You are an expert literary translator. Translate the following text from {source_language} to {target_language}.
    {substitution_instructions}
    Maintain the narrative style, tone, and meaning of the original text accurately.
    Do not add any extra commentary or explanation outside of the translated text itself.

    Original {source_language} Text:
    \"\"\"
    {original_text}
    \"\"\"

    Translated {target_language} Text:
    """
    try:
        print("Sending request for translation...")
        response_translation = model.generate_content(prompt_translation)
        translated_text = response_translation.text.strip()
        print(f"\nOriginal Text:\n{original_text}")
        print(f"\nTranslated Text ({target_language}):\n{translated_text}")
        return translated_text
    except Exception as e:
        print(f"Error during translation API call: {e}")
        if hasattr(e, 'prompt_feedback') and response_translation.prompt_feedback.block_reason:
             print(f"Request blocked. Reason: {response_translation.prompt_feedback.block_reason}")
        elif hasattr(e, 'parts') and not response_translation.parts:
             print("Request may have been blocked or resulted in an empty response.")
        return None

# --- Main Execution ---
if __name__ == "__main__":
    # **Step 1: Provide your API Key**
    if GOOGLE_API_KEY == "YOUR_API_KEY" or not GOOGLE_API_KEY:
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("!!! ERROR: Please replace 'YOUR_API_KEY' in the script with     !!!")
        print("!!! your actual Google AI Studio API key.                      !!!")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        exit()

    # **Step 2: Simulate Admin providing original text and identifying a character**
    sample_original_chapter_text = """
    The biting wind howled as Akira trudged through the desolate wasteland, his cybernetic eye scanning the horizon.
    He was a relic of a forgotten war, a ronin searching for a purpose. His only companion, a small, hovering drone
    named 'Chirp', beeped anxiously. "The radiation levels are high, Akira-sama!" Chirp projected in its synthesized voice.
    Akira merely grunted, pulling his tattered cloak tighter. He needed to find the "Sunstone" artifact before
    the Crimson Syndicate, led by the ruthless General Volkov, could get their hands on it.
    His former master, Sensei Ishikawa, had warned him of the Sunstone's power.
    """
    original_character_to_analyze = "Akira"
    source_language_of_text = "English"

    print(f"--- Stage 1: Character Analysis & Name Suggestion for '{original_character_to_analyze}' in {TARGET_INDIAN_LANGUAGE} ---")
    description, suggestions = get_character_analysis_and_suggestions(
        original_character_to_analyze,
        sample_original_chapter_text,
        TARGET_INDIAN_LANGUAGE
    )

    if not description or not suggestions:
        print("\nHalting due to errors or blocked content in character analysis or name suggestion.")
        exit()

    # **Step 3: Simulate Admin selecting mappings**
    # YOU WILL MANUALLY UPDATE THIS DICTIONARY after reviewing the suggestions printed from Stage 1.
    admin_selected_mappings = {
        "Akira": "Vikram",
        "Chirp": "Kili", # Changed to Kili as per discussion (Tamil for parrot, often used for cute)
        "Akira-sama": "Vikram-ji",
        "Sunstone": "Suryamani",
        "Crimson Syndicate": "Lal Sena",
        "General Volkov": "Senapati Varma",
        "Sensei Ishikawa": "Guru Ishwar"
    }
    print("\n--- Admin has reviewed suggestions and defined the following mappings: ---")
    for k, v in admin_selected_mappings.items():
        print(f"'{k}' -> '{v}'")

    # **Step 4: Translate the chapter with these mappings**
    print(f"\n--- Stage 2: Translation of Chapter to {TARGET_INDIAN_LANGUAGE} with Mappings ---")
    translated_chapter = translate_text_with_mappings(
        sample_original_chapter_text,
        admin_selected_mappings,
        source_language_of_text,
        TARGET_INDIAN_LANGUAGE
    )

    if translated_chapter:
        print("\n\n--- Process Complete ---")
        print("Review the translated text above. You can now adjust mappings or prompts and re-run.")
    else:
        print("\n\n--- Process Incomplete due to errors or blocked content in translation ---")