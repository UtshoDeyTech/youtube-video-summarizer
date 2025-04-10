# YouTube Video Transcriber and Summarizer

A Python application that automatically transcribes YouTube videos, generates summaries in multiple languages, and provides a user-friendly interface to manage and view transcriptions.

## Features

- **Multi-language Support**: Transcribe videos in 10 languages including English, Spanish, Hindi, Chinese, and more
- **Cross-language Summaries**: Generate summaries in a different language than the original video
- **AI-Powered Summaries**: Uses Google's Gemini API for intelligent summarization
- **User-friendly Interface**: Clean GUI with summary history, markdown preview, and process tracking
- **Parallel Processing**: Optimized for faster transcription using multithreading

## Installation

### Prerequisites

- Python 3.7+
- FFmpeg (required for audio processing)

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/youtube-transcriber.git
   cd youtube-transcriber
   ```

2. Install required packages:
   ```
   pip install -r requirements.txt
   ```

3. Ensure FFmpeg is installed on your system:
   - **Linux**: `sudo apt-get install ffmpeg`
   - **macOS**: `brew install ffmpeg`
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)

4. Add your Gemini API key:
   - Get an API key from [Google AI Studio](https://aistudio.google.com/)
   - Replace the placeholder API key in the `CONFIG` variable in `main.py`

## Usage

### Command Line Interface

Run the script with:

```
python main.py
```

Follow the prompts to:
1. Enter a YouTube URL
2. Select the source language (the language of the video)
3. Select the output language (the language you want the summary in)

### Graphical Interface

Launch the GUI with:

```
python main_ui.py
```

The interface allows you to:
- Enter YouTube URLs
- Select source and target languages
- View processing progress
- Browse summary history
- View and export generated summaries

## How It Works

1. **Download**: Extracts audio from YouTube videos using yt-dlp
2. **Transcribe**: Splits audio into chunks and uses Google's Speech Recognition API
3. **Summarize**: Processes the transcription with Gemini API to generate a structured summary
4. **Output**: Saves results as markdown files with timestamps

## Supported Languages

- Arabic
- Bangla
- Chinese (Simplified)
- English
- French
- German
- Hindi
- Japanese
- Korean
- Spanish

## Optimization Tips

For faster processing:
- Increase `max_workers` in the CONFIG for more parallel processing
- Adjust `chunk_size_ms` for optimal audio chunk sizes
- Consider using paid APIs like OpenAI Whisper for better performance

## License

[MIT License](LICENSE)

## Acknowledgements

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) for YouTube video downloading
- [SpeechRecognition](https://github.com/Uberi/speech_recognition) for audio transcription
- [pydub](https://github.com/jiaaro/pydub) for audio processing
- [Google Gemini API](https://ai.google.dev/) for AI summarization