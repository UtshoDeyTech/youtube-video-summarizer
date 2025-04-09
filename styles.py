# styles.py - CSS styling for the YouTube Video Summarizer application

# Main application styles
MAIN_STYLE = """
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
    color: #333333;
    background-color: #ffffff;
}

#headerFrame {
    background-color: #1e3a8a;
    color: white;
    padding: 10px;
    border-bottom: 1px solid #0f2361;
}

#appTitle {
    font-size: 18pt;
    font-weight: bold;
    color: white;
    margin-bottom: 10px;
}

#inputContainer {
    background-color: #ffffff;
    border-radius: 8px;
    padding: 15px;
    margin: 10px 0;
}

#inputLabel {
    font-weight: bold;
    color: #1e3a8a;
}

QLineEdit, QComboBox {
    padding: 8px;
    border: 1px solid #c0c0c0;
    border-radius: 4px;
    background-color: #f8f8f8;
}

QLineEdit:focus, QComboBox:focus {
    border: 1px solid #1e3a8a;
    background-color: white;
}

#urlInput {
    font-size: 11pt;
}

#processButton {
    background-color: #1e3a8a;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 10px 20px;
    font-weight: bold;
}

#processButton:hover {
    background-color: #2a4cad;
}

#processButton:pressed {
    background-color: #0f2361;
}

#processButton:disabled {
    background-color: #9ca3af;
}

#progressContainer {
    margin: 5px 20px;
}

#progressBar {
    border: none;
    border-radius: 3px;
    background-color: #e5e7eb;
    height: 20px;
    text-align: center;
}

#progressBar::chunk {
    background-color: #1e3a8a;
    border-radius: 3px;
}

#statusLabel {
    color: #4b5563;
    font-style: italic;
    margin-top: 5px;
}

#contentFrame {
    background-color: #f3f4f6;
}

#mainSplitter::handle {
    background-color: #d1d5db;
}

#leftPanel, #rightPanel {
    background-color: white;
}

#leftPanel {
    min-width: 200px;
    max-width: 350px;
}

#rightPanel {
    min-width: 300px;
}

#listHeader, #summaryHeader {
    background-color: #f9fafb;
    border-bottom: 1px solid #e5e7eb;
    padding: 10px;
}

#panelTitle {
    font-weight: bold;
    color: #1e3a8a;
    font-size: 12pt;
}

#summaryList {
    border: none;
    background-color: white;
    font-size: 10pt;
}

#summaryList::item {
    padding: 8px;
    border-bottom: 1px solid #f3f4f6;
}

#summaryList::item:selected {
    background-color: #e5edff;
    color: #1e3a8a;
}

#summaryList::item:hover {
    background-color: #f9fafb;
}

#buttonFrame {
    background-color: #f9fafb;
    border-top: 1px solid #e5e7eb;
    padding: 8px;
}

#toolButton, #viewToggleButton {
    background-color: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 6px;
    font-size: 10pt;
}

#toolButton:hover, #viewToggleButton:hover {
    background-color: #e5e7eb;
}

#toolButton:pressed, #viewToggleButton:pressed {
    background-color: #d1d5db;
}

#viewToggleButton:checked {
    background-color: #1e3a8a;
    color: white;
    border: 1px solid #0f2361;
}

#summaryContainer {
    padding: 0;
    background-color: white;
}

#summaryDisplay {
    border: none;
    background-color: white;
    font-size: 11pt;
    line-height: 1.5;
    padding: 15px;
}
"""

# HTML styles for markdown rendering
HTML_STYLE = """
body {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.6;
    color: #333333;
    padding: 10px;
    margin: 0;
}

h1 {
    font-size: 20pt;
    font-weight: bold;
    color: #1e3a8a;
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e5e7eb;
}

h2 {
    font-size: 16pt;
    font-weight: bold;
    color: #2563eb;
    margin-top: 24px;
    margin-bottom: 12px;
}

h3 {
    font-size: 14pt;
    font-weight: bold;
    color: #3b82f6;
    margin-top: 20px;
    margin-bottom: 10px;
}

h4 {
    font-size: 12pt;
    font-weight: bold;
    color: #60a5fa;
    margin-top: 16px;
    margin-bottom: 8px;
}

p {
    margin-bottom: 14px;
}

ul, ol {
    padding-left: 30px;
    margin-bottom: 16px;
}

li {
    margin-bottom: 6px;
}

blockquote {
    margin: 15px 0;
    padding: 10px 20px;
    background-color: #f9fafb;
    border-left: 4px solid #2563eb;
    color: #4b5563;
}

code {
    font-family: Consolas, Monaco, 'Courier New', monospace;
    background-color: #f1f5f9;
    padding: 2px 4px;
    border-radius: 3px;
    font-size: 0.9em;
}

pre {
    background-color: #f1f5f9;
    padding: 10px;
    border-radius: 5px;
    overflow-x: auto;
    margin-bottom: 16px;
}

pre code {
    background-color: transparent;
    padding: 0;
}

a {
    color: #2563eb;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 20px 0;
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 20px 0;
}

th, td {
    border: 1px solid #e5e7eb;
    padding: 8px 12px;
}

th {
    background-color: #f9fafb;
    font-weight: bold;
    text-align: left;
}

tr:nth-child(even) {
    background-color: #f9fafb;
}

tr:hover {
    background-color: #f3f4f6;
}

hr {
    border: 0;
    height: 1px;
    background-color: #e5e7eb;
    margin: 20px 0;
}
"""

# CSS for exported HTML summaries
SUMMARY_CSS = """
body {
    font-family: 'Segoe UI', Arial, sans-serif;
    line-height: 1.6;
    color: #333333;
    max-width: 900px;
    margin: 0 auto;
    padding: 30px;
    background-color: #f9fafb;
}

.main-content {
    background-color: white;
    padding: 40px;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

h1 {
    font-size: 24pt;
    font-weight: bold;
    color: #1e3a8a;
    margin-bottom: 20px;
    padding-bottom: 15px;
    border-bottom: 2px solid #e5e7eb;
}

h2 {
    font-size: 18pt;
    font-weight: bold;
    color: #2563eb;
    margin-top: 30px;
    margin-bottom: 15px;
}

h3 {
    font-size: 16pt;
    font-weight: bold;
    color: #3b82f6;
    margin-top: 25px;
    margin-bottom: 12px;
}

h4 {
    font-size: 14pt;
    font-weight: bold;
    color: #60a5fa;
    margin-top: 20px;
    margin-bottom: 10px;
}

p {
    margin-bottom: 16px;
    font-size: 12pt;
}

ul, ol {
    padding-left: 30px;
    margin-bottom: 20px;
    font-size: 12pt;
}

li {
    margin-bottom: 8px;
}

blockquote {
    margin: 20px 0;
    padding: 15px 25px;
    background-color: #f3f4f6;
    border-left: 5px solid #2563eb;
    color: #4b5563;
    font-style: italic;
}

code {
    font-family: Consolas, Monaco, 'Courier New', monospace;
    background-color: #f1f5f9;
    padding: 3px 6px;
    border-radius: 4px;
    font-size: 11pt;
}

pre {
    background-color: #f1f5f9;
    padding: 15px;
    border-radius: 6px;
    overflow-x: auto;
    margin-bottom: 20px;
    font-size: 11pt;
}

pre code {
    background-color: transparent;
    padding: 0;
}

a {
    color: #2563eb;
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 25px auto;
    border-radius: 6px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

table {
    border-collapse: collapse;
    width: 100%;
    margin: 25px 0;
    font-size: 12pt;
}

th, td {
    border: 1px solid #e5e7eb;
    padding: 12px 16px;
}

th {
    background-color: #f3f4f6;
    font-weight: bold;
    text-align: left;
}

tr:nth-child(even) {
    background-color: #f9fafb;
}

tr:hover {
    background-color: #f3f4f6;
}

hr {
    border: 0;
    height: 1px;
    background-color: #e5e7eb;
    margin: 25px 0;
}

@media print {
    body {
        background-color: white;
        padding: 0;
    }
    
    .main-content {
        box-shadow: none;
        padding: 0;
    }
}
"""