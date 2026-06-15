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
        const messageElement = document.createElement("div");
        messageElement.className = "chat-message user-message";
        messageElement.textContent = userMessage;
        chatMessages.appendChild(messageElement);
        chatInput.value = "";

        const responseElement = document.createElement("div");
        responseElement.className = "chat-message bot-message";
        responseElement.textContent = toDisplayText(result.response);
        chatMessages.appendChild(responseElement);
    }
});