const sendButton = document.getElementById("send-button");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");
const modelSelect = document.getElementById("model-select");
const newChatButton = document.getElementById("new-chat-button");
const searchChatsInput = document.getElementById("search-chats-input");
const chatTitleModal = document.getElementById("chat-title-modal");
const saveChatTitleButton = document.getElementById("save-chat-title");
const cancelChatTitleButton = document.getElementById("cancel-chat-title");
const deleteChatButton = document.getElementById("delete-chat-button");
const exportChatButton = document.getElementById("export-chat");
const fileDropZone = document.getElementById("file-drop-zone");
const uploadHint = document.getElementById("upload-hint");
const uploadFileList = document.getElementById("upload-file-list");
const MAX_UPLOAD_FILES = 3;
const MAX_FILE_SIZE_BYTES = 1024 * 1024;

let conversationHistory = [];
let currentChatId = null; // This will be set when a chat is loaded or created
let chatTitleInput = document.getElementById("chat-title-input");
let savedChatsList = document.getElementById("saved-chats-list");
let pendingFileContent = null; // Array of dropped file contents waiting to be sent with the next message
let pendingFileNames = [];

function clearUploadState() {
    pendingFileContent = null;
    pendingFileNames = [];
    uploadFileList.innerHTML = "";
    uploadHint.textContent = "Drag and drop up to 3 files here";
    fileDropZone.classList.remove("has-file");
    chatInput.placeholder = "Type your message here...";
}

function updateUploadBox(names) {
    uploadFileList.innerHTML = "";
    pendingFileNames = names;

    if (pendingFileNames.length === 0) {
        clearUploadState();
        return;
    }

    pendingFileNames.forEach((name) => {
        const item = document.createElement("li");
        item.textContent = name;
        uploadFileList.appendChild(item);
    });

    const fileLabel = pendingFileNames.length === 1 ? "file" : "files";
    uploadHint.textContent = `${pendingFileNames.length} ${fileLabel} attached. They will be sent with your next message.`;
    chatInput.placeholder = `${pendingFileNames.length} ${fileLabel} attached. Add an optional message.`;
    fileDropZone.classList.add("has-file");
}

function readTextFile(file) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = (event) => resolve(event.target.result);
        reader.onerror = () => reject(new Error(`Failed to read file: ${file.name}`));
        reader.readAsText(file);
    });
}

function toDisplayText(value) {
    if (Array.isArray(value)) {
        return value
            .filter((item) => item && item.type === "message")
            .map((item) => item.content || "")
            .join("\n")
            .trim();
    }

    if (value && typeof value === "object") {
        if (value.type === "message") {
            return value.content || "";
        }
        return "";
    }

    return typeof value === "string" ? value : "";
}


function createBubble(label, text, cssClass, renderMarkdown = false) {
    const wrapper = document.createElement("div");
    wrapper.className = `chat-message ${cssClass}`;

    // Apply red color for user messages
    if (cssClass === "user-message") {
        wrapper.style.color = "#9900ff";  // Bootstrap danger/red color
    }

    const tag = document.createElement("span");
    tag.className = "message-tag";
    tag.textContent = label;

    const body = document.createElement("div");
    body.className = "message-body";

    if (renderMarkdown) {
        body.innerHTML = marked.parse(text);

        if (window.renderMathInElement) {
            window.renderMathInElement(body, {
                delimiters: [
                    { left: "$$", right: "$$", display: true },
                    { left: "\\[", right: "\\]", display: true },
                    { left: "$", right: "$", display: false },
                    { left: "\\(", right: "\\)", display: false }
                ]
            });
        }

    } else {
        body.textContent = text;
    }

    wrapper.appendChild(tag);
    wrapper.appendChild(body);
    return wrapper;
}

async function createNewChat(chat_title) {
    // Clear the conversation history and chat messages
    conversationHistory.length = 0;
    chatMessages.innerHTML = "";
    currentChatId = null; // Reset the current chat ID

    try {
        const response = await fetch("/chat/new", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ title: chat_title })
        });

        const result = await response.json();
        if (result.status === "success") {
            currentChatId = result.chat_id;
        } else {
            alert("Error: " + result.message);
        }
    } catch (error) {
        alert("An error occurred while creating a new chat.");
    }

    // Refresh the chat history list to include the new chat
    await getChatHistory();

    // select the newly created chat in the chat list from it's id
        const allListItems = document.querySelectorAll(".chat-list-item");
        allListItems.forEach(item => item.classList.remove("chat-list-selected"));
        const newChatListItem = Array.from(allListItems).find(item => item.textContent === chat_title);
        if (newChatListItem) {
            newChatListItem.classList.add("chat-list-selected");
        }
}


function loadChat(chatId = null, chatTitle = null) {
    // fetches the chat history for the given chat ID and populates the chat messages area with the conversation history
    fetch(`/chat/${chatId}`)
        .then(response => response.json())
        .then(data => {
            if (data.status === "success") {
                conversationHistory = []; // Clear the conversation history before loading new chat
                chatMessages.innerHTML = "";
                let messages = data.messages || [];
                // load the messages into the chat area, if there are file contexts, only load the file name for reference
                messages.forEach(msg => {
                    const cssClass = msg.sender === "user" ? "user-message" : "bot-message";
                    const fileContextText = prepareFileContextForDisplay(msg.file_context);

                    console.log(`Loading message from ${msg.sender}: ${msg.message}${fileContextText ? `\n${fileContextText}` : ""}`);
                    chatMessages.appendChild(createBubble(`${msg.sender}:`, msg.message, cssClass, true));
                    if (fileContextText) {
                        chatMessages.appendChild(createBubble(`Uploaded file name:`, fileContextText, "file-context", false));
                    }
                    conversationHistory.push({ sender: msg.sender, content: msg.message });
                    // add a separator between messages
                    const separator = document.createElement("div");
                    separator.className = "message-separator";
                    separator.innerHTML = "<hr>";
                    chatMessages.appendChild(separator);
                });
                currentChatId = chatId;
                chatTitleInput.value = chatTitle || data.title || "Chat";
            } else {
                alert("Error: " + data.message);
            }
        })
        .catch(error => {
            alert("An error occurred while loading the chat.");
        });
}


async function getChatHistory(title_filter = "") {
    let result;
    try {
        const response = await fetch(`/chats?title_query=${encodeURIComponent(title_filter)}`);
        result = await response.json();
    } catch (error) {
        alert("An error occurred while fetching the chat history.");
        return;
    }
    savedChatsList.innerHTML = "";
    if (result.status === "success") {
        result.chats.forEach(chat => {
            const listItem = document.createElement("li");
            listItem.className = "chat-list-item";
            listItem.textContent = chat.title;
            listItem.dataset.chatId = chat.id; // Store the chat ID in a data attribute
            listItem.addEventListener("click", function() { 
                loadChat(chat.id, chat.title);
                // remove selected class from all list items
                const allListItems = document.querySelectorAll(".chat-list-item");
                allListItems.forEach(item => item.classList.remove("chat-list-selected"));
                // add selected class to the clicked list item
                this.classList.add("chat-list-selected");
                
            });
            savedChatsList.appendChild(listItem);
        });
    } else {
        alert("Error: " + result.message);
    }
}


function prepareFileContextForDisplay(fileContext) {
    if (!fileContext || !Array.isArray(fileContext) || fileContext.length === 0) {
        return null;
    }
    return fileContext.map(entry => `File: ${entry.file_name}`).join("\n");
}   


function prepareFileContextForServer()  {

    // loop through the pendingFileNames and pendingFileContent and prepare a json string with the file name and content, for example: { "file_name": "example.txt", "content": "This is the content of the file." }
    if (pendingFileNames.length === 0 || !Array.isArray(pendingFileContent) || pendingFileContent.length === 0) {
        return null;
    }

    // create an array of file contexts for each file name and content, for example: [{ "file_name": "example1.txt", "content": "This is the content of the first file." }, { "file_name": "example2.txt", "content": "This is the content of the second file." }]
    const fileContext = pendingFileNames.map((fileName, index) => {
        return {
            file_name: fileName,
            content: pendingFileContent[index] || ""
        };
    });

    return fileContext;

}

function saveChatMessage(chatId, sender, message, fileContext = null) {
    // sends a POST request to save a chat message to the server for the given chat ID, sender, and message content

    const payloadFileContext = fileContext;

    console.log(`Saving message for chat ID ${chatId} from ${sender}: ${message}`);
    console.log(`File context: ${JSON.stringify(payloadFileContext)}`);
   
    fetch("/chat/new-message", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ chat_id: chatId, sender: sender, message: message, file_context: payloadFileContext })
    });
}


sendButton.addEventListener("click", async (event) => {
    event.preventDefault();

    // if the current chat ID is not set, create a new chat first
    if (!currentChatId){
        await createNewChat(chatTitleInput.value.trim() || "New Chat");
    }
    
    let chatId = currentChatId;

    const userMessage = chatInput.value.trim();
    if (!userMessage && !pendingFileContent) return;

    // save the user message to the server immediately
    const fileContextForServer = prepareFileContextForServer();
    saveChatMessage(chatId, "user", userMessage, fileContextForServer);

    // clear the user message input immediately to give feedback that the message is being processed
    chatInput.value = "";

    // Add user message
    chatMessages.appendChild(createBubble("You:", userMessage, "user-message", false));
    chatInput.value = "";

    conversationHistory.push({ sender: "user", content: userMessage });

    // Add separator before adding the bot message
    const separator = document.createElement("div");
    separator.className = "message-separator";
    separator.innerHTML = "<hr>";
    chatMessages.appendChild(separator);

    const selectedModel = modelSelect.value;
    if (!selectedModel) return;

    sendButton.classList.add("loading");
    sendButton.disabled = true;
    sendButton.setAttribute("aria-busy", "true");
    disableButtons();
    
    try {
        const response = await fetch("/chat/send", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                chat_id: chatId,
                model: selectedModel
            })
        });

        // clear the pending file content after sending the message
        pendingFileContent = null;      

        const result = await response.json();

        if (result.status === "success") {
            // Add bot response
            let displayText = toDisplayText(result.response);
            chatMessages.appendChild(createBubble("Bot:", displayText, "bot-message", true));
            conversationHistory.push({ sender: "bot", content: result.response });
            chatMessages.scrollTop = chatMessages.scrollHeight;
            // save the bot message to the server immediately
            saveChatMessage(chatId, "bot", displayText, null);
            clearUploadState();

        } else {
            alert("Error: " + result.message);
        }

    } catch (error) {
        alert("An error occurred while sending the message.");
    } finally {
        sendButton.classList.remove("loading");
        sendButton.disabled = false;
        enableButtons();
        sendButton.removeAttribute("aria-busy");
    }
});


// Add event listener to the search input to filter chats as the user types
searchChatsInput.addEventListener("input", (event) => {
    const query = event.target.value.trim();
    getChatHistory(query);
});


function hideButtons() {
    newChatButton.style.display = "none";
    sendButton.style.display = "none";
    deleteChatButton.style.display = "none";
    exportChatButton.style.display = "none";
}

function showButtons() {
    newChatButton.style.display = "inline-block";
    sendButton.style.display = "inline-block";
    deleteChatButton.style.display = "inline-block";
    exportChatButton.style.display = "inline-block";
}

function openChatTitleModal() {
    hideButtons();
    chatTitleModal.style.display = "grid";
    chatTitleInput.value = ""; // Set the input value to the current chat title
    chatTitleInput.focus();
}


function closeChatTitleModal() {
    showButtons();
    chatTitleModal.style.display = "none";
}

newChatButton.addEventListener("click", openChatTitleModal);


saveChatTitleButton.addEventListener("click", async () => {
    const newTitle = chatTitleInput.value.trim();
    if (!newTitle) {
        alert("Chat title cannot be empty.");
        return;
    }
    await createNewChat(newTitle);
    closeChatTitleModal();
});

cancelChatTitleButton.addEventListener("click", closeChatTitleModal);


chatTitleInput.addEventListener("keydown", async (event) => {
    if (event.key === "Enter") {
        event.preventDefault();
        const title = chatTitleInput.value.trim() || "New Chat";
        await createNewChat(title);
        closeChatTitleModal();
    } else if (event.key === "Escape") {
        closeChatTitleModal();
    }
});


deleteChatButton.addEventListener("click", async () => {
    if (!currentChatId) {
        alert("No chat selected to delete.");
        return;
    }
    if (!confirm("Are you sure you want to delete this chat? This action cannot be undone.")) {
        return;
    }
    try {
        const response = await fetch(`/chat/${currentChatId}`, {
            method: "DELETE"
        });
        const result = await response.json();
        if (result.status === "success") {
            alert("Chat deleted successfully.");
            currentChatId = null;
            conversationHistory.length = 0;
            chatTitleInput.value = "";
            chatMessages.innerHTML = "";
            await getChatHistory();
        }
        else {
            alert("Error: " + result.message);
        }
    } catch (error) {
        alert("An error occurred while deleting the chat.");
    }       

});


function disableButtons() {
    newChatButton.disabled = true;
    deleteChatButton.disabled = true;
    exportChatButton.disabled = true;
}


function enableButtons() {
    newChatButton.disabled = false;
    deleteChatButton.disabled = false;
    exportChatButton.disabled = false;
}


function exportChat() {
    if (!currentChatId) {
        alert("No chat selected to export.");
        return
    }

    // Create a blob from the conversation history
    const blob = new Blob([JSON.stringify(conversationHistory, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${chatTitleInput.value.trim() || "chat"}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

exportChatButton.addEventListener("click", exportChat);


fileDropZone.addEventListener("dragover", (event) => {
    event.preventDefault();
    fileDropZone.classList.add("dragover");
});

fileDropZone.addEventListener("dragleave", (event) => {
    event.preventDefault();
    fileDropZone.classList.remove("dragover");
});

fileDropZone.addEventListener("drop", handleFileDrop);


async function handleFileDrop(event) {
    // take a file and read its contents, do not add it to the chat history, but send it with the next message as part of the context
    event.preventDefault();
    fileDropZone.classList.remove("dragover");

    const droppedFiles = Array.from(event.dataTransfer.files || []);
    if (droppedFiles.length === 0) {
        return;
    }

    if (droppedFiles.length > MAX_UPLOAD_FILES) {
        alert(`You can upload a maximum of ${MAX_UPLOAD_FILES} files at a time.`);
    }

    const candidateFiles = droppedFiles.slice(0, MAX_UPLOAD_FILES);
    const oversizedFiles = candidateFiles.filter((file) => file.size >= MAX_FILE_SIZE_BYTES);

    if (oversizedFiles.length > 0) {
        const names = oversizedFiles.map((file) => file.name).join(", ");
        alert(`These files are too large (must be less than 1 MB each): ${names}`);
    }

    const filesToRead = candidateFiles.filter((file) => file.size < MAX_FILE_SIZE_BYTES);

    if (filesToRead.length === 0) {
        clearUploadState();
        return;
    }

    try {
        const fileContents = await Promise.all(filesToRead.map((file) => readTextFile(file)));
        pendingFileContent = fileContents;
        updateUploadBox(filesToRead.map((file) => file.name));
    } catch (error) {
        console.error(error);
        alert("One or more files could not be read. Please try again.");
    }
}


window.addEventListener('DOMContentLoaded', async () => {
    await getChatHistory();
    // select the most recent chat in the chat list if it exists
    const first = document.querySelector(".chat-list-item");
    if (!first) return;

    first.classList.add("chat-list-selected");
    const firstID = Number(first.dataset.chatId);
    loadChat(firstID, first.textContent);
    clearUploadState();
});
