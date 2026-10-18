// ===== DOM Elements =====
const fileInput = document.getElementById("fileInput");
const choosePdfBtn = document.getElementById("choosePdfBtn");
const fileName = document.getElementById("fileName");
const uploadStatus = document.getElementById("uploadStatus");
const statusProcessing = document.getElementById("statusProcessing");
const statusSuccess = document.getElementById("statusSuccess");
const statusError = document.getElementById("statusError");
const successDetails = document.getElementById("successDetails");
const errorText = document.getElementById("errorText");
const chatMessages = document.getElementById("chatMessages");
const emptyState = document.getElementById("emptyState");
const questionInput = document.getElementById("questionInput");
const askBtn = document.getElementById("askBtn");
const askBtnText = document.getElementById("askBtnText");
const askBtnLoading = document.getElementById("askBtnLoading");
const statsCard = document.getElementById("statsCard");
const totalChunks = document.getElementById("totalChunks");

// Track whether a PDF has been uploaded
let pdfUploaded = false;

// ===== Utility: Escape HTML to prevent XSS =====
function escapeHtml(text) {
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

// ===== PDF Upload =====
choosePdfBtn.addEventListener("click", () => {
    fileInput.click();
});

fileInput.addEventListener("change", async () => {
    const file = fileInput.files[0];
    if (!file) return;

    // Validate file type on the client side
    if (!file.name.toLowerCase().endsWith(".pdf")) {
        showUploadError("Only PDF files are allowed.");
        return;
    }

    // Validate file size (25 MB)
    if (file.size > 25 * 1024 * 1024) {
        showUploadError("File is too large. Maximum upload size is 25 MB.");
        return;
    }

    fileName.textContent = file.name;
    showUploadProcessing();

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (data.success) {
            showUploadSuccess(data);
            pdfUploaded = true;
            askBtn.disabled = false;
            questionInput.focus();
            fetchStats();
        } else {
            showUploadError(data.error || "Upload failed.");
        }
    } catch (err) {
        showUploadError("Could not connect to the server. Please try again.");
    }

    // Reset the file input so the same file can be re-uploaded
    fileInput.value = "";
});

function showUploadProcessing() {
    uploadStatus.style.display = "block";
    statusProcessing.style.display = "flex";
    statusSuccess.style.display = "none";
    statusError.style.display = "none";
}

function showUploadSuccess(data) {
    statusProcessing.style.display = "none";
    statusSuccess.style.display = "block";
    successDetails.textContent =
        data.pages + " pages processed · " + data.chunks + " chunks created";
}

function showUploadError(message) {
    uploadStatus.style.display = "block";
    statusProcessing.style.display = "none";
    statusSuccess.style.display = "none";
    statusError.style.display = "block";
    errorText.textContent = message;
}

// ===== Fetch Stats =====
async function fetchStats() {
    try {
        const response = await fetch("/stats");
        const data = await response.json();
        if (data.success) {
            totalChunks.textContent = data.total_chunks;
            statsCard.style.display = "block";
        }
    } catch (err) {
        // Silently fail for stats — not critical
    }
}

// ===== Chat: Enter key and button =====
questionInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !askBtn.disabled) {
        askQuestion();
    }
});

askBtn.addEventListener("click", () => {
    askQuestion();
});

// ===== Ask Question =====
async function askQuestion() {
    const question = questionInput.value.trim();

    if (!question) {
        return;
    }

    if (!pdfUploaded) {
        addMessage("ai", "Please upload a PDF first before asking questions.");
        return;
    }

    // Hide empty state on first question
    if (emptyState) {
        emptyState.style.display = "none";
    }

    // Add user message to chat
    addMessage("user", question);
    questionInput.value = "";

    // Show loading state
    setAskLoading(true);
    const thinkingEl = addThinking();

    try {
        const response = await fetch("/ask", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ question: question }),
        });

        const data = await response.json();

        // Remove thinking indicator
        if (thinkingEl) thinkingEl.remove();

        if (data.success) {
            addMessage("ai", data.answer, data.sources || []);
        } else {
            addMessage("ai", data.error || "Something went wrong.");
        }
    } catch (err) {
        if (thinkingEl) thinkingEl.remove();
        addMessage(
            "ai",
            "Could not connect to the server. Please check if the server is running."
        );
    }

    setAskLoading(false);
}

// ===== Loading State for Ask Button =====
function setAskLoading(loading) {
    if (loading) {
        askBtn.disabled = true;
        questionInput.disabled = true;
        askBtnText.style.display = "none";
        askBtnLoading.style.display = "inline-flex";
    } else {
        askBtn.disabled = false;
        questionInput.disabled = false;
        askBtnText.style.display = "inline";
        askBtnLoading.style.display = "none";
        questionInput.focus();
    }
}

// ===== Add a Chat Message =====
function addMessage(role, text, sources) {
    sources = sources || [];

    const wrapper = document.createElement("div");
    wrapper.className = "message message-" + role;

    // Label (You / AI Assistant)
    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = role === "user" ? "You" : "AI Assistant";
    wrapper.appendChild(label);

    // Message bubble with escaped HTML and newlines converted to <br>
    const bubble = document.createElement("div");
    bubble.className = "message-bubble";
    bubble.innerHTML = escapeHtml(text).replace(/\n/g, "<br>");
    wrapper.appendChild(bubble);

    // Source references
    if (sources.length > 0) {
        const sourcesContainer = document.createElement("div");
        sourcesContainer.className = "sources-container";

        const sourcesTitle = document.createElement("div");
        sourcesTitle.className = "sources-title";
        sourcesTitle.textContent = "Sources";
        sourcesContainer.appendChild(sourcesTitle);

        // Deduplicate sources by source+page
        const seen = new Set();
        sources.forEach(function (src) {
            const key = src.source + "-" + src.page;
            if (!seen.has(key)) {
                seen.add(key);
                const tag = document.createElement("span");
                tag.className = "source-tag";
                tag.textContent =
                    "\uD83D\uDCC4 " +
                    escapeHtml(src.source) +
                    " \u2014 Page " +
                    src.page;
                sourcesContainer.appendChild(tag);
            }
        });

        wrapper.appendChild(sourcesContainer);
    }

    chatMessages.appendChild(wrapper);
    scrollToBottom();
}

// ===== Thinking Indicator =====
function addThinking() {
    const wrapper = document.createElement("div");
    wrapper.className = "thinking-message";

    const label = document.createElement("div");
    label.className = "message-label";
    label.textContent = "AI Assistant";
    wrapper.appendChild(label);

    const bubble = document.createElement("div");
    bubble.className = "thinking-bubble";
    bubble.innerHTML =
        '<div class="thinking-dots">' +
        "<span></span><span></span><span></span>" +
        "</div>" +
        " Thinking...";
    wrapper.appendChild(bubble);

    chatMessages.appendChild(wrapper);
    scrollToBottom();
    return wrapper;
}

// ===== Auto-scroll to Bottom =====
function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// ===== Initial Load =====
fetchStats();
