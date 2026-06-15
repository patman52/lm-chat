const sendButton = document.getElementById("send-button");
const chatInput = document.getElementById("chat-input");
const chatMessages = document.getElementById("chat-messages");
const modelSelect = document.getElementById("model-select");

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
        wrapper.style.color = "#dc3545";  // Bootstrap danger/red color
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


sendButton.addEventListener("click", async () => {
    const userMessage = chatInput.value.trim();
    if (!userMessage) return;

    const selectedModel = modelSelect.value;
    if (!selectedModel) return;

    const response = await fetch("/chat/send", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            message: userMessage,
            model: selectedModel
        })
    });

    const result = await response.json();

    if (result.status === "success") {
        // Add user message
        chatMessages.appendChild(createBubble("You:", userMessage, "user-message", false));
        chatInput.value = "";
        // Add bot response
        chatMessages.appendChild(createBubble("Bot:", toDisplayText(result.response), "bot-message", true));
        
        // Add separator before adding the bot message
        const separator = document.createElement("div");
        separator.className = "message-separator";
        separator.innerHTML = "<hr>";

        chatMessages.scrollTop = chatMessages.scrollHeight;
    } else {
        alert("Error: " + result.message);
    }
});