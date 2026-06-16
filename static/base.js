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

let conversationHistory = [];
let currentChatId = null; // This will be set when a chat is loaded or created
let chatTitleInput = document.getElementById("chat-title-input");
let savedChatsList = document.getElementById("saved-chats-list");


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
                messages.forEach(msg => {
                    const cssClass = msg.sender === "user" ? "user-message" : "bot-message";
                    chatMessages.appendChild(createBubble(`${msg.sender}:`, msg.message, cssClass, true));
                    conversationHistory.push({ sender: msg.sender, content: msg.message });
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


function save_chat_message(chatId, sender, message) {
    // sends a POST request to save a chat message to the server for the given chat ID, sender, and message content
    fetch("/chat/new-message", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({ chat_id: chatId, sender: sender, message: message })
    });
}


sendButton.addEventListener("click", async (event) => {
    event.preventDefault();

    // if the current chat ID is not set, create a new chat first
    if (!currentChatId) {
        await createNewChat(chatTitleInput.value.trim() || "New Chat");
    }

    const userMessage = chatInput.value.trim();
    if (!userMessage) return;

    // save the user message to the server immediately
    save_chat_message(currentChatId, "user", userMessage);

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
                message: conversationHistory.map(item => item.content).join("\n"),
                model: selectedModel
            })
        });

        const result = await response.json();

        if (result.status === "success") {
            // Add bot response
            let displayText = toDisplayText(result.response);
            chatMessages.appendChild(createBubble("Bot:", displayText, "bot-message", true));
            conversationHistory.push({ sender: "bot", content: result.response });
            chatMessages.scrollTop = chatMessages.scrollHeight;
            // save the bot message to the server immediately
            save_chat_message(currentChatId, "bot", displayText);

        } else {
            alert("Error: " + result.message);
        }

    } catch (error) {
        alert("An error occurred while sending the message.");
    } finally {
        sendButton.classList.remove("loading");
        enableButtons();
        sendButton.removeAttribute("aria-busy");
    }
});


// Add event listener to the search input to filter chats as the user types
searchChatsInput.addEventListener("input", (event) => {
    const query = event.target.value.trim();
    getChatHistory(query);
});


function openChatTitleModal() {
    chatTitleModal.style.display = "grid";
    chatTitleInput.value = ""; // Set the input value to the current chat title
    chatTitleInput.focus();
}


function closeChatTitleModal() {
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
}


function enableButtons() {
    newChatButton.disabled = false;
    deleteChatButton.disabled = false;
}


window.addEventListener('DOMContentLoaded', async () => {
    await getChatHistory();
    // select the most recent chat in the chat list if it exists
    const first = document.querySelector(".chat-list-item");
    if (!first) return;

    first.classList.add("chat-list-selected");
    const firstID = Number(first.dataset.chatId);
    loadChat(firstID, first.textContent);
});
