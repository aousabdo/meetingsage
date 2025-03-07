# MeetingSage 🎙️

MeetingSage is an AI-powered meeting assistant that transcribes, summarizes, and extracts action items from your meetings, helping you capture important information and follow up on commitments.

## Features

- **Audio Recording**: Record meetings directly through the web interface or upload existing audio files
- **Transcription**: Convert speech to text using OpenAI's advanced speech recognition technology
- **Summarization**: Generate concise summaries of meeting content using AI
- **Action Item Extraction**: Automatically identify and track action items from meeting discussions
- **Meeting Management**: Save, view, and search through past meetings
- **MongoDB Integration**: Store meeting data securely in MongoDB with fallback to local storage

## Installation

### Prerequisites

- Python 3.8+ 
- MongoDB account (optional, app will work with local storage if not available)
- OpenAI API key

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/aousabdo/meetingsage.git
   cd meetingsage
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the project root directory with the following variables:
   ```
   # MongoDB Configuration (optional)
   MONGODB_URI=your_mongodb_connection_string
   MONGODB_DB_NAME=meetingsage

   # OpenAI API Key (required)
   OPENAI_API_KEY=your_openai_api_key

   # App configuration
   DEBUG=True
   ```

## Usage

1. Start the application:
   ```bash
   streamlit run app.py
   ```

2. Open your web browser and navigate to the provided URL (typically http://localhost:8501)

3. Create a new meeting:
   - Enter a meeting title
   - Record audio or upload an audio file
   - Click "Process Recording" to transcribe and analyze the meeting

4. View meeting details:
   - See the meeting summary and extracted action items
   - Review the full transcript
   - Add, edit, or delete action items

## Project Structure

```
meetingsage/
├── app.py                 # Main Streamlit application
├── config.py              # Configuration settings
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (gitignored)
├── .gitignore             # Git ignore file
├── README.md              # Project documentation
├── test_api.py            # API testing script
├── test_mongodb.py        # MongoDB testing script
│
├── components/            # UI components
│   ├── __init__.py        # Package initialization
│   ├── action_items.py    # Action item UI components
│   ├── meeting_list.py    # Meeting list display components
│   ├── recorder.py        # Audio recording components
│   ├── sidebar.py         # Sidebar navigation
│   └── transcript_view.py # Transcript display components
│
├── models/                # Data models
│   ├── __init__.py        # Package initialization
│   ├── meeting.py         # Meeting data model
│   └── user.py            # User data model
│
├── utils/                 # Utility functions
│   ├── __init__.py        # Package initialization
│   ├── analysis.py        # Meeting analysis tools
│   ├── audio.py           # Audio processing utilities
│   ├── database.py        # MongoDB integration
│   ├── mock_database.py   # Local storage fallback
│   ├── summarization.py   # Text summarization
│   └── transcription.py   # Speech-to-text functionality
│
├── mock_db/               # Local storage directory
└── temp_audio/            # Temporary audio storage
```

## Technologies Used

- **Streamlit**: Frontend web application framework
- **OpenAI API**: Transcription and AI analysis
- **MongoDB**: Database storage (with local fallback)
- **Flask**: Secondary API server for background processing
- **WebRTC**: Real-time audio recording

## Development

### Environment Variables

Create a copy of the `.env.example` file as `.env` and fill in your specific configuration:

```
# MongoDB Configuration
MONGODB_URI=your_mongodb_connection_string
MONGODB_DB_NAME=meetingsage

# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key

# App configuration
DEBUG=True
```

### Local Development

1. Install development dependencies:
   ```bash
   pip install -r requirements-dev.txt  # If you have a separate dev requirements file
   ```

2. Run the application in debug mode:
   ```bash
   streamlit run app.py
   ```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- OpenAI for providing the API for transcription and text analysis
- Streamlit for the amazing web app framework
- All contributors who have helped shape this project
