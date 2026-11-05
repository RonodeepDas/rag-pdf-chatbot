const statusBox = document.getElementById("status");
const responseBox = document.getElementById("response");
const uploadBtn = document.getElementById("uploadBtn");
const askBtn = document.getElementById("askBtn");
const fileInput = document.getElementById("pdfFile");
const questionInput = document.getElementById("question");

const API_BASE_URL = "https://rag-pdf-chatbot-bgwi.onrender.com";
let uploaded = false;

uploadBtn.addEventListener("click", async () => {
  const file = fileInput.files[0];
  if (!file) {
    statusBox.textContent = "Please choose a PDF first.";
    return;
  }

  const formData = new FormData();
  formData.append("file", file);

  statusBox.textContent = "Processing PDF...";
  try {
    const res = await fetch(`${API_BASE_URL}/api/process`, {
      method: "POST",
      body: formData,
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Failed to process PDF.");
    }

    uploaded = true;
    statusBox.textContent = `Ready. Indexed ${data.chunks} chunks from ${data.pages} pages.`;
    responseBox.textContent = "Document loaded. Ask a question below.";
  } catch (err) {
    statusBox.textContent = err.message;
  }
});

askBtn.addEventListener("click", async () => {
  const question = questionInput.value.trim();
  if (!question) {
    responseBox.textContent = "Please enter a question.";
    return;
  }
  if (!uploaded) {
    responseBox.textContent =
      "Please upload and process a PDF before asking a question.";
    return;
  }

  responseBox.textContent = "Thinking...";
  try {
    const res = await fetch(`${API_BASE_URL}/api/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });
    const data = await res.json();

    if (!res.ok) {
      throw new Error(data.detail || "Request failed.");
    }

    const pages =
      data.pages && data.pages.length ? data.pages.join(", ") : "n/a";
    responseBox.textContent = `${data.answer}\n\nSources: pages ${pages}`;
  } catch (err) {
    responseBox.textContent = err.message;
  }
});
