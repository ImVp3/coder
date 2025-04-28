// src/static/js/script.js

// --- Global Variables & Elements ---
const chatBox = document.getElementById('chat-box');
const chatInput = document.getElementById('chat-input');
const sendButton = document.getElementById('send-button');
const clearButton = document.getElementById('clear-button');
const flowStatusSpan = document.getElementById('flow-status');

const modelSelect = document.getElementById('model-select');
const temperatureSlider = document.getElementById('temperature-slider');
const temperatureValue = document.getElementById('temperature-value');
const maxIterationsSlider = document.getElementById('max-iterations-slider');
const maxIterationsValue = document.getElementById('max-iterations-value');
const reflectCheckbox = document.getElementById('reflect-checkbox');
const frameworkInput = document.getElementById('framework-input');
const saveSettingsButton = document.getElementById('save-settings-button');
const settingsStatusDiv = document.getElementById('settings-status');

const urlInput = document.getElementById('url-input');
const maxDepthSlider = document.getElementById('max-depth-slider');
const maxDepthValue = document.getElementById('max-depth-value');
const uploadUrlButton = document.getElementById('upload-url-button');
const fileInput = document.getElementById('file-input');
const uploadFilesButton = document.getElementById('upload-files-button');
const uploadStatusDiv = document.getElementById('upload-status');
const deleteSourceInput = document.getElementById('delete-source-input');
const deleteSourceButton = document.getElementById('delete-source-button');
const deleteStatusDiv = document.getElementById('delete-status');
const sourceListUl = document.getElementById('source-list');

let eventSource = null; // For Server-Sent Events

// --- Utility Functions ---
function displayStatus(element, message, type = 'info') {
    element.textContent = message;
    element.className = `status-message status-${type}`; // Add type class for styling
    // Optional: Clear status after a few seconds
    // setTimeout(() => { element.textContent = ''; element.className = 'status-message'; }, 5000);
}

function addMessageToChat(sender, messageContent) {
    const messageDiv = document.createElement('div');
    messageDiv.classList.add('chat-message');
    if (sender === 'user') {
        messageDiv.classList.add('user-message');
        messageDiv.textContent = messageContent; // Display user text directly
    } else { // 'bot'
        messageDiv.classList.add('bot-message');
        // Use innerHTML for bot messages to render potential HTML/Markdown (like code blocks)
        // Be cautious with innerHTML if the source isn't trusted.
        // Consider using a Markdown library (like Marked.js) for safer rendering.
        // Basic rendering for now:
        messageDiv.innerHTML = messageContent.replace(/```python\n([\s\S]*?)\n```/g, '<pre><code>$1</code></pre>');
    }
    chatBox.appendChild(messageDiv);
    chatBox.scrollTop = chatBox.scrollHeight; // Scroll to bottom
}

// --- Tab Handling ---
function openTab(evt, tabName) {
    let i, tabcontent, tablinks;
    tabcontent = document.getElementsByClassName("tab-content");
    for (i = 0; i < tabcontent.length; i++) {
        tabcontent[i].style.display = "none";
    }
    tablinks = document.getElementsByClassName("tab-button");
    for (i = 0; i < tablinks.length; i++) {
        tablinks[i].className = tablinks[i].className.replace(" active", "");
    }
    document.getElementById(tabName).style.display = "block";
    evt.currentTarget.className += " active";
}

// --- Chat Functionality ---
function connectChatStream(userMessage) {
    // Close existing connection if any
    if (eventSource) {
        eventSource.close();
    }

    // Add user message to chat immediately
    addMessageToChat('user', userMessage);
    chatInput.value = ''; // Clear input field

    // Create a placeholder for the bot's response
    const botMessageDiv = document.createElement('div');
    botMessageDiv.classList.add('chat-message', 'bot-message');
    botMessageDiv.innerHTML = "Thinking..."; // Initial placeholder
    chatBox.appendChild(botMessageDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    // Establish SSE connection
    eventSource = new EventSource(`/api/chat/stream?message=${encodeURIComponent(userMessage)}`);

    let fullBotMessage = "";

    eventSource.onmessage = function(event) {
        try {
            const data = JSON.parse(event.data);

            if (data.type === 'flow') {
                flowStatusSpan.textContent = data.content || 'Processing...';
            } else if (data.type === 'message_chunk') {
                // Append chunk to the full message and update the bot message div
                fullBotMessage += data.content;
                 // Basic rendering update, replace ``` blocks
                botMessageDiv.innerHTML = fullBotMessage.replace(/```python\n([\s\S]*?)\n```/g, '<pre><code>$1</code></pre>');
                chatBox.scrollTop = chatBox.scrollHeight; // Keep scrolled to bottom
            } else if (data.type === 'full_message') {
                 // Final message update (might be redundant if chunks cover everything)
                 fullBotMessage = data.content;
                 botMessageDiv.innerHTML = fullBotMessage.replace(/```python\n([\s\S]*?)\n```/g, '<pre><code>$1</code></pre>');
                 chatBox.scrollTop = chatBox.scrollHeight;
            } else if (data.type === 'error') {
                botMessageDiv.innerHTML = `Error: ${data.content}`;
                botMessageDiv.style.color = 'red';
                eventSource.close(); // Close on error
            } else if (data.type === 'end') {
                console.log("Stream ended.");
                eventSource.close();
                 // Optional: Update flow status back to Idle or based on final state
                 // flowStatusSpan.textContent = 'Idle';
            }
        } catch (e) {
            console.error("Error parsing SSE data:", e);
            botMessageDiv.innerHTML = "Error receiving response.";
            botMessageDiv.style.color = 'red';
            eventSource.close();
        }
    };

    eventSource.onerror = function(err) {
        console.error("EventSource failed:", err);
        botMessageDiv.innerHTML = "Connection error.";
        botMessageDiv.style.color = 'red';
        if (eventSource) {
            eventSource.close();
        }
        flowStatusSpan.textContent = 'Error';
    };
}

sendButton.addEventListener('click', () => {
    const message = chatInput.value.trim();
    if (message) {
        connectChatStream(message);
    }
});

chatInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { // Send on Enter, allow Shift+Enter for newline
        e.preventDefault(); // Prevent default newline behavior
        const message = chatInput.value.trim();
        if (message) {
            connectChatStream(message);
        }
    }
});


clearButton.addEventListener('click', () => {
    chatBox.innerHTML = ''; // Clear chat display
    flowStatusSpan.textContent = 'Idle';
    if (eventSource) {
        eventSource.close(); // Close any active stream
    }
    // Optionally call an API endpoint to clear server-side history if needed
});

// --- Settings Functionality ---
temperatureSlider.addEventListener('input', () => {
    temperatureValue.textContent = temperatureSlider.value;
});
maxIterationsSlider.addEventListener('input', () => {
    maxIterationsValue.textContent = maxIterationsSlider.value;
});

saveSettingsButton.addEventListener('click', async () => {
    const settings = {
        model: modelSelect.value,
        temperature: parseFloat(temperatureSlider.value),
        max_iterations: parseInt(maxIterationsSlider.value),
        reflect: reflectCheckbox.checked,
        framework: frameworkInput.value.trim() || null // Send null if empty
    };

    displayStatus(settingsStatusDiv, 'Saving settings...', 'info');

    try {
        const response = await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(settings)
        });

        const result = await response.json();

        if (response.ok) {
            displayStatus(settingsStatusDiv, result.status || 'Settings saved successfully!', 'success');
        } else {
            displayStatus(settingsStatusDiv, result.detail || 'Failed to save settings.', 'error');
        }
    } catch (error) {
        console.error("Error saving settings:", error);
        displayStatus(settingsStatusDiv, 'Error connecting to server.', 'error');
    }
});


// --- Document Management Functionality ---
maxDepthSlider.addEventListener('input', () => {
    maxDepthValue.textContent = maxDepthSlider.value;
});

async function fetchSources() {
    try {
        const response = await fetch('/api/documents/sources');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const sources = await response.json();
        sourceListUl.innerHTML = ''; // Clear existing list
        if (sources.length === 0) {
            sourceListUl.innerHTML = '<li>No sources found.</li>';
        } else {
            sources.forEach(source => {
                const li = document.createElement('li');
                li.textContent = source;
                sourceListUl.appendChild(li);
            });
        }
    } catch (error) {
        console.error("Error fetching sources:", error);
        sourceListUl.innerHTML = '<li>Error loading sources.</li>';
    }
}

uploadUrlButton.addEventListener('click', async () => {
    const url = urlInput.value.trim();
    const depth = parseInt(maxDepthSlider.value);
    if (!url) {
        displayStatus(uploadStatusDiv, 'Please enter a URL.', 'error');
        return;
    }

    displayStatus(uploadStatusDiv, `Loading from ${url}...`, 'info');
    uploadUrlButton.disabled = true; // Prevent double clicks

    try {
        const response = await fetch('/api/documents/upload_url', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ url: url, max_depth: depth })
        });

        const result = await response.json();

        if (response.ok) {
            displayStatus(uploadStatusDiv, result.status || 'URL processed.', 'success');
            urlInput.value = ''; // Clear input on success
            fetchSources(); // Refresh source list
        } else {
            displayStatus(uploadStatusDiv, result.detail || result.status || 'Failed to process URL.', 'error');
        }
    } catch (error) {
        console.error("Error uploading URL:", error);
        displayStatus(uploadStatusDiv, 'Error connecting to server.', 'error');
    } finally {
         uploadUrlButton.disabled = false;
    }
});

uploadFilesButton.addEventListener('click', async () => {
    const files = fileInput.files;
    if (files.length === 0) {
        displayStatus(uploadStatusDiv, 'Please select files to upload.', 'error');
        return;
    }

    const formData = new FormData();
    for (const file of files) {
        formData.append('files', file); // Key must match FastAPI parameter name
    }

    displayStatus(uploadStatusDiv, `Uploading ${files.length} file(s)...`, 'info');
    uploadFilesButton.disabled = true;

    try {
        const response = await fetch('/api/documents/upload_files', {
            method: 'POST',
            body: formData // No 'Content-Type' header needed for FormData, browser sets it
        });

        const result = await response.json();

        if (response.ok) {
            displayStatus(uploadStatusDiv, result.status || 'Files uploaded successfully.', 'success');
            fileInput.value = ''; // Clear file input
            fetchSources(); // Refresh source list
        } else {
            displayStatus(uploadStatusDiv, result.detail || result.status || 'Failed to upload files.', 'error');
        }
    } catch (error) {
        console.error("Error uploading files:", error);
        displayStatus(uploadStatusDiv, 'Error connecting to server.', 'error');
    } finally {
        uploadFilesButton.disabled = false;
    }
});


deleteSourceButton.addEventListener('click', async () => {
    const sourceToDelete = deleteSourceInput.value.trim();
    if (!sourceToDelete) {
        displayStatus(deleteStatusDiv, 'Please enter a source name to delete.', 'error');
        return;
    }

    displayStatus(deleteStatusDiv, `Deleting source: ${sourceToDelete}...`, 'info');
    deleteSourceButton.disabled = true;

    try {
        // Using POST here, but DELETE might be more semantically correct
        // If using DELETE, adjust FastAPI endpoint and potentially how data is sent
        const response = await fetch('/api/documents/delete', {
            method: 'POST', // Or 'DELETE'
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ source: sourceToDelete })
        });

        const result = await response.json();

        if (response.ok) {
            displayStatus(deleteStatusDiv, result.status || `Source '${sourceToDelete}' deleted.`, 'success');
            deleteSourceInput.value = ''; // Clear input
            fetchSources(); // Refresh source list
        } else {
            displayStatus(deleteStatusDiv, result.detail || result.status || 'Failed to delete source.', 'error');
        }
    } catch (error) {
        console.error("Error deleting source:", error);
        displayStatus(deleteStatusDiv, 'Error connecting to server.', 'error');
    } finally {
        deleteSourceButton.disabled = false;
    }
});


// --- Initial Load ---
document.addEventListener('DOMContentLoaded', () => {
    fetchSources(); // Load initial source list when the page loads
    // Set initial slider values display
    temperatureValue.textContent = temperatureSlider.value;
    maxIterationsValue.textContent = maxIterationsSlider.value;
    maxDepthValue.textContent = maxDepthSlider.value;
});
