# Oyez Case Scraper

This tool scrapes oral argument transcripts and case metadata from Oyez.org for Supreme Court cases.

## Features
- Scrapes complete case metadata (parties, dates, facts, conclusion, etc.)
- Captures oral argument transcripts
- Handles dynamic content loading
- Supports test mode (first 3 blocks) and full transcript mode
- Saves results in structured JSON format

## Prerequisites
- Python 3.8 or higher
- Chrome browser installed

## Setup

1. **Create and activate a virtual environment**
   ```bash
   # Create virtual environment in parent directory
   python -m venv ../venv

   # Activate virtual environment
   # On Windows:
   ..\venv\Scripts\activate
   # On macOS/Linux:
   source ../venv/bin/activate
   ```

2. **Install required packages**
   ```bash
   pip install selenium
   ```

3. **Project Structure**
   ```
   oyez_scraper/
   ├── selenium_transcript.py    # Main scraping script
   ├── README.md                # This file
   └── *_transcript_*.json      # Generated transcript files
   ```

## Usage

1. **Basic usage (test mode - first 3 blocks)**
   ```python
   python selenium_transcript.py
   ```

2. **For full transcript**
   ```python
   # Modify the main section in selenium_transcript.py:
   if __name__ == "__main__":
       get_transcript_with_selenium(
           case_year="2023",
           case_name="Acheson",  # Partial name is sufficient
           full_transcript=True  # Set to True for full transcript
       )
   ```

## Output Files
- `{Case_Name}_transcript_test.json`: Contains first 3 blocks (test mode)
- `{Case_Name}_transcript_full.json`: Contains complete transcript
