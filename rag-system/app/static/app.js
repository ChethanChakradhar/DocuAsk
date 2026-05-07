const state = {
  documents: [],
};

const els = {
  statusDot: document.querySelector("#statusDot"),
  statusText: document.querySelector("#statusText"),
  docCount: document.querySelector("#docCount"),
  chunkCount: document.querySelector("#chunkCount"),
  lockButton: document.querySelector("#lockButton"),
  refreshButton: document.querySelector("#refreshButton"),
  uploadForm: document.querySelector("#uploadForm"),
  fileInput: document.querySelector("#fileInput"),
  fileList: document.querySelector("#fileList"),
  dropZone: document.querySelector("#dropZone"),
  uploadButton: document.querySelector("#uploadButton"),
  documentList: document.querySelector("#documentList"),
  libraryStatus: document.querySelector("#libraryStatus"),
  setupNote: document.querySelector("#setupNote"),
  billingNote: document.querySelector("#billingNote"),
  askForm: document.querySelector("#askForm"),
  questionInput: document.querySelector("#questionInput"),
  topKInput: document.querySelector("#topKInput"),
  askButton: document.querySelector("#askButton"),
  answerArea: document.querySelector("#answerArea"),
  toast: document.querySelector("#toast"),
};

async function requestJson(url, options = {}) {
  const response = await fetch(url, options);
  const text = await response.text();
  const payload = text ? JSON.parse(text) : {};

  if (!response.ok) {
    const detail = payload.detail || response.statusText || "Request failed";
    throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join(", ") : detail);
  }

  return payload;
}

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("visible");
  window.clearTimeout(showToast.timer);
  showToast.timer = window.setTimeout(() => {
    els.toast.classList.remove("visible");
  }, 4200);
}

function showSetupHelp(message) {
  const lowerMessage = message.toLowerCase();
  const isKeyProblem = lowerMessage.includes("api key");
  const isQuotaProblem = lowerMessage.includes("quota") || lowerMessage.includes("billing");
  els.setupNote.hidden = !isKeyProblem;
  els.billingNote.hidden = !isQuotaProblem;
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  }).format(new Date(value));
}

function setBusy(button, busy, label) {
  button.disabled = busy;
  if (label) {
    button.dataset.readyLabel ||= button.textContent;
    button.textContent = busy ? label : button.dataset.readyLabel;
  }
}

async function checkHealth() {
  try {
    await requestJson("/health");
    els.statusDot.classList.add("ok");
    els.statusText.textContent = "Ready when you are";
  } catch (error) {
    els.statusDot.classList.remove("ok");
    els.statusText.textContent = "Needs a restart";
  }
}

async function loadDocuments() {
  els.libraryStatus.textContent = "Checking";
  try {
    const payload = await requestJson("/documents");
    state.documents = payload.documents || [];
    renderDocuments();
    els.libraryStatus.textContent = "Ready";
  } catch (error) {
    els.documentList.innerHTML = renderEmpty("I could not load your documents right now.");
    els.libraryStatus.textContent = "Needs attention";
    showToast(error.message);
  }
}

function renderEmpty(message) {
  return `
    <div class="empty-state">
      <span class="answer-glyph" aria-hidden="true"></span>
      <p>${escapeHtml(message)}</p>
    </div>
  `;
}

function renderDocuments() {
  const totalChunks = state.documents.reduce((sum, doc) => sum + doc.chunk_count, 0);
  if (els.docCount) {
    els.docCount.textContent = state.documents.length;
  }
  if (els.chunkCount) {
    els.chunkCount.textContent = totalChunks;
  }

  if (!state.documents.length) {
    els.documentList.innerHTML = renderEmpty("Your library is empty. Add a document to begin.");
    return;
  }

  els.documentList.innerHTML = state.documents
    .map(
      (doc) => `
        <article class="document-card">
          <div class="document-main">
            <div>
              <p class="document-title">${escapeHtml(doc.filename)}</p>
              <div class="document-meta">
                <span>${doc.page_count} pages</span>
                <span>${doc.chunk_count} passages</span>
                <span>Added ${formatDate(doc.ingested_at)}</span>
              </div>
            </div>
            <button class="danger-button" type="button" data-delete="${doc.doc_id}">Delete</button>
          </div>
        </article>
      `
    )
    .join("");
}

function renderFileList() {
  const files = Array.from(els.fileInput.files || []);
  els.fileList.textContent = files.length
    ? files.map((file) => file.name).join(", ")
    : "No files selected";
}

async function uploadDocuments(event) {
  event.preventDefault();
  const files = Array.from(els.fileInput.files || []);

  if (!files.length) {
    showToast("Choose at least one PDF first.");
    return;
  }

  const body = new FormData();
  files.forEach((file) => body.append("files", file));

  setBusy(els.uploadButton, true, "Adding...");
  try {
    const payload = await requestJson("/documents/upload", {
      method: "POST",
      body,
    });
    els.uploadForm.reset();
    renderFileList();
    await loadDocuments();
    showToast(`Added ${payload.documents.length} document(s).`);
  } catch (error) {
    showSetupHelp(error.message);
    showToast(error.message);
  } finally {
    setBusy(els.uploadButton, false);
  }
}

async function deleteDocument(docId) {
  try {
    await requestJson(`/documents/${docId}`, { method: "DELETE" });
    await loadDocuments();
    showToast("Removed from your library.");
  } catch (error) {
    showToast(error.message);
  }
}

async function askQuestion(event) {
  event.preventDefault();
  const question = els.questionInput.value.trim();

  if (question.length < 3) {
    showToast("Type a slightly longer question.");
    return;
  }

  setBusy(els.askButton, true, "Reading...");
  els.answerArea.innerHTML = renderEmpty("Reading your documents...");

  try {
    const payload = await requestJson("/qa/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question,
        top_k: Number(els.topKInput.value) || undefined,
      }),
    });
    renderAnswer(payload);
  } catch (error) {
    els.answerArea.innerHTML = renderEmpty("I could not answer that yet.");
    showToast(error.message);
  } finally {
    setBusy(els.askButton, false);
  }
}

function renderAnswer(payload) {
  const groundedLabel = payload.grounded ? "Answer from your PDF" : "Not enough detail";

  els.answerArea.innerHTML = `
    <div class="answer-card">
      <div class="answer-header">
        <div>
          <p class="eyebrow">${escapeHtml(groundedLabel)}</p>
          <h3>${payload.grounded ? "Here is the direct answer" : "I could not confirm that"}</h3>
        </div>
      </div>
      <div class="answer-text">${formatAnswer(payload.answer)}</div>
    </div>
  `;
}

function formatAnswer(answer) {
  const cleaned = String(answer)
    .replace(/\s*\[C\d+\]/g, "")
    .replace(/\*\*(.*?)\*\*/g, "$1")
    .trim();
  const lines = cleaned.split(/\n+/).map((line) => line.trim()).filter(Boolean);
  const blocks = [];
  let listItems = [];

  function flushList() {
    if (!listItems.length) {
      return;
    }
    blocks.push(`<ol>${listItems.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ol>`);
    listItems = [];
  }

  lines.forEach((line) => {
    const numbered = line.match(/^\d+\.\s+(.*)$/);
    if (numbered) {
      listItems.push(numbered[1]);
      return;
    }

    flushList();
    blocks.push(`<p>${escapeHtml(line)}</p>`);
  });

  flushList();

  return blocks.join("");
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

els.refreshButton.addEventListener("click", () => {
  checkHealth();
  loadDocuments();
});
els.lockButton.addEventListener("click", async () => {
  await fetch("/auth/lock", { method: "POST" });
  window.location.href = "/login";
});
els.fileInput.addEventListener("change", renderFileList);
els.uploadForm.addEventListener("submit", uploadDocuments);
els.askForm.addEventListener("submit", askQuestion);
els.documentList.addEventListener("click", (event) => {
  const button = event.target.closest("[data-delete]");
  if (button) {
    deleteDocument(button.dataset.delete);
  }
});

["dragenter", "dragover"].forEach((eventName) => {
  els.dropZone.addEventListener(eventName, (event) => {
    event.preventDefault();
    els.dropZone.classList.add("dragging");
  });
});

["dragleave", "drop"].forEach((eventName) => {
  els.dropZone.addEventListener(eventName, () => {
    els.dropZone.classList.remove("dragging");
  });
});

els.dropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  els.fileInput.files = event.dataTransfer.files;
  renderFileList();
});

checkHealth();
loadDocuments();

if (new URLSearchParams(window.location.search).get("unlocked") === "1") {
  showToast("Unlocked. You can ask your PDFs now.");
  window.history.replaceState({}, "", window.location.pathname);
}
