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
async function loadConversations() {

    let res = await fetch("http://127.0.0.1:8000/conversations", {
        headers: getAuthHeaders()
    });

    let chats = await res.json();

    let history = document.getElementById("history");
    history.innerHTML = "";

    chats.forEach(chat => {
        let div = document.createElement("div");

        div.innerText = chat.title;
        div.onclick = () => loadChat(chat.thread_id);

        history.appendChild(div);
    });
}

// -----------------------------
async function createNewChat() {

    let res = await fetch("http://127.0.0.1:8000/new_chat", {
        method: "POST",
        headers: getAuthHeaders()
    });

    let data = await res.json();
    thread_id = data.thread_id;

    document.getElementById("chatbox").innerHTML = "";

    loadConversations();
}

// -----------------------------
async function loadChat(id) {

    thread_id = id;

    let res = await fetch("http://127.0.0.1:8000/messages/" + id, {
        headers: getAuthHeaders()
    });

    let messages = await res.json();

    let chatbox = document.getElementById("chatbox");
    chatbox.innerHTML = "";

    messages.forEach(m => {
        let div = document.createElement("div");

        div.className = m.role === "user" ? "user" : "bot";
        div.textContent = m.content;

        chatbox.appendChild(div);
    });
}

// -----------------------------
async function sendMessage() {

    let input = document.getElementById("userInput");
    let msg = input.value.trim();

    if (!msg) return;

    if (!thread_id) await createNewChat();

    let chatbox = document.getElementById("chatbox");

    let userDiv = document.createElement("div");
    userDiv.textContent = msg;
    chatbox.appendChild(userDiv);

    input.value = "";

    let botDiv = document.createElement("div");
    chatbox.appendChild(botDiv);

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

    while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        botDiv.textContent += decoder.decode(value);
    }
}

// -----------------------------
window.onload = loadConversations;