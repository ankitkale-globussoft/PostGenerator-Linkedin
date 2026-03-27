# LinkedIn Post Extractor Extension

A premium Chrome extension for scraping LinkedIn posts into JSON files, with real-time progress and folder selection.

## Features
- **Max Posts Control:** Set a limit on how many posts to scrape.
- **Folder Persistence:** Select a target folder once; the extension remembers it (using IndexedDB).
- **Format:** Saves posts in a clean JSON format: `{"text": "...", "engagement": 123}`.
- **Progress Monitoring:** Real-time progress bar and status updates.
- **Premium Design:** Glassmorphism UI with LinkedIn-inspired aesthetics.

## How to Install
1. Open Google Chrome.
2. Navigate to `chrome://extensions/`.
3. Enable **Developer Mode** in the top right corner.
4. Click **Load unpacked**.
5. Select the folder `linkedin_post_extractor_extension` from your project directory.

## How to Use
1. Go to any LinkedIn feed (Home or any Profile's "Posts" section).
2. Click the extension icon in your toolbar.
3. Choose the **Maximum Posts** you want to extract.
4. Click **Select Folder** to choose where the JSON files will be saved.
5. Click **Start Scraping**.
6. The extension will scroll automatically and save the file once finished!

## Notes
- Ensure you have a LinkedIn tab active when starting the extraction.
- The extension respects your folder selection even after browser restarts.
- For best results, use on pages with at least as many posts as your requested limit.
