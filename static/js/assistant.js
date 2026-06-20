(() => {
    const form = document.getElementById("chat-form");
    const input = document.getElementById("chat-input");
    const messages = document.getElementById("chat-messages");
    const sendButton = document.getElementById("chat-send");
    const clearButton = document.getElementById("clear-chat");
    const modeLabel = document.getElementById("chat-mode");
    const csrfToken = form?.querySelector("[name=csrfmiddlewaretoken]")?.value;
    const history = [];

    if (!form || !input || !messages || !sendButton || !csrfToken) return;

    function addMessage(role, content, pending = false) {
        const row = document.createElement("div");
        row.className = `chat-row chat-row-${role}`;
        const avatar = document.createElement("div");
        avatar.className = "chat-avatar";
        avatar.textContent = role === "user" ? "You" : "AI";
        const bubble = document.createElement("div");
        bubble.className = `chat-bubble chat-bubble-${role}`;
        const urlPattern = /(https?:\/\/[^\s]+)/g;
        let lastIndex = 0;
        for (const match of content.matchAll(urlPattern)) {
            bubble.append(document.createTextNode(content.slice(lastIndex, match.index)));
            const link = document.createElement("a");
            link.href = match[0];
            link.textContent = match[0];
            link.target = "_blank";
            link.rel = "noopener noreferrer";
            link.className = "chat-source-link";
            bubble.append(link);
            lastIndex = match.index + match[0].length;
        }
        bubble.append(document.createTextNode(content.slice(lastIndex)));
        if (pending) bubble.classList.add("chat-typing");
        row.append(avatar, bubble);
        messages.appendChild(row);
        messages.scrollTop = messages.scrollHeight;
        return row;
    }

    function setBusy(isBusy) {
        input.disabled = isBusy;
        sendButton.disabled = isBusy;
    }

    async function sendMessage() {
        const message = input.value.trim();
        if (!message) return;

        const priorHistory = history.slice(-10);
        addMessage("user", message);
        history.push({ role: "user", content: message });
        input.value = "";
        input.style.height = "auto";
        setBusy(true);
        const typingRow = addMessage("assistant", "AI Bot is searching and thinking...", true);

        try {
            const response = await fetch(window.location.pathname, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "X-CSRFToken": csrfToken,
                    "X-Requested-With": "XMLHttpRequest",
                },
                body: JSON.stringify({ message, history: priorHistory }),
            });
            const data = await response.json();
            typingRow.remove();
            if (!response.ok) throw new Error(data.error || "AI Bot could not reply.");
            addMessage("assistant", data.reply);
            history.push({ role: "assistant", content: data.reply });
            if (data.mode?.startsWith("offline") && modeLabel) {
                modeLabel.textContent = "Offline safety mode";
                modeLabel.className = "rounded-full border border-amber-700 bg-amber-50 px-3 py-1.5 text-xs font-bold text-amber-800";
            } else if (modeLabel) {
                modeLabel.textContent = data.web_used ? "Live web search used" : "AI answer";
                modeLabel.className = "rounded-full border border-emerald-700 bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700";
            }
            if (data.notice) addMessage("assistant", data.notice);
        } catch (error) {
            typingRow.remove();
            addMessage("assistant", error.message || "AI Bot could not reply. Please try again.");
        } finally {
            setBusy(false);
            input.focus();
        }
    }

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        sendMessage();
    });

    input.addEventListener("keydown", (event) => {
        if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            form.requestSubmit();
        }
    });

    input.addEventListener("input", () => {
        input.style.height = "auto";
        input.style.height = `${Math.min(input.scrollHeight, 128)}px`;
    });

    clearButton?.addEventListener("click", () => {
        history.length = 0;
        messages.replaceChildren();
        addMessage(
            "assistant",
            "Chat cleared. Ask me about screen time, privacy, cyberbullying, contacts, or location safety."
        );
        input.focus();
    });
})();
