# AI Journal Assistant 📔

A personal journaling application powered by Google's Gemini 2.0 Flash Lite AI. Keep track of your notes, reminders, shopping lists, and more with natural language processing.

## Features

- 🤖 AI-powered natural language understanding
- 📝 Multiple entry types (notes, reminders, shopping lists)
- 🔍 Smart query system for finding entries
- 📊 Real-time entry tracking
- 🎯 Automatic category detection
- 💬 Conversational interface using Streamlit

## Prerequisites

- Python 3.8 or higher
- Google Gemini API key

## Installation

1. Clone this repository:
```bash
git clone https://github.com/yourusername/AIJournalApp.git
cd AIJournalApp
```

2. Create a `.env` file (if not exists) in the project root and add your Google API key:
```
GOOGLE_API_KEY=your_api_key_here
```

3. Run the setup script:
```bash
# On Windows
python setup.py

# On macOS/Linux
python3 setup.py
```

## Running the App

After setup, start the app with:
```bash
# On Windows
python run.py

# On macOS/Linux
python3 run.py
```

The app will open in your default web browser at `http://localhost:8501`

## Usage Examples

- Add items to shopping list:
  ```
  "Add milk and eggs to my shopping list"
  ```

- Create reminders:
  ```
  "Remind me about the dentist appointment tomorrow at 2pm"
  ```

- Query entries:
  ```
  "Show me my shopping list"
  "What reminders do I have?"
  ```

## Project Structure

- `journal_app.py` - Main application logic and UI
- `run.py` - Cross-platform launcher script
- `setup.py` - Installation and environment setup
- `requirements.txt` - Python dependencies
- `.env` - Environment variables (API keys)

## Dependencies

- streamlit>=1.28.0
- google-genai>=0.3.0 (use google-genai=1.49.0 if facing any issues)
- python-dotenv>=1.0.0

## License

MIT License

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.
