import sys
import os
import glob
import datetime
import markdown
import logging
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QLabel, QLineEdit, QComboBox, QPushButton, QTextEdit, 
                            QSplitter, QListWidget, QMessageBox, QStatusBar,
                            QFrame, QProgressBar, QTabWidget)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QDesktopServices

# Import the YouTube processing functionality
from main import CONFIG, AudioDownloader, Transcriber, Summarizer, FileManager, FFmpegHandler

# Import styles
from styles import STYLES

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Constants
OUTPUT_FOLDER = "output"
APP_TITLE = "YouTube Video Summarizer"


class WorkerThread(QThread):
    """Worker thread to handle processing without freezing the UI"""
    update_progress_signal = pyqtSignal(int, str)
    complete_signal = pyqtSignal(bool, str)
    log_signal = pyqtSignal(str, str)  # message, level (info, success, warning, error)
    
    def __init__(self, youtube_url, source_language, output_language):
        super().__init__()
        self.youtube_url = youtube_url
        self.source_language = source_language
        self.output_language = output_language
        self.summary_file_path = ""
        
    def log_info(self, message):
        self.log_signal.emit(message, "info")
        
    def log_success(self, message):
        self.log_signal.emit(message, "success")
        
    def log_warning(self, message):
        self.log_signal.emit(message, "warning")
        
    def log_error(self, message):
        self.log_signal.emit(message, "error")
        
    def run(self):
        try:
            # Update UI
            self.update_progress_signal.emit(10, "Initializing...")
            self.log_info("Starting to process YouTube video")
            
            # Get language names for logging
            source_language_name = next((lang["name"] for lang in CONFIG["languages"] 
                                     if lang["code"] == self.source_language), self.source_language)
            output_language_name = next((lang["name"] for lang in CONFIG["languages"] 
                                     if lang["code"] == self.output_language), self.output_language)
            self.log_info(f"Video language: {source_language_name}")
            self.log_info(f"Summary language: {output_language_name}")
            
            # Generate timestamp for filenames
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Set output filenames
            audio_file = os.path.join(CONFIG["temp_directory"], "downloaded_audio.wav")
            self.summary_file_path = os.path.join(OUTPUT_FOLDER, f"{timestamp}_summary.md")
            
            # Create temp directory if it doesn't exist
            os.makedirs(CONFIG["temp_directory"], exist_ok=True)
            
            # Create output directory if it doesn't exist
            os.makedirs(OUTPUT_FOLDER, exist_ok=True)
            
            # Step 1: Download audio
            self.update_progress_signal.emit(20, "Downloading audio...")
            self.log_info("Downloading audio from YouTube...")
            downloader = AudioDownloader()
            download_success, video_title = downloader.download_from_youtube(self.youtube_url, audio_file)
            
            if not download_success:
                self.log_error("Failed to download audio")
                self.update_progress_signal.emit(0, "Failed to download audio")
                self.complete_signal.emit(False, "Failed to download audio")
                return
            
            self.log_success(f"Downloaded: {video_title}")
            self.update_progress_signal.emit(40, "Audio download complete")
            
            # Step 2: Transcribe audio
            self.log_info("Transcribing audio...")
            self.update_progress_signal.emit(50, "Transcribing audio...")
            
            transcriber = Transcriber()
            transcription = transcriber.transcribe_audio(audio_file, self.source_language)
            
            if not transcription:
                self.log_error("No text was transcribed")
                self.update_progress_signal.emit(0, "Transcription failed")
                self.complete_signal.emit(False, "No text was transcribed")
                return
            
            word_count = len(transcription.split())
            self.log_success(f"Transcription complete ({word_count} words)")
            self.update_progress_signal.emit(70, "Transcription complete")
            
            # Step 3: Summarize transcription
            self.log_info("Generating summary...")
            self.update_progress_signal.emit(75, "Generating summary...")
            
            summarizer = Summarizer(CONFIG["gemini_api_key"])
            summary = summarizer.summarize_text(
                transcription, 
                self.source_language, 
                self.output_language, 
                video_title
            )
            
            summary_word_count = len(summary.split())
            self.log_success(f"Summary generation complete ({summary_word_count} words)")
            self.update_progress_signal.emit(90, "Summary generated")
            
            # Save summary to markdown file
            self.log_info("Saving summary...")
            self.update_progress_signal.emit(95, "Saving summary...")
            
            FileManager.save_to_markdown(summary, self.summary_file_path)
            
            # Clean up temporary files but keep summary
            self.log_info("Cleaning up temporary files...")
            self.update_progress_signal.emit(98, "Cleaning up...")
            
            FileManager.cleanup([self.summary_file_path])
            
            self.log_success("✓ Process completed successfully")
            self.update_progress_signal.emit(100, "Complete!")
            self.complete_signal.emit(True, self.summary_file_path)
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error in worker thread: {error_msg}")
            self.log_error(f"Error occurred: {error_msg}")
            self.update_progress_signal.emit(0, f"Error: {error_msg}")
            self.complete_signal.emit(False, error_msg)


class SummaryViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        # Check for FFmpeg
        if not FFmpegHandler.setup():
            QMessageBox.critical(self, "Error", "FFmpeg is required but not found. Please install FFmpeg and try again.")
            sys.exit(1)
            
        self.setWindowTitle(APP_TITLE)
        self.setGeometry(100, 100, 1200, 800)
        self.showMaximized()  # Start maximized
        
        # Create the output folder if it doesn't exist
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)
            
        self.init_ui()
        self.load_history()
        
    def init_ui(self):
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Apply styles
        self.setStyleSheet(STYLES)
        
        # Add top section for input controls
        top_frame = QFrame()
        top_frame.setObjectName("inputFrame")
        top_layout = QVBoxLayout()
        top_frame.setLayout(top_layout)
        
        # URL input section
        url_layout = QHBoxLayout()
        url_label = QLabel("YouTube URL:")
        url_label.setObjectName("inputLabel")
        self.url_input = QLineEdit()
        self.url_input.setObjectName("urlInput")
        self.url_input.setPlaceholderText("Enter YouTube URL here...")
        
        # Add a paste button for URL
        paste_btn = QPushButton("Paste")
        paste_btn.setObjectName("actionButton")
        paste_btn.clicked.connect(self.paste_url)
        
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        url_layout.addWidget(paste_btn)
        
        # Language selection section
        lang_layout = QHBoxLayout()
        
        # Source language
        source_lang_label = QLabel("Video Language:")
        source_lang_label.setObjectName("inputLabel")
        self.source_lang_combo = QComboBox()
        self.source_lang_combo.setObjectName("comboBox")
        
        # Output language
        output_lang_label = QLabel("Summary Language:")
        output_lang_label.setObjectName("inputLabel")
        self.output_lang_combo = QComboBox()
        self.output_lang_combo.setObjectName("comboBox")
        
        # Populate language combos
        for lang in CONFIG["languages"]:
            self.source_lang_combo.addItem(f"{lang['name']} ({lang['code']})", lang['code'])
            self.output_lang_combo.addItem(f"{lang['name']} ({lang['code']})", lang['code'])
        
        # Set default to English
        default_index = next((i for i, lang in enumerate(CONFIG["languages"]) if lang["code"] == "en-US"), 0)
        self.source_lang_combo.setCurrentIndex(default_index)
        self.output_lang_combo.setCurrentIndex(default_index)
        
        lang_layout.addWidget(source_lang_label)
        lang_layout.addWidget(self.source_lang_combo)
        lang_layout.addWidget(output_lang_label)
        lang_layout.addWidget(self.output_lang_combo)
        
        # Process button
        process_layout = QHBoxLayout()
        self.process_btn = QPushButton("Process Video")
        self.process_btn.setObjectName("primaryButton")
        self.process_btn.clicked.connect(self.process_video)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("%p% %v")
        
        process_layout.addWidget(self.process_btn)
        process_layout.addWidget(self.progress_bar)
        
        # Add layouts to top section
        top_layout.addLayout(url_layout)
        top_layout.addLayout(lang_layout)
        top_layout.addLayout(process_layout)
        
        # Create main splitter for content section
        content_splitter = QSplitter(Qt.Horizontal)
        
        # Left section - History list
        history_frame = QFrame()
        history_frame.setObjectName("historyFrame")
        history_layout = QVBoxLayout()
        history_frame.setLayout(history_layout)
        
        history_label = QLabel("Summary History")
        history_label.setObjectName("sectionHeader")
        self.history_list = QListWidget()
        self.history_list.setObjectName("historyList")
        self.history_list.itemClicked.connect(self.load_summary)
        
        history_btn_layout = QHBoxLayout()
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setObjectName("actionButton")
        refresh_btn.clicked.connect(self.load_history)
        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("actionButton")
        delete_btn.clicked.connect(self.delete_summary)
        
        history_btn_layout.addWidget(refresh_btn)
        history_btn_layout.addWidget(delete_btn)
        
        history_layout.addWidget(history_label)
        history_layout.addWidget(self.history_list)
        history_layout.addLayout(history_btn_layout)
        
        # Right section - Tab widget for Summary and Log
        right_frame = QFrame()
        right_frame.setObjectName("summaryFrame")
        right_layout = QVBoxLayout()
        right_frame.setLayout(right_layout)
        
        # Create tab widget
        tab_widget = QTabWidget()
        tab_widget.setObjectName("contentTabs")
        
        # Summary Tab
        summary_tab = QWidget()
        summary_layout = QVBoxLayout()
        summary_tab.setLayout(summary_layout)
        
        summary_header = QHBoxLayout()
        summary_label = QLabel("Summary Preview")
        summary_label.setObjectName("sectionHeader")
        self.summary_title = QLabel("")
        self.summary_title.setObjectName("summaryTitle")
        
        summary_header.addWidget(summary_label)
        summary_header.addWidget(self.summary_title, 1)  # Add stretch to push title to right
        
        # Summary text area with HTML support
        self.summary_view = QTextEdit()
        self.summary_view.setObjectName("summaryView")
        self.summary_view.setReadOnly(True)
        
        # Summary actions
        summary_actions = QHBoxLayout()
        self.open_btn = QPushButton("Open in Editor")
        self.open_btn.setObjectName("actionButton")
        self.open_btn.clicked.connect(self.open_in_editor)
        self.open_btn.setEnabled(False)
        
        self.copy_btn = QPushButton("Copy to Clipboard")
        self.copy_btn.setObjectName("actionButton")
        self.copy_btn.clicked.connect(self.copy_to_clipboard)
        self.copy_btn.setEnabled(False)
        
        summary_actions.addWidget(self.open_btn)
        summary_actions.addWidget(self.copy_btn)
        summary_actions.addStretch()
        
        summary_layout.addLayout(summary_header)
        summary_layout.addWidget(self.summary_view)
        summary_layout.addLayout(summary_actions)
        
        # Log Tab
        log_tab = QWidget()
        log_layout = QVBoxLayout()
        log_tab.setLayout(log_layout)
        
        log_header = QHBoxLayout()
        log_label = QLabel("Processing Status")
        log_label.setObjectName("sectionHeader")
        
        log_header.addWidget(log_label)
        log_header.addStretch()
        
        # Activity log area
        self.activity_log = QTextEdit()
        self.activity_log.setObjectName("activityLog")
        self.activity_log.setReadOnly(True)
        
        # Log actions
        log_actions = QHBoxLayout()
        clear_log_btn = QPushButton("Clear Log")
        clear_log_btn.setObjectName("actionButton")
        clear_log_btn.clicked.connect(self.clear_log)
        
        copy_log_btn = QPushButton("Copy Log")
        copy_log_btn.setObjectName("actionButton")
        copy_log_btn.clicked.connect(self.copy_log)
        
        log_actions.addWidget(clear_log_btn)
        log_actions.addWidget(copy_log_btn)
        log_actions.addStretch()
        
        log_layout.addLayout(log_header)
        log_layout.addWidget(self.activity_log)
        log_layout.addLayout(log_actions)
        
        # Add tabs to tab widget
        tab_widget.addTab(summary_tab, "Summary")
        tab_widget.addTab(log_tab, "Activity Log")
        
        right_layout.addWidget(tab_widget)
        
        # Set up the splitter
        content_splitter.addWidget(history_frame)
        content_splitter.addWidget(right_frame)
        content_splitter.setStretchFactor(0, 1)  # History gets 1/5 of space
        content_splitter.setStretchFactor(1, 4)  # Content gets 4/5 of space
        
        # Add the top section and content splitter to main layout
        main_layout.addWidget(top_frame)
        main_layout.addWidget(content_splitter, 1)  # Give the splitter the most space
        
        # Add status bar
        self.status_bar = QStatusBar()
        self.status_bar.setObjectName("statusBar")
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")
        
        # Initialize current summary path
        self.current_summary_path = None
        
        # Add welcome message to activity log
        self.add_to_log("Welcome to YouTube Video Summarizer", "info")
        self.add_to_log("Enter a YouTube URL and select languages to begin", "info")

    def add_to_log(self, message, level="info"):
        """Add a user-friendly message to the log with appropriate formatting"""
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        
        # Set color based on message level
        if level == "info":
            color = "#444444"  # Dark gray
            prefix = "ℹ️ "
        elif level == "success":
            color = "#28a745"  # Green
            prefix = "✓ "
        elif level == "warning":
            color = "#ffc107"  # Yellow/amber
            prefix = "⚠️ "
        elif level == "error":
            color = "#dc3545"  # Red
            prefix = "❌ "
        else:
            color = "#444444"
            prefix = ""
        
        # Format and add the message
        formatted_message = f"<span style='color:#888888'>[{timestamp}]</span> <span style='color:{color}'>{prefix}{message}</span>"
        self.activity_log.append(formatted_message)
        
        # Make sure newest log entries are visible
        self.activity_log.verticalScrollBar().setValue(self.activity_log.verticalScrollBar().maximum())
        
        # Also log to system logger if it's an error or warning
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)

    def clear_log(self):
        """Clear the activity log"""
        self.activity_log.clear()
        self.add_to_log("Log cleared", "info")
        
    def copy_log(self):
        """Copy log content to clipboard"""
        if self.activity_log.toPlainText():
            clipboard = QApplication.clipboard()
            clipboard.setText(self.activity_log.toPlainText())
            self.status_bar.showMessage("Log copied to clipboard")
            self.add_to_log("Log copied to clipboard", "info")
        else:
            self.status_bar.showMessage("No log content to copy")

    def paste_url(self):
        """Paste clipboard content to URL input"""
        clipboard = QApplication.clipboard()
        self.url_input.setText(clipboard.text())
        self.add_to_log("URL pasted from clipboard", "info")
    
    def load_history(self):
        """Load summary history from output folder"""
        self.history_list.clear()
        
        # Find all markdown files in the output folder
        summary_files = glob.glob(os.path.join(OUTPUT_FOLDER, "*_summary.md"))
        
        # Sort by modification time, newest first
        summary_files.sort(key=os.path.getmtime, reverse=True)
        
        for file_path in summary_files:
            # Get filename only
            filename = os.path.basename(file_path)
            
            # Try to extract date from filename
            try:
                date_part = filename.split('_')[0]
                date_obj = datetime.datetime.strptime(date_part, "%Y%m%d%H%M%S")
                display_name = date_obj.strftime("%Y-%m-%d %H:%M:%S")
            except:
                display_name = filename
                
            # Add to list with full path as data
            self.history_list.addItem(display_name)
            # Store the full path in the item's data
            self.history_list.item(self.history_list.count() - 1).setData(Qt.UserRole, file_path)
        
        self.add_to_log(f"Loaded {len(summary_files)} summaries from history", "info")
    
    def load_summary(self, item):
        """Load and display selected summary"""
        file_path = item.data(Qt.UserRole)
        if not os.path.exists(file_path):
            QMessageBox.warning(self, "File Not Found", f"The file {file_path} could not be found.")
            self.load_history()  # Refresh the list
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                md_content = f.read()
                
            # Convert Markdown to HTML
            html_content = markdown.markdown(md_content, extensions=['tables', 'fenced_code'])
            
            # Set as current summary
            self.current_summary_path = file_path
            self.summary_title.setText(os.path.basename(file_path))
            
            # Display in the viewer with HTML formatting
            self.summary_view.setHtml(html_content)
            
            # Enable action buttons
            self.open_btn.setEnabled(True)
            self.copy_btn.setEnabled(True)
            
            self.status_bar.showMessage(f"Loaded: {file_path}")
            self.add_to_log(f"Loaded summary: {os.path.basename(file_path)}", "info")
        except Exception as e:
            error_msg = str(e)
            self.status_bar.showMessage(f"Error loading summary: {error_msg}")
            self.add_to_log(f"Error loading summary: {error_msg}", "error")
    
    def delete_summary(self):
        """Delete the selected summary file"""
        current_item = self.history_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "No Selection", "Please select a summary to delete.")
            return
        
        file_path = current_item.data(Qt.UserRole)
        
        # Confirm deletion
        reply = QMessageBox.question(self, 'Confirm Deletion',
                                    f"Are you sure you want to delete this summary?\n{os.path.basename(file_path)}",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            try:
                os.remove(file_path)
                self.status_bar.showMessage(f"Deleted: {file_path}")
                self.add_to_log(f"Deleted summary: {os.path.basename(file_path)}", "info")
                
                # Clear view if this was the current summary
                if self.current_summary_path == file_path:
                    self.summary_view.clear()
                    self.summary_title.setText("")
                    self.current_summary_path = None
                    self.open_btn.setEnabled(False)
                    self.copy_btn.setEnabled(False)
                
                # Refresh the list
                self.load_history()
            except Exception as e:
                error_msg = str(e)
                self.status_bar.showMessage(f"Error deleting file: {error_msg}")
                self.add_to_log(f"Error deleting file: {error_msg}", "error")
    
    def open_in_editor(self):
        """Open the current summary in default application"""
        if self.current_summary_path and os.path.exists(self.current_summary_path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(self.current_summary_path))
            self.add_to_log("Opened summary in external editor", "info")
        else:
            QMessageBox.warning(self, "Error", "No valid summary file is currently selected.")
    
    def copy_to_clipboard(self):
        """Copy summary content to clipboard"""
        if self.summary_view.toPlainText():
            clipboard = QApplication.clipboard()
            clipboard.setText(self.summary_view.toPlainText())
            self.status_bar.showMessage("Summary copied to clipboard")
            self.add_to_log("Summary copied to clipboard", "info")
        else:
            self.status_bar.showMessage("No content to copy")
    
    def process_video(self):
        """Process the YouTube video and generate a summary"""
        # Get inputs
        youtube_url = self.url_input.text().strip()
        if not youtube_url:
            QMessageBox.warning(self, "Input Error", "Please enter a YouTube URL.")
            return
        
        # Get selected language codes
        source_language = self.source_lang_combo.currentData()
        source_language_name = self.source_lang_combo.currentText()
        
        output_language = self.output_lang_combo.currentData()
        output_language_name = self.output_lang_combo.currentText()
        
        # Log the process start
        self.add_to_log("Starting new video processing task", "info")
        self.add_to_log(f"URL: {youtube_url}", "info")
        self.add_to_log(f"Video Language: {source_language_name}", "info")
        self.add_to_log(f"Summary Language: {output_language_name}", "info")
        
        # Disable the process button and show progress
        self.process_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_bar.showMessage("Processing video...")
        
        # Create and start worker thread
        self.worker = WorkerThread(youtube_url, source_language, output_language)
        self.worker.update_progress_signal.connect(self.update_progress)
        self.worker.complete_signal.connect(self.process_complete)
        self.worker.log_signal.connect(self.handle_worker_log)
        self.worker.start()
    
    def handle_worker_log(self, message, level):
        """Handle log messages from worker thread"""
        self.add_to_log(message, level)
    
    def update_progress(self, value, message):
        """Update progress bar and status"""
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(message)
    
    def process_complete(self, success, result):
        """Handle process completion"""
        # Re-enable the process button
        self.process_btn.setEnabled(True)
        
        if success:
            # Refresh the history list
            self.load_history()
            
            # Find and select the new summary
            for i in range(self.history_list.count()):
                item = self.history_list.item(i)
                if item.data(Qt.UserRole) == result:
                    self.history_list.setCurrentItem(item)
                    self.load_summary(item)
                    break
            
            self.status_bar.showMessage("Processing complete!")
            self.add_to_log("Video processing completed successfully", "success")
            QMessageBox.information(self, "Success", "Video processing complete!")
        else:
            self.status_bar.showMessage(f"Error: {result}")
            self.add_to_log(f"Processing failed: {result}", "error")
            QMessageBox.critical(self, "Error", f"An error occurred:\n{result}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SummaryViewer()
    window.show()
    sys.exit(app.exec_())