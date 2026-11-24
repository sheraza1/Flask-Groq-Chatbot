// A new id per page load, so reloading the page starts a new conversation.
const sessionId = crypto.randomUUID();

const form = document.getElementById("userinputform");
const input = document.getElementById("userinput");
const sendButton = document.getElementById("sendbtn");
const chat = document.getElementById("upperid");

function scrollToBottom() {
    chat.scrollTop = chat.scrollHeight;
}

// Builds a message bubble with textContent, so text from the user or the model is never parsed as HTML.
function addMessage(text, who, isError = false) {
    const row = document.createElement("div");
    row.className = "message";

    const wrapper = document.createElement("div");
    wrapper.className = who === "user" ? "usermessagediv" : "appmessagediv";

    const bubble = document.createElement("div");
    bubble.className = who === "user" ? "usermessage" : "appmessage";
    if (isError) {
        bubble.style.border = "1px solid red";
    }
    bubble.textContent = text;

    wrapper.appendChild(bubble);
    row.appendChild(wrapper);
    chat.appendChild(row);
    scrollToBottom();
    return bubble;
}

function setBusy(busy) {
    sendButton.disabled = busy;
    input.disabled = busy;
    input.placeholder = busy ? "Wait . . ." : "Your message...";
}

// Shows the reply one character at a time.
function typeInto(bubble, text, done) {
    let index = 0;
    const step = () => {
        if (index < text.length) {
            bubble.textContent += text[index++];
            scrollToBottom();
            setTimeout(step, 20);
        } else {
            done();
        }
    };
    step();
}

async function sendMessage() {
    const text = input.value.trim();
    if (!text) return;

    addMessage(text, "user");
    input.value = "";
    setBusy(true);

    try {
        const response = await fetch("/data", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ data: text, session_id: sessionId }),
        });
        const json = await response.json();

        if (json.response) {
            const bubble = addMessage("", "app");
            typeInto(bubble, String(json.message), () => setBusy(false));
        } else {
            addMessage(json.message, "app", true);
            setBusy(false);
        }
    } catch (error) {
        addMessage("Could not reach the server.", "app", true);
        setBusy(false);
    }
}

form.addEventListener("submit", (event) => {
    event.preventDefault();
    sendMessage();
});

scrollToBottom();
