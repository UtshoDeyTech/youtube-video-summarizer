import yt_dlp
import speech_recognition as sr
import os
import subprocess
import re
import datetime
import google.generativeai as genai
from pydub import AudioSegment
from pydub.silence import split_on_silence
import concurrent.futures
import logging
import shutil
import glob

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration constants
CONFIG = {
    "chunk_size_ms": 30000,  # 30 seconds
    "max_silence_ms": 1000,  # 1 second
    "silence_threshold": 16,
    "use_parallel": True,
    "max_workers": 4,
    "gemini_api_key": "AIzaSyCvr7e0_1Rg-xKXbXZT4eRN3gDYEY3bVZQ",
    "languages": [
        {"code": "bn-BD", "name": "Bangla"},
        {"code": "en-US", "name": "English"},
        {"code": "hi-IN", "name": "Hindi"}
    ],
    "temp_directory": "temp_files"
}

class FFmpegHandler:
    @staticmethod
    def find_ffmpeg_path():
        """Find FFmpeg path or return None if not found."""
        try:
            result = subprocess.run(['which', 'ffmpeg'], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE, 
                                    text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:  # Specify the exception instead of using bare except
            pass
        
        # Common locations
        common_locations = [
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg'
        ]
        
        for location in common_locations:
            if os.path.exists(location):
                return location
        
        return None

    @staticmethod
    def setup():
        """Set up FFmpeg for audio processing."""
        ffmpeg_path = FFmpegHandler.find_ffmpeg_path()
        if ffmpeg_path:
            logger.info(f"Found FFmpeg at: {ffmpeg_path}")
            AudioSegment.converter = ffmpeg_path
            return True
        else:
            logger.warning("Could not find FFmpeg automatically. Audio processing may fail.")
            return False

class AudioDownloader:
    @staticmethod
    def download_from_youtube(youtube_url, output_path):
        """Download audio from a YouTube video and save it as a WAV file."""
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'wav',
                'preferredquality': '192',
            }],
            'outtmpl': output_path.replace('.wav', ''),
            'noplaylist': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as downloader:
                info = downloader.extract_info(youtube_url, download=False)
                video_title = info.get('title', 'Unknown Title')
                downloader.download([youtube_url])
            logger.info(f"Audio downloaded successfully as {output_path}")
            return True, video_title
        except Exception as e:
            logger.error(f"Error downloading audio: {e}")
            return False, "Unknown Title"

class Transcriber:
    def __init__(self, config=CONFIG):
        self.config = config
        
    def process_chunk(self, chunk_data):
        """Process a single audio chunk in parallel."""
        i, chunk, r, language = chunk_data
        chunk_filename = os.path.join(self.config["temp_directory"], f"temp_chunk_{i}.wav")
        
        try:
            os.makedirs(self.config["temp_directory"], exist_ok=True)
            chunk.export(chunk_filename, format="wav")
            
            results = {}
            
            with sr.AudioFile(chunk_filename) as source:
                audio_data = r.record(source)
                
                try:
                    text = r.recognize_google(audio_data, language=language)
                    results['text'] = text
                except Exception as e:
                    results['text'] = ""
                    results['error'] = str(e)
            
            return i, results
        
        except Exception as e:
            logger.error(f"Error processing chunk {i}: {e}")
            return i, {'error': str(e)}

    def transcribe_audio(self, path, language):
        """Split a large audio file into chunks and transcribe each chunk."""
        logger.info("Loading audio file...")
        sound = AudioSegment.from_wav(path)
        
        logger.info("Creating chunks...")
        chunks = split_on_silence(
            sound,
            min_silence_len=self.config["max_silence_ms"],
            silence_thresh=sound.dBFS - self.config["silence_threshold"],
            keep_silence=500
        )
        
        # Combine small chunks
        combined_chunks = []
        temp_chunk = AudioSegment.empty()
        
        for chunk in chunks:
            if len(temp_chunk) + len(chunk) <= self.config["chunk_size_ms"]:
                temp_chunk += chunk
            else:
                combined_chunks.append(temp_chunk)
                temp_chunk = chunk
        
        if len(temp_chunk) > 0:
            combined_chunks.append(temp_chunk)
        
        chunks = combined_chunks
        logger.info(f"Audio split into {len(chunks)} chunks (optimized)")
        
        # Initialize recognizer
        r = sr.Recognizer()
        
        # Process chunks
        transcribed_text = [""] * len(chunks)
        
        if self.config["use_parallel"] and len(chunks) > 1:
            logger.info(f"Using parallel processing for transcription in {language}...")
            chunk_data = [(i, chunk, r, language) for i, chunk in enumerate(chunks)]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.config["max_workers"]) as executor:
                results = list(executor.map(self.process_chunk, chunk_data))
                
                for i, result_dict in results:
                    if 'text' in result_dict:
                        transcribed_text[i] = result_dict['text']
                        if transcribed_text[i]:
                            logger.info(f"Chunk {i+1}/{len(chunks)} transcribed: {transcribed_text[i][:30]}...")
                        else:
                            logger.info(f"Chunk {i+1}/{len(chunks)}: No text transcribed")
        else:
            # Process sequentially
            logger.info(f"Processing chunks sequentially in {language}...")
            for i, chunk in enumerate(chunks):
                i, result_dict = self.process_chunk((i, chunk, r, language))
                
                if 'text' in result_dict:
                    transcribed_text[i] = result_dict['text']
                    if transcribed_text[i]:
                        logger.info(f"Chunk {i+1}/{len(chunks)} transcribed: {transcribed_text[i][:30]}...")
                    else:
                        logger.info(f"Chunk {i+1}/{len(chunks)}: No text transcribed")
        
        # Combine all transcribed text
        full_transcription = " ".join([text for text in transcribed_text if text])
        
        return full_transcription

class Summarizer:
    def __init__(self, api_key, config=CONFIG):
        self.api_key = api_key
        self.config = config
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        self.generation_config = {
            "temperature": 0.3,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
    
    def split_text_into_chunks(self, text, max_chunk_size=4000):
        """Split text into chunks at sentence boundaries."""
        if len(text) <= max_chunk_size:
            return [text]
        
        sentence_boundaries = r'([।!?])'
        sentences = re.split(sentence_boundaries, text)
        
        combined_sentences = []
        for i in range(0, len(sentences)-1, 2):
            if i+1 < len(sentences):
                combined_sentences.append(sentences[i] + sentences[i+1])
            else:
                combined_sentences.append(sentences[i])
        
        if len(sentences) % 2 == 1:
            combined_sentences.append(sentences[-1])
        
        chunks = []
        current_chunk = ""
        
        for sentence in combined_sentences:
            if len(current_chunk) + len(sentence) > max_chunk_size:
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = sentence
            else:
                current_chunk += sentence
        
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks
    
    def get_prompts(self, language_code, video_title):
        """Get enhanced universal prompts with language-specific output instructions."""
        # Define language display name for prompt instructions
        language_display_name = next(
            (lang["name"] for lang in self.config["languages"] if lang["code"] == language_code), 
            "the detected language"
        )
        
        first_chunk_prompt = f"""Analyze and summarize the following transcript text thoroughly. Your output must be in {language_display_name} language.

First, try to identify:
1. The core topic or theme of the content
2. The speaker's main purpose or objective
3. The target audience
4. The key message being conveyed

Then create a summary following this format:

1. Brief Introduction: Write a concise paragraph that captures the essence of the content, including who is speaking, the overall purpose, and why this content matters.

2. Present the main points as detailed bullet points:
   • Each bullet point should capture a complete thought or concept
   • Make the bullets information-rich with concrete details, not vague statements
   • Each bullet should be clear, precise, and focused on one key idea
   • Add sub-bullets where needed to provide important supporting details or examples
   • Use direct quotes when particularly significant

Remember this is the first part of a larger transcript, so identify recurring themes that may continue throughout the content."""

        middle_chunk_prompt = f"""Continue analyzing this middle section of the transcript. Your output must be in {language_display_name} language.

First, check if this section:
1. Introduces new topics or themes
2. Elaborates on previously mentioned concepts
3. Presents opposing viewpoints or alternative perspectives
4. Provides examples, case studies or evidence

Then create a summary following this format:

1. Brief Connector: Write a brief sentence or two connecting this section to the previous content.

2. Present the main points of this section as detailed bullet points:
   • Focus on new information and insights, not repeating previous sections
   • Make each bullet point substantial with specific facts, examples or explanations
   • Use clear, precise language to capture complex ideas
   • Include sub-bullets to highlight nested concepts or important details
   • Note any significant changes in tone, perspective, or focus

Be attentive to the speaker's emphasis, repetition, or emotional cues that indicate important points."""

        last_chunk_prompt = f"""This is the final part of the transcript. Analyze it carefully while reflecting on the entire content. Your output must be in {language_display_name} language.

First, identify:
1. How the speaker concludes their message
2. Any final key points or takeaways emphasized
3. The overall message and purpose of the entire transcript
4. The significance or implications of this content

Then create a comprehensive summary following this format:

1. Section Summary: Summarize just this final section in a short paragraph.

2. Key points from this final section:
   • List the unique points from this final section as detailed bullets
   • Include significant concluding remarks or calls to action
   • Note any solutions, recommendations, or future directions mentioned

3. Overall Analysis:
   • What is the main thesis or central message of the entire transcript?
   • What are the most significant points across the entire content?
   • Who would benefit most from this information and why?
   • What is the speaker's perspective or approach to the topic?

This final section should help tie together all the content into a coherent whole."""

        consolidation_prompt = f"""Create a comprehensive, in-depth markdown summary of this YouTube video transcript. Your output must be entirely in {language_display_name} language.

Video Title: "{video_title}"

First, analyze the content to understand:
1. The core purpose and main themes of the video
2. The expertise and perspective of the speaker
3. The intended audience and why this content matters to them
4. The unique insights, strategies, or knowledge being shared

Then create a polished, detailed markdown summary with these components:

# Title: "{video_title}"

## Overview
Write a substantive introductory paragraph (around 4-5 sentences) that:
- Establishes the context and subject matter
- Identifies the speaker/creator and their qualifications (if known)
- Clearly states the main purpose of the video
- Explains why this content is valuable or important
- Captures the essence of what viewers will learn

## Key Insights
Create detailed, informative bullet points that dive deep into the content:
* Each main point should be a complete thought that captures a significant concept
* Organize points in logical order of importance or as they build upon each other
* Use rich, specific language with concrete examples rather than vague generalizations
* Include exact figures, statistics, or quotes when available
* Add indented sub-bullets to break down complex points:
  * Use sub-bullets for supporting evidence, examples, or step-by-step explanations
  * Include nuance, exceptions, or alternative perspectives
  * Highlight practical applications or implementation details

## Main Takeaways
Summarize the 3-5 most important lessons or actionable insights from the video:
* Focus on practical, applicable knowledge
* Highlight transformative ideas or paradigm shifts
* Include specific actions viewers can take based on this information

## Conclusion
Write a thoughtful concluding paragraph that:
- Reinforces the central message
- Connects the content to broader themes or implications
- Explains why this information matters in the bigger picture
- Notes any limitations or considerations for applying this knowledge

Your summary should be comprehensive, well-structured, and capture both the letter and spirit of the content. Use proper markdown formatting throughout with correct heading levels, bullet points, and paragraph breaks. The goal is to provide a reader with a thorough understanding of the video's content even if they haven't watched it.

Remember to maintain the original tone and perspective of the speaker while ensuring the summary is objective, accurate, and valuable to the reader."""
        
        return {
            "first_chunk": first_chunk_prompt,
            "middle_chunk": middle_chunk_prompt,
            "last_chunk": last_chunk_prompt,
            "consolidation": consolidation_prompt
        }
    
    def summarize_text(self, input_text, language_code, video_title, chunk_size=4000):
        """Summarize text using Gemini API with enhanced analytical approach."""
        # Split the text into manageable chunks
        text_chunks = self.split_text_into_chunks(input_text, chunk_size)
        logger.info(f"Text split into {len(text_chunks)} chunks for processing")
        
        # Get enhanced prompts
        prompts = self.get_prompts(language_code, video_title)
        
        # Process each chunk with enhanced analysis
        chunk_summaries = []
        
        for i, chunk in enumerate(text_chunks):
            logger.info(f"Processing chunk {i+1}/{len(text_chunks)} with enhanced analysis...")
            
            if i == 0:
                # First chunk
                system_prompt = prompts["first_chunk"]
            elif i == len(text_chunks) - 1:
                # Last chunk
                system_prompt = prompts["last_chunk"]
            else:
                # Middle chunks
                system_prompt = prompts["middle_chunk"]
            
            try:
                response = self.model.generate_content(
                    contents=[{"role": "user", "parts": [{"text": f"{system_prompt}\n\n{chunk}"}]}],
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
                
                chunk_summaries.append(response.text)
                logger.info(f"Chunk {i+1} processed successfully with enhanced analysis")
                
            except Exception as e:
                logger.error(f"Error processing chunk {i+1}: {e}")
                # Use a universal error message format
                error_message = "Error processing this section"
                chunk_summaries.append(f"[{error_message}: {str(e)}]")
        
        # Create final consolidated summary with enhanced insights
        if len(chunk_summaries) > 1:
            logger.info("Creating final consolidated summary with comprehensive analysis...")
            
            try:
                response = self.model.generate_content(
                    contents=[{"role": "user", "parts": [{"text": f"{prompts['consolidation']}\n\n{''.join(chunk_summaries)}"}]}],
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
                return response.text
            except Exception as e:
                logger.error(f"Error during final consolidation: {e}")
                # Return all chunk summaries if consolidation fails
                return "\n\n".join(chunk_summaries)
        else:
            # Format single chunk as markdown with a universal format
            # For a single chunk, we'll still want to get a comprehensive summary
            try:
                # Get language display name for the prompt
                language_display_name = next(
                    (lang["name"] for lang in self.config["languages"] if lang["code"] == language_code), 
                    "the detected language"
                )
                
                # Create a simplified consolidation prompt for single chunks
                single_chunk_prompt = f"""Create a comprehensive markdown summary of this YouTube video transcript. Your output must be entirely in {language_display_name} language.

Video Title: "{video_title}"

Based on the transcript analysis provided, create a well-structured summary that:

# Title: "{video_title}"

## Overview
Write a substantive introduction that captures the essence of the content.

## Key Insights
Create detailed, informative bullet points that dive deep into the main points.
* Use rich, specific language with concrete examples
* Add indented sub-bullets to break down complex points

## Main Takeaways
Summarize the most important lessons or actionable insights.

## Conclusion
Write a thoughtful concluding paragraph that reinforces the central message.

Use proper markdown formatting throughout with correct heading levels, bullet points, and paragraph breaks."""

                # Try to get a more comprehensive single-chunk summary
                response = self.model.generate_content(
                    contents=[{"role": "user", "parts": [{"text": f"{single_chunk_prompt}\n\n{chunk_summaries[0]}"}]}],
                    generation_config=self.generation_config,
                    safety_settings=self.safety_settings
                )
                return response.text
            except Exception as e:
                logger.error(f"Error creating single chunk comprehensive summary: {e}")
                # Fall back to original content if the enhanced approach fails
                formatted_text = f"""# {video_title}

{chunk_summaries[0]}
"""
                return formatted_text

class FileManager:
    @staticmethod
    def cleanup(keep_files=None):
        """
        Clean up temporary files generated during execution, keeping only the specified files.
        Only deletes temporary files, not the main Python files.
        
        Args:
            keep_files: List of filenames or filename prefixes to keep
        """
        if keep_files is None:
            keep_files = []
        
        # Remove temp directory and its contents
        if os.path.exists(CONFIG["temp_directory"]):
            try:
                shutil.rmtree(CONFIG["temp_directory"])
                logger.info(f"Removed temporary directory: {CONFIG['temp_directory']}")
            except Exception as e:
                logger.error(f"Error removing temporary directory: {e}")
        
        # Delete only temporary audio files and other generated files
        # List of temporary file patterns to delete
        temp_patterns = [
            "downloaded_audio.wav",        # Downloaded audio
            "*.wav",                       # Any other WAV files
            "temp_chunk_*.wav",            # Temporary audio chunks
            "*.mp3"                        # Any other audio files
        ]
        
        # Find files matching temp patterns that aren't in keep_files
        for pattern in temp_patterns:
            matching_files = glob.glob(pattern)
            for file in matching_files:
                # Skip if the file should be kept
                if file in keep_files or any(file.startswith(keep) for keep in keep_files):
                    continue
                
                try:
                    os.remove(file)
                    logger.info(f"Removed temporary file: {file}")
                except Exception as e:
                    logger.error(f"Error removing file {file}: {e}")

    @staticmethod
    def save_to_markdown(content, filepath):
        """Save content to a markdown file."""
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"Content saved to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving content to {filepath}: {e}")
            return False

class YouTubeProcessor:
    def __init__(self, config=CONFIG):
        self.config = config
        self.transcriber = Transcriber(config)
        self.summarizer = Summarizer(config["gemini_api_key"], config)
        
    def process_video(self, youtube_url, language_code):
        """Process a YouTube video: download, transcribe, and summarize."""
        # Generate timestamp for filenames
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Set output filenames
        audio_file = os.path.join(self.config["temp_directory"], "downloaded_audio.wav")
        transcription_file = f"{timestamp}_transcription.md"
        summary_file = f"{timestamp}_summary.md"
        
        # Get language name
        language_name = next((lang["name"] for lang in self.config["languages"] 
                             if lang["code"] == language_code), language_code)
        
        logger.info(f"Starting to process YouTube video: {youtube_url}")
        logger.info(f"Selected language: {language_name} ({language_code})")
        
        # Create temp directory if it doesn't exist
        os.makedirs(self.config["temp_directory"], exist_ok=True)
        
        # Step 1: Download audio
        downloader = AudioDownloader()
        download_success, video_title = downloader.download_from_youtube(youtube_url, audio_file)
        
        if not download_success:
            logger.error("Failed to download audio. Please check the YouTube URL and try again.")
            return False
        
        # Step 2: Transcribe audio
        logger.info("Starting transcription process...")
        transcription = self.transcriber.transcribe_audio(audio_file, language_code)
        
        if not transcription:
            logger.error("No text was transcribed.")
            return False
        
        # Save transcription to markdown file
        FileManager.save_to_markdown(transcription, transcription_file)
        
        # Step 3: Summarize transcription
        logger.info("Starting summarization process...")
        try:
            summary = self.summarizer.summarize_text(transcription, language_code, video_title)
            
            # Save summary to markdown file
            FileManager.save_to_markdown(summary, summary_file)
            
            logger.info("Summarization completed successfully!")
            logger.info(f"Files saved: {transcription_file}, {summary_file}")
            
            # Clean up temporary files
            files_to_keep = [transcription_file, summary_file]
            FileManager.cleanup(files_to_keep)
            
            return True
            
        except Exception as e:
            logger.error(f"An error occurred during summarization: {e}")
            return False

def display_language_menu(languages):
    """Display a menu of available languages and get user selection."""
    print("\n----- AVAILABLE LANGUAGES -----")
    for i, lang in enumerate(languages, 1):
        print(f"{i}. {lang['name']} ({lang['code']})")
    
    while True:
        try:
            choice = int(input("\nSelect language [1-{}]: ".format(len(languages))))
            if 1 <= choice <= len(languages):
                return languages[choice-1]["code"]
            else:
                print(f"Please enter a number between 1 and {len(languages)}")
        except ValueError:
            print("Please enter a valid number")

def main():
    # Setup
    if not FFmpegHandler.setup():
        logger.error("FFmpeg is required for audio processing. Please install it and try again.")
        return
    
    # Get YouTube URL
    youtube_url = input("Enter YouTube URL: ").strip()
    
    # Display language menu and get selection
    selected_language = display_language_menu(CONFIG["languages"])
    
    # Process the video
    processor = YouTubeProcessor()
    processor.process_video(youtube_url, selected_language)

if __name__ == "__main__":
    main()