let thread_id = null;

// -----------------------------
// Create New Chat
// -----------------------------
async function createNewChat() {
    let res = await fetch("http://127.0.0.1:8000/new_chat", {
        method: "POST"
    });

    if (!res.ok) {
        throw new Error(`Unable to create chat: ${res.status}`);
    }

    let data = await res.json();
    thread_id = data.thread_id;

    document.getElementById("chatbox").innerHTML = "";

    await loadConversations();

    return thread_id;
}

// -----------------------------
// Load Sidebar Conversations
// -----------------------------
async function loadConversations() {
    let res = await fetch("http://127.0.0.1:8000/conversations");
    let chats = await res.json();

    let history = document.getElementById("history");
    history.innerHTML = "";

    chats.forEach(chat => {
        let div = document.createElement("div");

        div.innerText = chat.title;
        div.className = "history-item";
        div.onclick = () => loadChat(chat.thread_id);

        history.appendChild(div);
    });
}

// -----------------------------
// Load Selected Chat
// -----------------------------
async function loadChat(id) {
    thread_id = id;

    let res = await fetch("http://127.0.0.1:8000/messages/" + id);
    let messages = await res.json();

    let chatbox = document.getElementById("chatbox");
    chatbox.innerHTML = "";

    messages.forEach(m => {
        let div = document.createElement("div");

        div.className = (m.role === "user") ? "user" : "bot";
        div.textContent = m.content;

        chatbox.appendChild(div);
    });

    chatbox.scrollTop = chatbox.scrollHeight;
}

// -----------------------------
// Send Message (with spinner)
// -----------------------------
async function sendMessage() {
    let input = document.getElementById("userInput");
    let msg = input.value.trim();

    if (!msg) return;

    if (!thread_id) {
        await createNewChat();
    }

    let chatbox = document.getElementById("chatbox");

    // -----------------------------
    // User Message
    // -----------------------------
    let userDiv = document.createElement("div");
    userDiv.className = "user";
    userDiv.textContent = msg;

    chatbox.appendChild(userDiv);

    input.value = "";
    chatbox.scrollTop = chatbox.scrollHeight;

    // -----------------------------
    // Bot Placeholder (Spinner)
    // -----------------------------
    let botDiv = document.createElement("div");
    botDiv.className = "bot loading";

    let spinner = document.createElement("div");
    spinner.className = "spinner";

    let textSpan = document.createElement("span");
    textSpan.textContent = "Thinking...";

    botDiv.appendChild(spinner);
    botDiv.appendChild(textSpan);

    chatbox.appendChild(botDiv);

    try {
        let res = await fetch("http://127.0.0.1:8000/chat", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                message: msg,
                thread_id: thread_id
            })
        });

        if (!res.ok) {
            throw new Error(`Server returned ${res.status}`);
        }

        // -----------------------------
        // Non-stream response fallback
        // -----------------------------
        if (!res.body) {
            botDiv.classList.remove("loading");
            botDiv.innerHTML = "";

            const text = await res.text();
            botDiv.textContent = text;
            return;
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();

        let firstChunk = true;

        // -----------------------------
        // Streaming response
        // -----------------------------
        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            let chunk = decoder.decode(value, { stream: true });

            // Remove spinner on first chunk
            if (firstChunk) {
                botDiv.classList.remove("loading");
                botDiv.innerHTML = "";
                firstChunk = false;
            }

            botDiv.textContent += chunk;

            chatbox.scrollTop = chatbox.scrollHeight;
        }
    } catch (err) {
        botDiv.classList.remove("loading");
        botDiv.innerHTML = "Server error";
        console.error(err);
    }
}

// -----------------------------
// Enter Key Support
// -----------------------------
document
    .getElementById("userInput")
    .addEventListener("keydown", function (e) {
        if (e.key === "Enter") {
            e.preventDefault();
            sendMessage();
        }
    });

// -----------------------------
// Initial Load
// -----------------------------
loadConversations();