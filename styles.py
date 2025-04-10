"""
Styles for the YouTube Video Summarizer UI
"""

STYLES = """
/* Main application styles */
QMainWindow {
    background-color: #f5f5f5;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 11pt;
}

/* Input section styles */
#inputFrame {
    background-color: #ffffff;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
    margin: 8px;
    padding: 15px;
}

#inputLabel {
    font-weight: bold;
    min-width: 120px;
}

#urlInput {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 8px;
    background-color: #fafafa;
    font-size: 11pt;
}

#urlInput:focus {
    border: 1px solid #4285f4;
    background-color: #ffffff;
}

QPushButton#primaryButton {
    background-color: #4285f4;
    color: white;
    border: none;
    border-radius: 4px;
    padding: 10px 20px;
    font-weight: bold;
    min-width: 150px;
}

QPushButton#primaryButton:hover {
    background-color: #2b75e8;
}

QPushButton#primaryButton:pressed {
    background-color: #1a65d9;
}

QPushButton#primaryButton:disabled {
    background-color: #a5c2f2;
}

QPushButton#actionButton {
    background-color: #f8f9fa;
    border: 1px solid #dadce0;
    border-radius: 4px;
    color: #3c4043;
    padding: 6px 12px;
}

QPushButton#actionButton:hover {
    background-color: #e8eaed;
    border-color: #d2d5d9;
}

QPushButton#actionButton:pressed {
    background-color: #dadce0;
}

QComboBox#comboBox {
    border: 1px solid #ccc;
    border-radius: 4px;
    padding: 6px;
    background-color: white;
    min-width: 200px;
}

QComboBox#comboBox:hover {
    border-color: #4285f4;
}

QComboBox#comboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: right;
    width: 20px;
    border-left: 1px solid #ccc;
}

QProgressBar#progressBar {
    border: 1px solid #ccc;
    border-radius: 4px;
    background-color: #f5f5f5;
    text-align: center;
    min-height: 20px;
}

QProgressBar#progressBar::chunk {
    background-color: #4285f4;
    border-radius: 3px;
}

/* History section styles */
#historyFrame {
    background-color: #ffffff;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
    margin: 8px;
}

#historyList {
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 4px;
    font-size: 10pt;
    background-color: #fafafa;
}

#historyList::item {
    border-bottom: 1px solid #f0f0f0;
    padding: 8px;
}

#historyList::item:selected {
    background-color: #e8f0fe;
    color: #1a73e8;
}

#historyList::item:hover {
    background-color: #f5f5f5;
}

/* Summary section styles */
#summaryFrame {
    background-color: #ffffff;
    border-radius: 8px;
    border: 1px solid #e0e0e0;
    margin: 8px;
}

#summaryView {
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 15px;
    font-size: 11pt;
    line-height: 1.5;
    background-color: #ffffff;
}

#summaryTitle {
    font-weight: bold;
    color: #3c4043;
    font-size: 10pt;
}

/* Activity Log view styles */
#activityLog {
    font-family: 'Segoe UI', 'Arial', sans-serif;
    font-size: 10pt;
    line-height: 1.6;
    border: 1px solid #e0e0e0;
    border-radius: 4px;
    padding: 10px;
    background-color: #ffffff;
}

/* Tab widget styles */
#contentTabs {
    border: none;
    background-color: transparent;
}

#contentTabs::pane {
    border: none;
    background-color: transparent;
}

#contentTabs QTabBar::tab {
    background-color: #f0f0f0;
    border: 1px solid #e0e0e0;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 15px;
    margin-right: 2px;
}

#contentTabs QTabBar::tab:selected {
    background-color: #ffffff;
    border-bottom: 1px solid #ffffff;
}

#contentTabs QTabBar::tab:!selected {
    margin-top: 2px;
}

#contentTabs QTabBar::tab:hover {
    background-color: #e8eaed;
}

/* Section headers */
#sectionHeader {
    font-weight: bold;
    font-size: 14pt;
    color: #202124;
    padding: 10px;
}

/* Status bar */
#statusBar {
    background-color: #f8f9fa;
    border-top: 1px solid #dadce0;
    padding: 4px;
    color: #5f6368;
}

/* Splitter handle */
QSplitter::handle {
    background-color: #e0e0e0;
    width: 2px;
}

QSplitter::handle:hover {
    background-color: #4285f4;
}

/* Style for Markdown rendering */
#summaryView {
    line-height: 1.6;
}

/* Render headings, lists, and code blocks nicely */
#summaryView h1 {
    font-size: 24px;
    color: #202124;
    margin-top: 25px;
    margin-bottom: 15px;
    border-bottom: 1px solid #eee;
    padding-bottom: 5px;
}

#summaryView h2 {
    font-size: 20px;
    color: #3c4043;
    margin-top: 20px;
    margin-bottom: 10px;
}

#summaryView h3 {
    font-size: 16px;
    color: #5f6368;
    margin-top: 15px;
    margin-bottom: 10px;
}

#summaryView p {
    margin-bottom: 15px;
}

#summaryView ul, #summaryView ol {
    margin-left: 20px;
    margin-bottom: 15px;
}

#summaryView li {
    margin-bottom: 5px;
}

#summaryView pre {
    background-color: #f8f9fa;
    border: 1px solid #eee;
    border-radius: 3px;
    padding: 10px;
    font-family: 'Consolas', 'Monaco', monospace;
    overflow-x: auto;
}

#summaryView code {
    background-color: #f8f9fa;
    border: 1px solid #eee;
    border-radius: 3px;
    padding: 2px 4px;
    font-family: 'Consolas', 'Monaco', monospace;
}

#summaryView blockquote {
    border-left: 4px solid #ccc;
    padding-left: 15px;
    color: #5f6368;
    font-style: italic;
}

#summaryView table {
    border-collapse: collapse;
    width: 100%;
    margin-bottom: 15px;
}

#summaryView th, #summaryView td {
    border: 1px solid #eee;
    padding: 8px;
    text-align: left;
}

#summaryView th {
    background-color: #f8f9fa;
    font-weight: bold;
}

#summaryView tr:nth-child(even) {
    background-color: #f8f9fa;
}
"""