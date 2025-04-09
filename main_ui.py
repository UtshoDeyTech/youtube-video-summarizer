import sys
import os
import datetime
import re
import shutil
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QLabel, QLineEdit, QPushButton, QComboBox, QTextBrowser,
                            QSplitter, QFileDialog, QListWidget, QMessageBox, QProgressBar,
                            QToolButton, QFrame, QSizePolicy)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QFont, QTextOption, QIcon

# Import the YouTube processing functionality from main.py
from main import FFmpegHandler, AudioDownloader, Transcriber, Summarizer, CONFIG, logger
# Import custom styles
from styles import MAIN_STYLE, HTML_STYLE, SUMMARY_CSS

# Add markdown to HTML converter
try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
    print("Markdown module not found. Install with: pip install markdown")
    print("Using plain text display instead.")

# Constants
OUTPUT_FOLDER = "output"  # The folder to store all summaries
TEMP_FOLDER = "temp_files"  # Temporary files during processing

class ProcessingThread(QThread):
    """Thread for handling the YouTube video processing in the background."""
    update_progress = pyqtSignal(int, str)
    finished_signal = pyqtSignal(bool, str, str)  # Success, message, filename

    def __init__(self, youtube_url, language_code):
        super().__init__()
        self.youtube_url = youtube_url
        self.language_code = language_code
        self.config = CONFIG.copy()
        self.config["temp_directory"] = TEMP_FOLDER

    def run(self):
        try:
            # Set up FFmpeg
            self.update_progress.emit(5, "Setting up FFmpeg...")
            if not FFmpegHandler.setup():
                self.finished_signal.emit(False, "FFmpeg setup failed. Please install FFmpeg.", "")
                return

            # Generate timestamp for filenames
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Set output filenames
            os.makedirs(self.config["temp_directory"], exist_ok=True)
            audio_file = os.path.join(self.config["temp_directory"], "downloaded_audio.wav")
            
            # Create output folder for storing summaries if it doesn't exist
            os.makedirs(OUTPUT_FOLDER, exist_ok=True)
            
            # Set the output filename 
            summary_file = os.path.join(OUTPUT_FOLDER, f"{timestamp}_summary.md")
            
            # Step 1: Download audio
            self.update_progress.emit(10, "Downloading YouTube audio...")
            downloader = AudioDownloader()
            download_success, video_title = downloader.download_from_youtube(self.youtube_url, audio_file)
            
            if not download_success:
                self.finished_signal.emit(False, "Failed to download audio. Please check the YouTube URL.", "")
                return
            
            # Update title in summary filename
            sanitized_title = re.sub(r'[\\/*?:"<>|]', "_", video_title)  # Replace invalid filename chars
            truncated_title = sanitized_title[:50]  # Limit length
            summary_file = os.path.join(OUTPUT_FOLDER, f"{timestamp}_{truncated_title}.md")
            
            # Step 2: Transcribe audio
            self.update_progress.emit(30, "Transcribing audio...")
            transcriber = Transcriber(self.config)
            transcription = transcriber.transcribe_audio(audio_file, self.language_code)
            
            if not transcription:
                self.finished_signal.emit(False, "No text was transcribed.", "")
                return
            
            # Step 3: Summarize transcription
            self.update_progress.emit(60, "Generating summary...")
            summarizer = Summarizer(self.config["gemini_api_key"], self.config)
            summary = summarizer.summarize_text(transcription, self.language_code, video_title)
            
            # Save summary to file
            with open(summary_file, "w", encoding="utf-8") as f:
                f.write(summary)
            
            self.update_progress.emit(90, "Cleaning up temporary files...")
            
            # Clean up temporary directory
            if os.path.exists(TEMP_FOLDER):
                shutil.rmtree(TEMP_FOLDER)
            
            self.update_progress.emit(100, "Done!")
            self.finished_signal.emit(True, f"Summary created successfully: {os.path.basename(summary_file)}", summary_file)
            
        except Exception as e:
            logger.error(f"Error in processing thread: {str(e)}")
            self.finished_signal.emit(False, f"An error occurred: {str(e)}", "")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_existing_summaries()
        self.current_summary_file = None
        
    def init_ui(self):
        self.setWindowTitle("YouTube Video Summarizer")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(MAIN_STYLE)
        
        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create header frame
        header_frame = QFrame()
        header_frame.setObjectName("headerFrame")
        header_layout = QVBoxLayout(header_frame)
        
        # App title
        title_label = QLabel("YouTube Video Summarizer")
        title_label.setObjectName("appTitle")
        title_label.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(title_label)
        
        # Input container
        input_container = QFrame()
        input_container.setObjectName("inputContainer")
        input_layout = QHBoxLayout(input_container)
        
        # YouTube URL input
        url_layout = QVBoxLayout()
        url_label = QLabel("YouTube URL:")
        url_label.setObjectName("inputLabel")
        self.url_input = QLineEdit()
        self.url_input.setObjectName("urlInput")
        self.url_input.setPlaceholderText("Enter YouTube URL here")
        url_layout.addWidget(url_label)
        url_layout.addWidget(self.url_input)
        input_layout.addLayout(url_layout, 3)
        
        # Language selection
        language_layout = QVBoxLayout()
        language_label = QLabel("Language:")
        language_label.setObjectName("inputLabel")
        self.language_combo = QComboBox()
        self.language_combo.setObjectName("languageCombo")
        for lang in CONFIG["languages"]:
            self.language_combo.addItem(f"{lang['name']} ({lang['code']})", lang['code'])
        language_layout.addWidget(language_label)
        language_layout.addWidget(self.language_combo)
        input_layout.addLayout(language_layout, 1)
        
        # Process button
        button_layout = QVBoxLayout()
        button_layout.addStretch()
        self.process_btn = QPushButton("Process Video")
        self.process_btn.setObjectName("processButton")
        self.process_btn.clicked.connect(self.process_video)
        button_layout.addWidget(self.process_btn)
        input_layout.addLayout(button_layout, 1)
        
        header_layout.addWidget(input_container)
        
        # Progress bar
        progress_container = QFrame()
        progress_container.setObjectName("progressContainer")
        progress_layout = QVBoxLayout(progress_container)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setObjectName("progressBar")
        self.progress_bar.setVisible(False)
        progress_layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setObjectName("statusLabel")
        self.status_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.status_label)
        
        header_layout.addWidget(progress_container)
        main_layout.addWidget(header_frame)
        
        # Main content area with splitter
        content_frame = QFrame()
        content_frame.setObjectName("contentFrame")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)
        splitter.setObjectName("mainSplitter")
        
        # Left panel (summary list)
        left_panel = QFrame()
        left_panel.setObjectName("leftPanel")
        left_layout = QVBoxLayout(left_panel)
        
        list_header = QFrame()
        list_header.setObjectName("listHeader")
        list_header_layout = QHBoxLayout(list_header)
        
        list_label = QLabel("Saved Summaries")
        list_label.setObjectName("panelTitle")
        list_header_layout.addWidget(list_label)
        
        left_layout.addWidget(list_header)
        
        # Summary list
        self.summary_list = QListWidget()
        self.summary_list.setObjectName("summaryList")
        self.summary_list.itemClicked.connect(self.load_summary)
        left_layout.addWidget(self.summary_list)
        
        # Buttons for managing summaries
        list_buttons_frame = QFrame()
        list_buttons_frame.setObjectName("buttonFrame")
        list_buttons_layout = QHBoxLayout(list_buttons_frame)
        
        self.refresh_btn = QToolButton()
        self.refresh_btn.setObjectName("toolButton")
        self.refresh_btn.setText("↻")
        self.refresh_btn.setToolTip("Refresh list")
        self.refresh_btn.clicked.connect(self.load_existing_summaries)
        list_buttons_layout.addWidget(self.refresh_btn)
        
        self.delete_btn = QToolButton()
        self.delete_btn.setObjectName("toolButton")
        self.delete_btn.setText("🗑")
        self.delete_btn.setToolTip("Delete selected summary")
        self.delete_btn.clicked.connect(self.delete_summary)
        list_buttons_layout.addWidget(self.delete_btn)
        
        list_buttons_layout.addStretch()
        left_layout.addWidget(list_buttons_frame)
        
        # Right panel (summary display)
        right_panel = QFrame()
        right_panel.setObjectName("rightPanel")
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        # Summary header
        summary_header = QFrame()
        summary_header.setObjectName("summaryHeader")
        summary_header_layout = QHBoxLayout(summary_header)
        
        self.summary_title = QLabel("Summary Preview")
        self.summary_title.setObjectName("panelTitle")
        summary_header_layout.addWidget(self.summary_title)
        
        # View mode toggle
        view_toggle_layout = QHBoxLayout()
        
        self.view_formatted_btn = QToolButton()
        self.view_formatted_btn.setObjectName("viewToggleButton")
        self.view_formatted_btn.setText("Preview")
        self.view_formatted_btn.setToolTip("View formatted summary")
        self.view_formatted_btn.setCheckable(True)
        self.view_formatted_btn.setChecked(True)
        self.view_formatted_btn.clicked.connect(lambda: self.toggle_view_mode(True))
        view_toggle_layout.addWidget(self.view_formatted_btn)
        
        self.view_source_btn = QToolButton()
        self.view_source_btn.setObjectName("viewToggleButton")
        self.view_source_btn.setText("Source")
        self.view_source_btn.setToolTip("View source markdown")
        self.view_source_btn.setCheckable(True)
        self.view_source_btn.clicked.connect(lambda: self.toggle_view_mode(False))
        view_toggle_layout.addWidget(self.view_source_btn)
        
        summary_header_layout.addLayout(view_toggle_layout)
        
        # Export button
        self.export_btn = QToolButton()
        self.export_btn.setObjectName("toolButton")
        self.export_btn.setText("⤓")
        self.export_btn.setToolTip("Export summary")
        self.export_btn.clicked.connect(self.export_summary)
        summary_header_layout.addWidget(self.export_btn)
        
        right_layout.addWidget(summary_header)
        
        # Summary display area
        summary_container = QFrame()
        summary_container.setObjectName("summaryContainer")
        summary_container.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        summary_layout = QVBoxLayout(summary_container)
        
        self.summary_display = QTextBrowser()
        self.summary_display.setObjectName("summaryDisplay")
        self.summary_display.setOpenExternalLinks(True)
        self.summary_display.setWordWrapMode(QTextOption.WrapAtWordBoundaryOrAnywhere)
        
        summary_layout.addWidget(self.summary_display)
        right_layout.addWidget(summary_container)
        
        # Add panels to splitter
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setSizes([250, 950])  # Default sizes (20% left, 80% right)
        
        content_layout.addWidget(splitter)
        main_layout.addWidget(content_frame)
        
        self.setCentralWidget(main_widget)
        
        # Create a button group for the view buttons
        self.view_formatted_btn.clicked.connect(lambda: self.view_source_btn.setChecked(False))
        self.view_source_btn.clicked.connect(lambda: self.view_formatted_btn.setChecked(False))
    
    def load_existing_summaries(self):
        """Load existing summary files from the output folder."""
        self.summary_list.clear()
        
        # Create output folder if it doesn't exist
        if not os.path.exists(OUTPUT_FOLDER):
            os.makedirs(OUTPUT_FOLDER)
            self.status_label.setText(f"Created output folder: {OUTPUT_FOLDER}")
            return
        
        # Look for .md files in the output folder
        summary_files = [f for f in os.listdir(OUTPUT_FOLDER) if f.endswith('.md')]
        
        if not summary_files:
            self.status_label.setText("No existing summaries found.")
            return
        
        # Sort files by creation time (newest first)
        summary_files.sort(key=lambda x: os.path.getctime(os.path.join(OUTPUT_FOLDER, x)), reverse=True)
        
        # Add files to the list
        for file in summary_files:
            self.summary_list.addItem(file)
        
        self.status_label.setText(f"Found {len(summary_files)} existing summaries.")
    
    def load_summary(self, item):
        """Load and display a selected summary."""
        filename = item.text()
        file_path = os.path.join(OUTPUT_FOLDER, filename)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.current_summary_file = file_path
            self.summary_title.setText(f"Summary: {filename}")
            
            # Store original content
            self.current_markdown_content = content
            
            # Default to formatted view
            self.view_formatted_btn.setChecked(True)
            self.view_source_btn.setChecked(False)
            self.render_markdown(content)
            
            self.status_label.setText(f"Loaded summary: {filename}")
        except Exception as e:
            self.status_label.setText(f"Error loading summary: {str(e)}")
    
    def toggle_view_mode(self, formatted):
        """Toggle between formatted and source view modes."""
        if not self.current_summary_file:
            return
            
        if formatted:
            self.render_markdown(self.current_markdown_content)
        else:
            self.summary_display.setPlainText(self.current_markdown_content)
    
    def render_markdown(self, content):
        """Render markdown content to HTML for display."""
        if HAS_MARKDOWN:
            try:
                # Convert Markdown to HTML with additional extensions
                html_content = markdown.markdown(
                    content, 
                    extensions=[
                        'markdown.extensions.extra',
                        'markdown.extensions.nl2br',
                        'markdown.extensions.sane_lists'
                    ]
                )
                
                # Add CSS for better rendering
                html_content = f"""
                <html>
                <head>
                <style>
                {HTML_STYLE}
                </style>
                </head>
                <body>
                {html_content}
                </body>
                </html>
                """
                
                self.summary_display.setHtml(html_content)
            except Exception as e:
                self.summary_display.setPlainText(f"Error rendering markdown: {str(e)}\n\n{content}")
        else:
            # Fallback to plain text if markdown module is not available
            self.summary_display.setPlainText(content)
    
    def process_video(self):
        """Process a YouTube video based on the provided URL and language."""
        url = self.url_input.text().strip()
        
        if not url:
            QMessageBox.warning(self, "Input Error", "Please enter a YouTube URL.")
            return
        
        # Get selected language code
        language_code = self.language_combo.currentData()
        
        # Disable UI elements during processing
        self.process_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)
        self.status_label.setText("Starting process...")
        
        # Create and start the processing thread
        self.processing_thread = ProcessingThread(url, language_code)
        self.processing_thread.update_progress.connect(self.update_progress)
        self.processing_thread.finished_signal.connect(self.process_finished)
        self.processing_thread.start()
    
    def update_progress(self, value, message):
        """Update progress bar and status message."""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
    
    def process_finished(self, success, message, filename):
        """Handle completion of video processing."""
        self.process_btn.setEnabled(True)
        
        if success:
            self.status_label.setText(message)
            self.load_existing_summaries()
            
            # Select and load the new summary
            for i in range(self.summary_list.count()):
                if self.summary_list.item(i).text() == os.path.basename(filename):
                    self.summary_list.setCurrentRow(i)
                    self.load_summary(self.summary_list.item(i))
                    break
        else:
            self.progress_bar.setVisible(False)
            QMessageBox.warning(self, "Processing Error", message)
            self.status_label.setText("Ready")
    
    def delete_summary(self):
        """Delete the currently selected summary."""
        current_item = self.summary_list.currentItem()
        if not current_item:
            QMessageBox.information(self, "Selection Required", "Please select a summary to delete.")
            return
        
        filename = current_item.text()
        reply = QMessageBox.question(
            self, 'Confirm Deletion',
            f"Are you sure you want to delete '{filename}'?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                file_path = os.path.join(OUTPUT_FOLDER, filename)
                os.remove(file_path)
                self.load_existing_summaries()
                self.summary_display.clear()
                self.summary_title.setText("Summary Preview")
                self.current_summary_file = None
                self.status_label.setText(f"Deleted: {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Deletion Error", f"Failed to delete file: {str(e)}")
    
    def export_summary(self):
        """Export the current summary to another location."""
        if not self.current_summary_file or not os.path.exists(self.current_summary_file):
            QMessageBox.information(self, "No Summary", "Please select a summary to export.")
            return
        
        # Open file dialog to select destination
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Summary", 
            os.path.basename(self.current_summary_file),
            "Markdown Files (*.md);;Text Files (*.txt);;HTML Files (*.html);;All Files (*)"
        )
        
        if filename:
            try:
                # If exporting as HTML and we have markdown module
                if filename.lower().endswith('.html') and HAS_MARKDOWN:
                    with open(self.current_summary_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    html_content = markdown.markdown(
                        content, 
                        extensions=[
                            'markdown.extensions.extra',
                            'markdown.extensions.nl2br',
                            'markdown.extensions.sane_lists'
                        ]
                    )
                    
                    # Add some styling
                    styled_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{os.path.basename(self.current_summary_file)}</title>
    <style>
    {SUMMARY_CSS}
    </style>
</head>
<body>
    <div class="main-content">
        {html_content}
    </div>
</body>
</html>"""
                    
                    with open(filename, 'w', encoding='utf-8') as f:
                        f.write(styled_html)
                else:
                    # Normal file copy for other formats
                    shutil.copy2(self.current_summary_file, filename)
                
                self.status_label.setText(f"Exported summary to: {filename}")
            except Exception as e:
                QMessageBox.warning(self, "Export Error", f"Failed to export file: {str(e)}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")  # Use Fusion style for a modern look
    
    # Check if markdown module is available, if not, suggest installation
    if not HAS_MARKDOWN:
        print("To enable markdown rendering, install the markdown module:")
        print("pip install markdown")
    
    # Create and show the main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())