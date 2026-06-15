const sendButton = document.getElementById("send-button");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");
const modelSelect = document.getElementById("model-select");
const newChatButton = document.getElementById("new-chat-button");
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
}


newChatButton.addEventListener("click", async () => {
    // clears the chat history and messages, and creates a new chat with the title from the input field (or "New Chat" if the input is empty)
    await createNewChat(chatTitleInput.value.trim() || "New Chat");
});


function loadChat(chatId) {
    // fetches the chat history for the given chat ID and populates the chat messages area with the conversation history
    fetch(`/chat/${chatId}`)

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
            listItem.addEventListener("click", () => loadChat(chat.id));
            savedChatsList.appendChild(listItem);
        });
    } else {
        alert("Error: " + result.message);
    }
}


sendButton.addEventListener("click", async (event) => {
    event.preventDefault();

    // if the current chat ID is not set, create a new chat first
    if (!currentChatId) {
        await createNewChat(chatTitleInput.value.trim() || "New Chat");
    }

    const userMessage = chatInput.value.trim();
    if (!userMessage) return;

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
            chatMessages.appendChild(createBubble("Bot:", toDisplayText(result.response), "bot-message", true));
            conversationHistory.push({ sender: "bot", content: result.response });
            chatMessages.scrollTop = chatMessages.scrollHeight;
        } else {
            alert("Error: " + result.message);
        }

    } catch (error) {
        alert("An error occurred while sending the message.");
    } finally {
        sendButton.classList.remove("loading");
        sendButton.disabled = false;
        sendButton.removeAttribute("aria-busy");
    }
});


window.addEventListener('DOMContentLoaded', () => {
    getChatHistory();
});
