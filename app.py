import json
import re
import os
import random
from typing import Dict, Any, List, Tuple

from langchain_groq import ChatGroq
from langchain.schema import HumanMessage

## NEW: Base directory to hold all stories
STORIES_BASE_DIR = "stories"
## NEW: Standard filenames to be used within each story's directory
CONTEXT_FILENAME = "story_context.json"
FULL_STORY_FILENAME = "full_hindi_story.txt"

# --- NEW: Ancient Indian Cities for Mapping ---
ANCIENT_INDIAN_CITIES = [
    "पाटलिपुत्र",  # Pataliputra (ancient Patna)
    "अयोध्या",     # Ayodhya
    "हस्तिनापुर",   # Hastinapur
    "इंद्रप्रस्थ",  # Indraprastha
    "उज्जैन",      # Ujjain
    "काशी",        # Kashi (Varanasi)
    "मथुरा",       # Mathura
    "द्वारका",     # Dwarka
    "कुरुक्षेत्र",   # Kurukshetra
    "तक्षशिला",    # Takshashila
    "कान्यकुब्ज",   # Kanyakubja (Kannauj)
    "वैशाली",      # Vaishali
    "राजगृह",      # Rajgriha
    "श्रावस्ती",    # Shravasti
    "कपिलवस्तु",   # Kapilavastu
    "गांधार",      # Gandhara
    "मगध",        # Magadha
    "कोसल",       # Kosala
    "अवंती",       # Avanti
    "चेदि"         # Chedi
]


def extract_json(text: str) -> Dict:
    """
    Extracts a JSON object from a string that might contain additional text or markdown.
    This function is designed to be resilient to common LLM formatting issues.
    """
    if not text:
        print("⚠️ Warning: Received empty text for JSON extraction.")
        return {}

    text = text.strip()
    json_block_match = re.search(r"```json\s*(.*?)\s*```", text, re.DOTALL)
    if json_block_match:
        json_string = json_block_match.group(1).strip()
    else:
        start_brace = text.find('{')
        end_brace = text.rfind('}')
        if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
            json_string = text[start_brace : end_brace + 1]
        else:
            json_string = text
    json_string = re.sub(r',\s*([}\]])', r'\1', json_string)

    try:
        return json.loads(json_string)
    except json.JSONDecodeError as e:
        print(f"❌ Critical JSON Parsing Error: {e}")
        print(f"📄 The LLM response could not be parsed as JSON.")
        print(f"   Problematic String (first 500 chars): {json_string[:500]}...")
        print("   This often happens if the model doesn't follow instructions. Returning an empty dictionary.")
        return {}


def load_context(story_path: str) -> Dict:
    """Loads the story context from the context file within a specific story's directory."""
    context_file = os.path.join(story_path, CONTEXT_FILENAME)
    if os.path.exists(context_file):
        print(f"✅ Found existing context in '{context_file}'. Loading...")
        with open(context_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    else:
        print(f"🔍 No existing context file found for this story. Starting fresh.")
        return {
            "chapter_count": 0,
            "name_mapping": {},
            "primary_indian_city": None,
            "city_mapping": {},
            "cumulative_summary": "This is the beginning of the story.",
            "all_characters": []
        }

def save_context(context: Dict, story_path: str):
    """Saves the updated story context to the context file within a specific story's directory."""
    context_file = os.path.join(story_path, CONTEXT_FILENAME)
    with open(context_file, 'w', encoding='utf-8') as f:
        json.dump(context, f, indent=4, ensure_ascii=False)
    print(f"✅ Story context saved to '{context_file}'.")

def append_to_full_story(chapter_number: int, hindi_story: str, story_path: str):
    """Appends the new chapter to the full story file within a specific story's directory."""
    full_story_file = os.path.join(story_path, FULL_STORY_FILENAME)
    with open(full_story_file, 'a', encoding='utf-8') as f:
        f.write(f"\n\n--- अध्याय {chapter_number} ---\n\n")
        f.write(hindi_story)
    print(f"✅ Chapter {chapter_number} appended to '{full_story_file}'.")


# --- Supervisor and Worker Classes---
class Supervisor:
    def __init__(self, supervisor_name: str, supervisor_prompt: str, model: Any):
        self.name = supervisor_name
        self.prompt_template = supervisor_prompt
        self.model = model

class Worker:
    def __init__(self, worker_name: str, worker_prompt: str, supervisor: Supervisor, max_chunk_size: int = None):
        self.name = worker_name
        self.prompt_template = worker_prompt
        self.supervisor = supervisor
        self.max_chunk_size = max_chunk_size

    def process_input(self, text: str) -> str:
        prompt = f"""SYSTEM ROLE: {self.prompt_template}

INPUT:
{text}

INSTRUCTIONS:
1. Follow the task strictly and precisely.
2. Your entire response must be ONLY the required output format (e.g., JSON, text).
3. Do NOT include any explanations, apologies, or conversational text like "Here is the JSON...".
4. If the task requires JSON, your response MUST be a single, valid JSON object. It must start with '{{' and end with '}}'. Do not wrap it in markdown.
"""
        messages = [HumanMessage(content=prompt)]
        try:
            response = self.supervisor.model.invoke(messages)
            return response.content
        except Exception as e:
            print(f"❌ {self.name} failed: {str(e)}")
            return ""

# Initialize with Groq model
try:
    groq_model = ChatGroq(
        model_name="llama3-70b-8192",
        temperature=0.2,
        max_tokens=8192
    )
    print("✅ Using Groq Llama3 model")
except Exception as e:
    print(f"❌ Groq initialization failed: {str(e)}. Please ensure GROQ_API_KEY is set in your environment variables.")
    exit(1)

# Create supervisor
supervisor = Supervisor(
    supervisor_name="Cultural Adaptation Supervisor",
    supervisor_prompt="You are a supervisor managing a multi-step workflow for culturally adapting Japanese light novels to an Indian context. Ensure each worker performs its task accurately.",
    model=groq_model
)

# --- Worker Prompts ---
summarize_prompt = """You are an expert analyst of Japanese light novels. Your task is to thoroughly analyze the provided chapter and extract all key information into a valid JSON object.

CRITICAL INSTRUCTIONS FOR JSON VALIDITY:
1.  **NO UNESCAPED QUOTES:** Never place a double-quote (") inside a string value unless you escape it with a backslash (\\"). For example, `{"key": "He said, \\"Hello\\""}` is correct.
2.  **NAME vs. ROLE:**
    *   The "name" key MUST contain the character's proper name (e.g., "Ye Qingtang", "Naruto Uzumaki"). **This field must not be empty.**
    *   The "role" key describes their function or relationship in the story (e.g., "protagonist", "father", "village elder", "main antagonist").
3.  **VALID JSON ONLY:** Your entire response must be a single, valid JSON object starting with `{` and ending with `}`. Do not include any other text, explanations, or markdown.
4.  **LOCATIONS/CITIES:** Pay special attention to any cities, towns, villages, or geographical locations mentioned in the text.

Your analysis must include:
1.  Character Analysis: List all characters with their Japanese names, roles, personalities, gender, species/type (human/animal/beast/spirit/etc.), and relationship with the protagonist.
2.  Key Events: Important plot points in chronological order.
3.  Emotional Tone: The dominant emotions and how they change.
4.  Cultural Elements: Food, festivals, customs, locations that may need adaptation.
5.  World Elements: Any unique aspects of the setting.
6.  Style Notes: Narrative style, point of view.
7.  Chapter Summary: A detailed 3-4 sentence summary of this chapter.
8.  Locations: List all cities, towns, villages, or geographical places mentioned.

EXAMPLE JSON STRUCTURE:
{
    "characters": [
        {"name": "Ye Qingtang", "role": "Protagonist, Reborn Cultivator", "personality": "Determined, Cunning, Initially Shocked", "gender": "female", "species": "human", "relationship_to_protagonist": "herself"},
        {"name": "Great Elder", "role": "Family Elder, Antagonist", "personality": "Cunning, Authoritative", "gender": "male", "species": "human", "relationship_to_protagonist": "family elder"}
    ],
    "key_events": ["Event description 1.", "Event description 2."],
    "emotional_tone": {"dominant_emotion": "Tension", "emotion_changes": "Starts with shock, moves to determination."},
    "cultural_elements": ["Spirit Root", "Family hierarchy"],
    "world_elements": ["Cultivation system", "Xuanling Sect"],
    "style_notes": {"narrative_style": "Third-person limited", "pov": "Ye Qingtang", "quirks": "Frequent internal monologues."},
    "chapter_summary": "A detailed 3-4 sentence summary of the current chapter's plot points and character developments.",
    "locations": ["Tokyo", "Kyoto", "Shibuya District"]
}"""

adaptation_prompt = """You are a master Hindi novelist and screenwriter. Your mission is to transform a simple chapter into a vivid, cinematic, and emotionally resonant narrative for Indian readers. Your writing must be grammatically flawless and rich with descriptive detail.

**YOUR ROLE IS TO BE A STORYTELLER, NOT A TRANSLATOR. BREATHE LIFE INTO THE SCENE.**

**YOUR PROCESS:**
1.  **Understand the Core Scene:** Read the `original_text` and identify its key actions, dialogue, and emotional beats.
2.  **Use Your Tools:**
    *   `name_mapping`: You MUST use these Indian names.
    *   `city_mapping`: You MUST use this Indian city for ALL locations.
    *   `previous_summary`: Understand what happened before for context.
3.  **Write the Chapter:** Your output must be a flowing narrative. Do not just list events; weave them together into a compelling story.

**VIVID STORYTELLING TECHNIQUES (यह सबसे ज़रूरी है):**
*   **Show, Don't Tell:** This is your most important rule. Instead of stating an emotion, describe the physical actions that reveal it.
    *   **FLAT:** "वह नाराज़ था।"
    *   **VIVID:** "क्रोध से उसकी नसें तन गईं और उसने अपनी मुट्ठियाँ भींच लीं। उसकी आँखों में एक खतरनाक चमक थी।"
*   **Sentence Variety for Pacing:** Control the reading rhythm.
    *   Use **short, sharp sentences** during action or high-tension moments. (जैसे: वह भागा। साँस फूल रही थी। पीछे मुड़कर नहीं देखा।)
    *   Use **longer, flowing sentences** for descriptions of the environment, characters' thoughts, or moments of calm.
*   **Sensory Details:** Engage the reader's senses. What does the character see, hear, smell, or feel? Describe the dusty air, the smell of rain on soil, the distant temple bells, the texture of a silken robe.
*   **Dynamic Dialogue:** Dialogue is more than words.
    *   Describe *how* something is said. Use tags like 'फुसफुसाया' (whispered), 'चीख़कर बोला' (shouted), 'धीमे से कहा' (said softly), 'हिचकिचाते हुए पूछा' (asked hesitantly).
    *   Use punctuation to reflect speech patterns. A comma (,) for a pause, an ellipsis (...) for a trailing thought.
*   **Strategic Punctuation:** Your punctuation builds the world.
    *   **। (purna viram):** For firm sentence endings.
    *   **, (comma):** For natural pauses in thought or speech.
    *   **... (ellipsis):** To create suspense, show hesitation, or an unfinished thought.
    *   **! (exclamation mark):** For strong emotions - surprise, anger, joy, fear. Use it purposefully.
    *   **" " (quotes):** For all spoken dialogue.

**ADAPTATION RULES:**
-   Replace ALL foreign locations with the single Indian city provided in `city_mapping`.
-   Adapt cultural elements (food, customs) to an authentic Indian context.
-   Maintain the core plot, but enhance it with the storytelling techniques above.

**OUTPUT FORMAT:**
- Your entire response MUST be ONLY the full Hindi chapter.
- NO JSON, NO explanations, NO "Here is the chapter..."
- Write a complete, polished, and ready-to-read story chapter.
"""

naming_prompt = """You are a naming expert for localization. You will receive a JSON list of HUMAN characters. For each character, suggest 3 culturally appropriate FULL Indian names (first name + surname) based on their gender, role, and personality.

IMPORTANT: Only suggest names for characters whose species is "human".

Format your entire response as a single, valid JSON object. Do not add any other text.
{
    "name_suggestions": [
        {
            "original_name": "character_name",
            "gender": "male/female/unknown",
            "role": "character_role",
            "indian_names": ["FirstName Surname 1", "FirstName Surname 2", "FirstName Surname 3"]
        }
    ]
}"""

context_updater_prompt = """You are a story archivist. Your job is to create a seamless, updated plot summary. You will receive a JSON object with two keys: "previous_summary" and "new_chapter_summary".

Combine them into a new, coherent cumulative summary that briefly covers the entire story so far. It should be concise but capture all major plot points.

Output ONLY the new, updated cumulative summary as a plain text string. Do not add any other text or explanation.
"""

# Create workers
workers = {
    "summarizer": Worker("Chapter Summarizer", summarize_prompt, supervisor),
    "adapter": Worker("Cultural Adapter", adaptation_prompt, supervisor),
    "naming": Worker("Name Suggester", naming_prompt, supervisor),
    "context_updater": Worker("Context Updater", context_updater_prompt, supervisor)
}
#Handles user input for pasting chapter content.
def get_user_text() -> str:
    print("\nPaste the English version of the new chapter (Ctrl+Z then Enter on Windows, Ctrl+D then Enter on Unix):")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        lines.append(line)
    return "\n".join(lines)

# --- Display and Helper Functions ---
def print_detailed_summary(analysis_data: Dict, chapter_number: int):
    print("\n" + "="*80)
    print(f"📋 DETAILED ANALYSIS & SUMMARY (Chapter {chapter_number})")
    print("="*80)
    chapter_summary = analysis_data.get("chapter_summary", "No summary available")
    print(f"\n📖 CHAPTER SUMMARY:\n   {chapter_summary}")
    characters = analysis_data.get("characters", [])
    print(f"\n👥 CHARACTERS ({len(characters)} found):")
    for i, char in enumerate(characters, 1):
        if isinstance(char, dict):
            print(f"   {i}. {char.get('name', 'N/A')} | Role: {char.get('role', 'N/A')} | Species: {char.get('species', 'N/A')}")

    # Display locations found
    locations = analysis_data.get("locations", [])
    if locations:
        print(f"\n🏙️ LOCATIONS ({len(locations)} found):")
        for i, location in enumerate(locations, 1):
            print(f"   {i}. {location}")

def filter_new_human_characters(new_chars: List[Dict], existing_chars: List[Dict]) -> List[Dict]:
    """Filters for human characters that have not been seen before."""
    existing_names = {char.get('name') for char in existing_chars}
    new_human_characters = []
    for char in new_chars:
        if isinstance(char, dict) and char.get('species', '').lower() == 'human' and char.get('name') not in existing_names:
            new_human_characters.append(char)
    return new_human_characters

# Function to filter new locations
def filter_new_locations(new_locations: List[str], existing_mapping: Dict[str, str]) -> List[str]:
    """Filters for locations that haven't been mapped yet."""
    return [loc for loc in new_locations if loc and loc not in existing_mapping]

# Function to display mapping changes
def print_mapping_summary(name_mapping: Dict[str, str], city_mapping: Dict[str, str], chapter_num: int):
    """Prints a summary of all name and city mappings used in this chapter."""
    print(f"\n🗺️ MAPPING SUMMARY (Chapter {chapter_num}):")
    print("="*60)

    if name_mapping:
        print("\n👤 CHARACTER MAPPINGS:")
        for original, mapped in name_mapping.items():
            print(f"   {original} → {mapped}")

    if city_mapping:
        print("\n🏙️ CITY MAPPINGS:")
        for original, mapped in city_mapping.items():
            print(f"   {original} → {mapped}")

    if not name_mapping and not city_mapping:
        print("   No mappings needed for this chapter.")

# The central orchestration function. It calls various workers, handles character/city mapping interactions, updates context, and returns the translated chapter.
def run_pipeline(text: str, context: Dict) -> Tuple[str, Dict]:
    context["chapter_count"] += 1
    chapter_num = context["chapter_count"]
    print(f"\n🔍 Analyzing Chapter {chapter_num} content...")
    analysis_data = None
    analysis_raw = ""
    max_retries = 2
    for attempt in range(max_retries):
        if attempt > 0:
            print(f"   ...Attempt {attempt + 1} to get valid analysis from LLM.")
            fixer_prompt = f"""The JSON you provided previously was invalid and could not be parsed.
Error: The JSON contained syntax errors, likely unescaped quotes or missing commas.
Here is the invalid JSON you generated:
---
{analysis_raw}
---
Please correct the JSON syntax and provide ONLY the valid JSON object. Do not include any other text.
The original request was:
{summarize_prompt}"""
            analysis_raw = workers["summarizer"].process_input(fixer_prompt)
        else:
            analysis_raw = workers["summarizer"].process_input(text)
        analysis_data = extract_json(analysis_raw)
        if analysis_data and analysis_data.get("characters"):
            print("✅ Analysis successful.")
            break
    if not analysis_data or not analysis_data.get("characters"):
        print("❌ Chapter analysis failed after several retries. Cannot proceed.")
        context["chapter_count"] -= 1
        return "Chapter processing failed due to analysis error.", context

    print_detailed_summary(analysis_data, chapter_num)

    # Handle character name mappings (existing logic)
    print("\n💡 Managing character names...")
    new_characters_in_chapter = analysis_data.get("characters", [])
    new_human_characters = filter_new_human_characters(new_characters_in_chapter, context["all_characters"])
    if not new_human_characters:
        print("✅ No new human characters found. Using existing name mappings.")
    else:
        print(f"✨ Found {len(new_human_characters)} new human character(s) needing names.")
        name_suggestions_raw = workers["naming"].process_input(json.dumps(new_human_characters, ensure_ascii=False))
        name_data = extract_json(name_suggestions_raw)
        if name_data.get("name_suggestions"):
            print("\nPlease select Indian names for each NEW human character:")
            for suggestion in name_data["name_suggestions"]:
                original_name = suggestion.get("original_name")
                indian_names = suggestion.get("indian_names", [])
                print(f"\n👤 New Character: {original_name} (Role: {suggestion.get('role', 'N/A')})")
                for j, name in enumerate(indian_names, 1):
                    print(f"   {j}. {name}")
                print(f"   {len(indian_names) + 1}. Keep original name ({original_name})")
                while True:
                    try:
                        choice = int(input(f"👆 Your choice (1-{len(indian_names) + 1}): "))
                        if 1 <= choice <= len(indian_names):
                            context["name_mapping"][original_name] = indian_names[choice-1]
                            break
                        elif choice == len(indian_names) + 1:
                            context["name_mapping"][original_name] = original_name
                            break
                        else: print("❌ Invalid choice.")
                    except ValueError: print("❌ Invalid input.")
                print(f"✅ Name mapping set: {original_name} → {context['name_mapping'][original_name]}")

    # Manage the single primary city for the story
    print("\n🏙️ Managing location mappings...")
    new_locations = analysis_data.get("locations", [])

    # Step 1: Check if a primary city has been chosen for this story.
    if not context.get("primary_indian_city"):
        # If no city is set, and this chapter has locations, prompt the user to choose one.
        if new_locations:
            print("✨ This is the first time locations are mentioned in this story.")
            print("   Please select a primary Indian city that will be used for ALL locations.")
            for i, city in enumerate(ANCIENT_INDIAN_CITIES, 1):
                print(f"   {i}. {city}")

            while True:
                try:
                    choice = int(input(f"👆 Your choice (1-{len(ANCIENT_INDIAN_CITIES)}): "))
                    if 1 <= choice <= len(ANCIENT_INDIAN_CITIES):
                        selected_city = ANCIENT_INDIAN_CITIES[choice - 1]
                        context["primary_indian_city"] = selected_city
                        print(f"✅ Great! '{selected_city}' will now be the main setting for this story.")
                        break
                    else:
                        print("❌ Invalid choice.")
                except ValueError:
                    print("❌ Invalid input. Please enter a number.")
        else:
            # No locations found in this chapter, so we wait until one is found.
            print("✅ No locations found. The primary city will be chosen when a location first appears.")

    # Step 2: Now that a primary city might exist, map any new locations to it.
    primary_city = context.get("primary_indian_city")
    if primary_city:
        unmapped_locations = filter_new_locations(new_locations, context.get("city_mapping", {}))
        if unmapped_locations:
            print(f"✨ Mapping {len(unmapped_locations)} new location(s) to the primary city '{primary_city}':")
            for loc in unmapped_locations:
                context["city_mapping"][loc] = primary_city
                print(f"   - Mapped: {loc} → {primary_city}")
        else:
            print(f"✅ All mentioned locations are already mapped to '{primary_city}'.")

    # Update character list
    existing_names = {c.get('name') for c in context['all_characters']}
    for char in new_characters_in_chapter:
        if isinstance(char, dict) and char.get('name') and char['name'] not in existing_names:
            context['all_characters'].append(char)

    # Display mapping summary
    print_mapping_summary(context["name_mapping"], context["city_mapping"], chapter_num)

    print(f"\n🌐 Creating Indian context story for Chapter {chapter_num}...")

    # Enhanced adaptation input with city mappings
    adaptation_input = {
        "original_text": text,
        "analysis": analysis_data,
        "previous_summary": context["cumulative_summary"],
        "name_mapping": context["name_mapping"],
        "city_mapping": context["city_mapping"]
    }
    hindi_story = workers["adapter"].process_input(json.dumps(adaptation_input, ensure_ascii=False))

    print("\n🔄 Updating cumulative story summary...")
    updater_input = {
        "previous_summary": context["cumulative_summary"],
        "new_chapter_summary": analysis_data.get("chapter_summary", "")
    }
    new_cumulative_summary = workers["context_updater"].process_input(json.dumps(updater_input))
    if new_cumulative_summary:
        context["cumulative_summary"] = new_cumulative_summary.strip()
        print("✅ Cumulative summary updated.")
    else:
        print("⚠️ Could not update cumulative summary.")

    return hindi_story, context

# Function to let the user select an existing story or create a new one.
def select_or_create_story() -> str:
    """
    Manages story selection. Scans for existing stories, presents a menu to the user,
    and returns the path to the selected or newly created story directory.
    """
    print("--- Story Selection ---")
    os.makedirs(STORIES_BASE_DIR, exist_ok=True)

    existing_stories = [d for d in os.listdir(STORIES_BASE_DIR) if os.path.isdir(os.path.join(STORIES_BASE_DIR, d))]

    if not existing_stories:
        print("No existing stories found.")
    else:
        print("Please choose a story to continue:")
        for i, story_name in enumerate(existing_stories, 1):
            print(f"  {i}. {story_name}")

    print(f"  {len(existing_stories) + 1}. [Create a new story]")
    print(f"  0. Exit")

    while True:
        try:
            choice = int(input("\nYour choice: "))
            if 0 <= choice <= len(existing_stories) + 1:
                break
            else:
                print("❌ Invalid choice. Please try again.")
        except ValueError:
            print("❌ Please enter a number.")

    if choice == 0:
        print("Exiting. Goodbye!")
        exit()
    elif choice == len(existing_stories) + 1:
        # Create a new story
        while True:
            new_story_name = input("Enter a name for your new story: ").strip()
            if not new_story_name:
                print("❌ Story name cannot be empty.")
                continue
            # Sanitize the name to be a valid directory name
            sanitized_name = re.sub(r'[^\w\-_\. ]', '', new_story_name).strip().replace(' ', '_')
            if not sanitized_name:
                print("❌ Invalid story name. Please use letters, numbers, spaces, or underscores.")
                continue

            story_path = os.path.join(STORIES_BASE_DIR, sanitized_name)
            if os.path.exists(story_path):
                print(f"⚠️ A story named '{sanitized_name}' already exists. Please choose a different name.")
            else:
                os.makedirs(story_path)
                print(f"✨ New story '{sanitized_name}' created!")
                return story_path
    else:
        # Select an existing story
        selected_story_name = existing_stories[choice - 1]
        print(f"📖 Continuing story: '{selected_story_name}'")
        return os.path.join(STORIES_BASE_DIR, selected_story_name)

# The main function orchestrates the multi-story workflow.
def main():
    print("---")
    print("📖 Novel Verse: Enhanced Multi-Story Indian Context Creator 📖")
    print("---")

    # Let user select or create a story project
    selected_story_path = select_or_create_story()
    if not selected_story_path:
        return # Exit if something went wrong

    # Load context for the selected story
    story_context = load_context(selected_story_path)

    try:
        text = get_user_text()
        if not text.strip():
            raise ValueError("No input text provided. Please paste the chapter content.")

        # Run the main processing pipeline
        hindi_chapter, updated_context = run_pipeline(text, story_context)

        print("\n" + "=" * 80)
        print(f"✅ FINAL HINDI STORY (Chapter {updated_context.get('chapter_count', 'N/A')}):")
        print("=" * 80)
        print(hindi_chapter)

        # Save everything to the correct story's directory
        save_context(updated_context, selected_story_path)
        if updated_context.get("chapter_count", 0) > 0 and "failed" not in hindi_chapter:
             append_to_full_story(updated_context['chapter_count'], hindi_chapter, selected_story_path)
        print("\n🎉 Process complete for this story!")

    except Exception as e:
        print(f"\n❌ An unexpected error occurred in the main process: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
