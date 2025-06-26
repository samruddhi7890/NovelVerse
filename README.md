# NovelVerse

📖 NovelVerse: Multi-Story Indian Context Creator 📖

Translate and Culturally Adapt Light Novels to Hindi

🚀 Overview:

NovelVerse is a Python backend application for translating light novel chapters from English into Hindi, incorporating cultural adaptations like Indian character names and geographical locations. It supports managing multiple novel projects simultaneously, maintaining context for each. This project serves as the core translation engine, with future plans for full web and mobile UI integration.

✨ Key Features

Chapter Translation: Translates pasted English chapter text into Hindi.

Cultural Mapping: Automatically adapts foreign character names and locations to Indian equivalents, ensuring cultural relevance.

Story Continuation: Maintains narrative flow across chapters by leveraging cumulative story context.

Multi-Story Support: Work on and manage multiple novel translation projects concurrently, each with dedicated storage.

⚙️ Setup and Installation

Prerequisites: Python 3.x, Git (optional), and a Groq API Key.

Clone/Download: Get the project files.

git clone https://github.com/samruddhi7890/NovelVerse.git

cd NovelVerse

Virtual Environment: Create and activate a Python virtual environment.

python -m venv .venv

Activate:

macOS / Linux: source .venv/bin/activate

Windows: .\.venv\Scripts\activate

Install Dependencies:

pip install langchain-groq python-dotenv

Configure API Key: Create a .env file in the project root with your Groq API key:

GROQ_API_KEY="your_actual_groq_api_key_here"

(This file is ignored by Git for security.)

🚀 Usage:

Activate your virtual environment.

Run the script:

python app.py

Follow Console Prompts:

Choose to create a new story or continue an existing one.

Paste English chapter content when prompted.

Interactively select Indian names for new characters and a primary Indian city for the story's setting (for the first chapter).

Translated Hindi chapters will be displayed in the console and saved to stories/<your_story_name>/full_hindi_story.txt.

🛣️ Future Enhancements:

Improve translation quality through user feedback (LLM fine-tuning).

Develop full web and mobile user interfaces.

Integrate database for more robust data management.

Implement user authentication, community features, and content organization.

Plan for live deployment.
