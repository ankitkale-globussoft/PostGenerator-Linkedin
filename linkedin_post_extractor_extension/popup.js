// popup.js

const DB_NAME = "LinkedInExtractorDB";
const STORE_NAME = "FolderHandles";
const HANDLE_KEY = "targetFolder";

// Variables
let folderHandle = null;
let scrapedData = null;
let lastProfileName = "";

// Elements
const maxPostsInput = document.getElementById('max-posts');
const selectFolderBtn = document.getElementById('select-folder');
const folderNameSpan = document.getElementById('folder-name');
const startBtn = document.getElementById('start-scraping');
const downloadBtn = document.getElementById('download-btn');
const progressContainer = document.getElementById('progress-container');
const progressBar = document.getElementById('progress-bar');
const progressStatus = document.getElementById('progress-status');
const progressPercent = document.getElementById('progress-percent');
const statusMessage = document.getElementById('status-message');

// Initialize
document.addEventListener('DOMContentLoaded', async () => {
    const result = await chrome.storage.local.get(['maxPosts']);
    if (result.maxPosts) maxPostsInput.value = result.maxPosts;

    try {
        folderHandle = await getFolderHandle();
        if (folderHandle) {
            folderNameSpan.textContent = `📁 ${folderHandle.name}`;
            folderNameSpan.classList.add('status-success');
        }
    } catch (err) { console.error(err); }
});

// Save max posts change
maxPostsInput.addEventListener('change', () => {
    chrome.storage.local.set({ maxPosts: maxPostsInput.value });
});

// Select folder
selectFolderBtn.addEventListener('click', async () => {
    try {
        folderHandle = await window.showDirectoryPicker();
        await saveFolderHandle(folderHandle);
        folderNameSpan.textContent = `📁 ${folderHandle.name}`;
        folderNameSpan.classList.add('status-success');
        showMessage("Folder selected!", "success");
    } catch (err) { 
        if (err.name !== 'AbortError') showMessage("Error selecting folder", "error"); 
    }
});

// Start Scraping
startBtn.addEventListener('click', async () => {
    if (!folderHandle) {
        showMessage("Please select a folder first", "error");
        return;
    }

    try {
        // Verify Permission (USER GESTURE REQUIRED)
        const permission = await folderHandle.queryPermission({ mode: 'readwrite' });
        if (permission !== 'granted') {
            await folderHandle.requestPermission({ mode: 'readwrite' });
        }

        const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
        if (!tab || !tab.url || !tab.url.includes("linkedin.com")) {
            showMessage("Please focus a LinkedIn tab!", "error");
            return;
        }

        startBtn.classList.add('hidden');
        downloadBtn.classList.add('hidden');
        progressContainer.classList.remove('hidden');
        updateProgress(0, parseInt(maxPostsInput.value), "Initializing...");

        await chrome.scripting.executeScript({ target: { tabId: tab.id }, files: ['content.js'] });
        chrome.tabs.sendMessage(tab.id, { action: "START_SCRAPING", maxPosts: parseInt(maxPostsInput.value) });
    } catch (err) {
        showMessage("Setup error: " + err.message, "error");
        startBtn.classList.remove('hidden');
    }
});

// Download & Save JSON (USER GESTURE REQUIRED FOR WRITABLE)
downloadBtn.addEventListener('click', async () => {
    if (scrapedData && folderHandle) {
        await saveDataToFolder(scrapedData, lastProfileName);
        downloadBtn.classList.add('hidden');
        startBtn.classList.remove('hidden');
    }
});

// Message Listener from Content Script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === "PROGRESS_UPDATE") {
        updateProgress(message.current, message.total, message.status);
    } else if (message.type === "SCRAPING_COMPLETE") {
        scrapedData = message.data;
        lastProfileName = message.profileName;
        
        updateProgress(message.data.length, message.data.length, "Scraping Complete!");
        downloadBtn.classList.remove('hidden');
        showMessage(`${message.data.length} posts collected. Click Download to save.`, "success");
    } else if (message.type === "SCRAPING_ERROR") {
        showMessage(message.error, "error");
        startBtn.classList.remove('hidden');
    }
});

// UI Utils
function updateProgress(current, total, status) {
    const percent = Math.min((current / total) * 100, 100);
    progressBar.style.width = `${percent}%`;
    progressPercent.textContent = `${current}/${total}`;
    progressStatus.textContent = status;
}

function showMessage(text, type) {
    statusMessage.textContent = text;
    statusMessage.className = `status-message status-${type}`;
    statusMessage.classList.remove('hidden');
}

async function saveDataToFolder(data, profileName) {
    try {
        const finalName = profileName || "profile";
        const fileName = `raw_${finalName}.json`;
        const fileHandle = await folderHandle.getFileHandle(fileName, { create: true });
        const writable = await fileHandle.createWritable();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        await writable.write(blob);
        await writable.close();

        updateProgress(data.length, data.length, "Saved successfully!");
        showMessage(`Saved to ${fileName}`, "success");
        
        document.getElementById('last-saved').classList.remove('hidden');
        document.getElementById('save-time').textContent = new Date().toLocaleTimeString();
    } catch (err) {
        console.error("Save error:", err);
        showMessage("Error saving file: " + err.message, "error");
    }
}

// --------- IndexedDB Utils ---------
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, 1);
        request.onupgradeneeded = (e) => {
            const db = e.target.result;
            db.createObjectStore(STORE_NAME);
        };
        request.onsuccess = (e) => resolve(e.target.result);
        request.onerror = (e) => reject(e.target.error);
    });
}
async function saveFolderHandle(handle) {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readwrite");
    tx.objectStore(STORE_NAME).put(handle, HANDLE_KEY);
    return new Promise((resolve) => tx.oncomplete = () => resolve());
}
async function getFolderHandle() {
    const db = await openDB();
    const tx = db.transaction(STORE_NAME, "readonly");
    const request = tx.objectStore(STORE_NAME).get(HANDLE_KEY);
    return new Promise((resolve) => request.onsuccess = () => resolve(request.result));
}
