const token = localStorage.getItem("token");

console.log("TOKEN:", token);

if (!token) {
    alert("Please login again");
    window.location.href = "index.html";
}

// -----------------------------
function getAuthHeaders(extra = {}) {
    return {
        ...extra,
        "Authorization": "Bearer " + token
    };
}

let thread_id = null;

// -----------------------------
// -----------------------------
// Load conversation list
async function loadConversations() {
    try {
        let res = await fetch("http://127.0.0.1:8000/conversations", {
            headers: getAuthHeaders()
        });

        let chats = await res.json();

        let history = document.getElementById("history");
        history.innerHTML = "";

        chats.forEach(chat => {
            let div = document.createElement("div");
            div.className = "chat-item";
            div.innerText = chat.title || "New Chat";

            div.onclick = () => loadChat(chat.thread_id);

            history.appendChild(div);
        });

    } catch (err) {
        console.error("Error loading conversations:", err);
    }
}

// -----------------------------
// Create new chat
async function createNewChat() {
    try {
        let res = await fetch("http://127.0.0.1:8000/new_chat", {
            method: "POST",
            headers: getAuthHeaders()
        });

        let data = await res.json();
        thread_id = data.thread_id;

        document.getElementById("chatbox").innerHTML = "";

        loadConversations();

    } catch (err) {
        console.error("Error creating chat:", err);
    }
}

// -----------------------------
// Load existing chat
async function loadChat(id) {
    try {
        thread_id = id;

        let res = await fetch(`http://127.0.0.1:8000/messages/${id}`, {
            headers: getAuthHeaders()
        });

        let messages = await res.json();

        let chatbox = document.getElementById("chatbox");
        chatbox.innerHTML = "";

        messages.forEach(m => {
            let div = document.createElement("div");

            div.className = m.role === "user"
                ? "message user"
                : "message bot";

            div.textContent = m.content;

            chatbox.appendChild(div);
        });

        scrollToBottom();

    } catch (err) {
        console.error("Error loading chat:", err);
    }
}

// -----------------------------
// Send message
async function sendMessage() {
    let input = document.getElementById("userInput");
    let msg = input.value.trim();

    if (!msg) return;

    if (!thread_id) await createNewChat();

    let chatbox = document.getElementById("chatbox");

    // USER MESSAGE (RIGHT)
    let userDiv = document.createElement("div");
    userDiv.className = "message user";
    userDiv.textContent = msg;
    chatbox.appendChild(userDiv);

    input.value = "";

    scrollToBottom();

    // BOT MESSAGE (LEFT)
let botDiv = document.createElement("div");
botDiv.className = "message bot";

// 👉 typing indicator
botDiv.innerHTML = `
    <span class="typing">
        <span></span>
        <span></span>
        <span></span>
    </span>
`;

chatbox.appendChild(botDiv);
scrollToBottom();

try {
    let res = await fetch("http://127.0.0.1:8000/chat", {
        method: "POST",
        headers: getAuthHeaders({
            "Content-Type": "application/json"
        }),
        body: JSON.stringify({
            message: msg,
            thread_id: thread_id
        })
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();

    // remove typing animation when real data starts
    let started = false;

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        if (!started) {
            botDiv.innerHTML = ""; // ✅ remove typing dots
            started = true;
        }

        botDiv.textContent += decoder.decode(value);
        scrollToBottom();
    }

} catch (err) {
    botDiv.textContent = "Error: Unable to get response.";
}
}

// -----------------------------
// Scroll helper
function scrollToBottom() {
    const chatbox = document.getElementById("chatbox");
    chatbox.scrollTop = chatbox.scrollHeight;
}

// -----------------------------
// Enter key support
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("userInput");

    input.addEventListener("keypress", function (e) {
        if (e.key === "Enter") {
            sendMessage();
        }
    });

    loadConversations();
});