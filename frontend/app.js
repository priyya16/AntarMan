let anonId = localStorage.getItem("anon_id");
const API_BASE_URL = "http://localhost:8000";
const DEMO_TEXT_PRESETS = {
  calm: "Today was manageable. I am tired, but I am trying to stay positive and take things one step at a time.",
  stress: "I feel overwhelmed with exams and deadlines. My heart races and I cannot focus properly.",
  crisis: "I feel hopeless and I want to hurt myself."
};

const CANONICAL_EMOTIONS = ["stress", "anxiety", "sadness", "happiness", "anger", "neutral"];

const EMOTION_CHART_COLORS = {
  stress: "rgb(248, 113, 113)",
  anxiety: "rgb(251, 191, 36)",
  sadness: "rgb(96, 165, 250)",
  happiness: "rgb(52, 211, 153)",
  anger: "rgb(249, 115, 22)",
  neutral: "rgb(148, 163, 184)",
  disgust: "rgb(167, 139, 250)",
  surprise: "rgb(56, 189, 248)",
  fear: "rgb(244, 114, 182)",
  joy: "rgb(52, 211, 153)",
  love: "rgb(244, 63, 94)"
};

function emotionLineColor(label) {
  if (EMOTION_CHART_COLORS[label]) return EMOTION_CHART_COLORS[label];
  let h = 0;
  const s = String(label);
  for (let i = 0; i < s.length; i += 1) {
    h = (h * 31 + s.charCodeAt(i)) % 360;
  }
  return `hsl(${h}, 58%, 46%)`;
}

/** Last N calendar days as YYYY-MM-DD in UTC (matches SQLite date(created_at) with UTC timestamps). */
function lastNDayLabelsUtc(n) {
  const labels = [];
  const now = new Date();
  for (let i = n - 1; i >= 0; i -= 1) {
    const d = new Date(Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() - i));
    labels.push(d.toISOString().slice(0, 10));
  }
  return labels;
}

function ensureAnonId(responseAnonId) {
  if (!anonId && responseAnonId) {
    anonId = responseAnonId;
    localStorage.setItem("anon_id", anonId);
  }
}

function escapeHtml(s) {
  const div = document.createElement("div");
  div.textContent = s == null ? "" : String(s);
  return div.innerHTML;
}

function setButtonLoading(btn, loading) {
  if (!btn) return;
  btn.disabled = loading;
  btn.classList.toggle("is-loading", loading);
  const spin = btn.querySelector(".btn__spinner");
  if (spin) spin.hidden = !loading;
}

function applyTextPreset(presetId) {
  const text = DEMO_TEXT_PRESETS[presetId];
  if (!text) return;
  const input = document.getElementById("textInput");
  if (!input) return;
  input.value = text;
  input.focus();
}

async function loadLaunchMeta() {
  const el = document.getElementById("launchMeta");
  if (!el) return;
  try {
    const response = await fetch(API_BASE_URL + "/api/meta");
    if (!response.ok) throw new Error("status endpoint unavailable");
    const data = await response.json();
    const mode = data.model_mode || "unknown";
    el.textContent = `Live status: online • model: ${mode} • version: ${data.version || "n/a"}`;
  } catch (e) {
    el.textContent = "Live status: backend reachable, meta unavailable";
  }
}

function renderResultError(message) {
  const el = document.getElementById("result");
  el.hidden = false;
  el.className = "result-panel result-panel--emergency";
  el.innerHTML = `
    <div class="result-panel__row">
      <div class="result-panel__label">Notice</div>
      <div class="result-panel__value">${escapeHtml(message)}</div>
    </div>`;
}

function renderResult(data) {
  const el = document.getElementById("result");
  const emergency = data.emergency && data.emergency_info;
  el.hidden = false;
  el.className = emergency ? "result-panel result-panel--emergency" : "result-panel";

  let html = `
    <div class="result-panel__row">
      <div class="result-panel__label">Your anonymous ID</div>
      <div class="result-panel__chips"><span class="chip">${escapeHtml(data.anon_id)}</span></div>
    </div>
    <div class="result-panel__row">
      <div class="result-panel__label">Input &amp; understanding</div>
      <div class="result-panel__value">${escapeHtml(data.interpreted_text)}</div>
      <div class="result-panel__chips" style="margin-top:0.5rem">
        <span class="chip">${escapeHtml(data.input_type)}</span>
      </div>
    </div>
    <div class="result-panel__row">
      <div class="result-panel__label">Detected emotion</div>
      <div class="result-panel__chips">
        <span class="chip chip--emotion">${escapeHtml(data.emotion_label)}</span>
        <span class="chip">${escapeHtml(data.intensity)} intensity</span>
      </div>
    </div>
    <div class="result-panel__row">
      <div class="result-panel__label">Support message</div>
      <div class="result-panel__value">${escapeHtml(data.ai_response)}</div>
    </div>`;

  if (emergency) {
    const info = data.emergency_info;
    const lines = (info.helplines || []).map((h) => escapeHtml(h)).join("<br/>");
    html += `
    <div class="result-panel__row">
      <div class="result-panel__label">Crisis resources</div>
      <div class="result-panel__value"><strong>${escapeHtml(info.title)}</strong><br/>${escapeHtml(info.message)}</div>
    </div>
    <div class="result-panel__row">
      <div class="result-panel__label">Helplines</div>
      <div class="result-panel__value">${lines}</div>
    </div>`;
  }

  el.innerHTML = html;
}

async function analyzeText() {
  const text = document.getElementById("textInput").value.trim();
  const country = document.getElementById("country").value;
  if (!text) return;

  const btn = document.getElementById("sendTextBtn");
  setButtonLoading(btn, true);
  try {
    const response = await fetch(API_BASE_URL + "/api/process/text", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        anon_id: anonId,
        text,
        country
      })
    });
    if (!response.ok) {
      const err = await response.json();
      renderResultError(typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail));
      return;
    }
    const data = await response.json();
    ensureAnonId(data.anon_id);
    renderResult(data);
    loadMoodChart();
  } finally {
    setButtonLoading(btn, false);
  }
}

async function uploadFile() {
  const fileInput = document.getElementById("fileInput");
  const country = document.getElementById("country").value;
  if (!fileInput.files.length) {
    alert("Please select a file first");
    return;
  }

  const btn = document.getElementById("uploadBtn");
  setButtonLoading(btn, true);
  try {
    const file = fileInput.files[0];
    
    // Check file size (max 50MB)
    if (file.size > 50 * 1024 * 1024) {
      renderResultError("File is too large. Maximum size is 50MB.");
      return;
    }
    
    const form = new FormData();
    form.append("file", file);
    if (anonId) form.append("anon_id", anonId);
    form.append("country", country);

    console.log("Uploading file:", file.name, "to", API_BASE_URL + "/api/process/upload");
    
    const response = await fetch(API_BASE_URL + "/api/process/upload", {
      method: "POST",
      body: form
    });
    
    if (!response.ok) {
      let detail = `Upload failed (${response.status} ${response.statusText})`;
      try {
        const err = await response.json();
        if (err.detail) detail = typeof err.detail === "string" ? err.detail : JSON.stringify(err.detail);
      } catch (e) {
        console.error("Could not parse error response:", e);
      }
      console.error("Upload error:", detail);
      renderResultError(detail);
      return;
    }
    
    const data = await response.json();
    console.log("Upload success:", data);
    ensureAnonId(data.anon_id);
    renderResult(data);
    fileInput.value = ""; // Clear file input
    loadMoodChart();
  } catch (error) {
    console.error("Upload exception:", error);
    renderResultError("Upload error: " + error.message);
  } finally {
    setButtonLoading(btn, false);
  }
}

async function createPeerPost() {
  const message = document.getElementById("peerPostText").value.trim();
  if (!message) return;
  const btn = document.getElementById("postBtn");
  setButtonLoading(btn, true);
  try {
    const response = await fetch(API_BASE_URL + "/api/peer/posts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ anon_id: anonId, message })
    });
    if (!response.ok) {
      const err = await response.json();
      alert(`Post blocked: ${err.detail}`);
      return;
    }
    const data = await response.json();
    ensureAnonId(data.anon_id);
    document.getElementById("peerPostText").value = "";
    loadPeerFeed();
  } finally {
    setButtonLoading(btn, false);
  }
}

async function createReply(postId, message) {
    const response = await fetch(API_BASE_URL + `/api/peer/posts/${postId}/replies`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ anon_id: anonId, message })
  });
  if (!response.ok) {
    const err = await response.json();
    alert(`Reply blocked: ${err.detail}`);
    return;
  }
  const data = await response.json();
  ensureAnonId(data.anon_id);
  loadPeerFeed();
}

function buildPostElement(post) {
  const wrapper = document.createElement("article");
  wrapper.className = "post-card";

  const main = document.createElement("div");
  const meta = document.createElement("div");
  meta.className = "post-card__meta";
  meta.textContent = `${post.anon_id} · ${post.created_at}`;
  const body = document.createElement("div");
  body.className = "post-card__body";
  body.textContent = post.message;
  main.appendChild(meta);
  main.appendChild(body);
  wrapper.appendChild(main);

  if (post.replies && post.replies.length) {
    post.replies.forEach((reply) => {
      const block = document.createElement("div");
      block.className = "post-card__reply";
      const rmeta = document.createElement("div");
      rmeta.className = "post-card__meta";
      rmeta.textContent = `↳ ${reply.anon_id} · ${reply.created_at}`;
      const rbody = document.createElement("div");
      rbody.className = "post-card__body";
      rbody.textContent = reply.message;
      block.appendChild(rmeta);
      block.appendChild(rbody);
      wrapper.appendChild(block);
    });
  }

  const replyRow = document.createElement("div");
  replyRow.className = "reply-row";
  const replyInput = document.createElement("input");
  replyInput.type = "text";
  replyInput.placeholder = "Write a supportive reply…";
  replyInput.setAttribute("aria-label", "Reply to this post");
  const btn = document.createElement("button");
  btn.type = "button";
  btn.className = "btn btn--secondary";
  btn.textContent = "Reply";
  btn.addEventListener("click", () => {
    const msg = replyInput.value.trim();
    if (!msg) return;
    createReply(post.id, msg);
    replyInput.value = "";
  });
  replyRow.appendChild(replyInput);
  replyRow.appendChild(btn);
  wrapper.appendChild(replyRow);

  return wrapper;
}

async function loadPeerFeed() {
  const response = await fetch(API_BASE_URL + "/api/peer/feed");
  const feed = await response.json();
  const container = document.getElementById("peerFeed");
  container.innerHTML = "";
  feed.forEach((post) => container.appendChild(buildPostElement(post)));
}

function buildMoodSeries(rawStats, days) {
  const labels = lastNDayLabelsUtc(days);
  const byDate = {};
  rawStats.forEach((row) => {
    if (!row.day || !row.emotion_label) return;
    if (!byDate[row.day]) byDate[row.day] = {};
    byDate[row.day][row.emotion_label] = row.total;
  });

  const seen = new Set();
  rawStats.forEach((row) => {
    if (row.emotion_label) seen.add(row.emotion_label);
  });
  const extras = [...seen].filter((e) => !CANONICAL_EMOTIONS.includes(e)).sort();
  const emotions = [...CANONICAL_EMOTIONS, ...extras];

  const datasets = emotions.map((emotion) => ({
    label: emotion,
    data: labels.map((day) => (byDate[day] && byDate[day][emotion]) || 0),
    tension: 0.35,
    fill: false,
    borderColor: emotionLineColor(emotion),
    backgroundColor: "transparent",
    borderWidth: 2,
    pointRadius: 3,
    pointHoverRadius: 5
  }));
  return { labels, datasets };
}

let moodChart;
const MOOD_CHART_DAYS = 7;

async function loadMoodChart() {
  const response = await fetch(API_BASE_URL + `/api/stats/daily-mood?days=${MOOD_CHART_DAYS}`);
  const stats = await response.json();
  const series = buildMoodSeries(stats, MOOD_CHART_DAYS);
  const ctx = document.getElementById("moodChart");
  if (!ctx) return;
  if (moodChart) moodChart.destroy();
  moodChart = new Chart(ctx, {
    type: "line",
    data: {
      labels: series.labels,
      datasets: series.datasets
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      interaction: { mode: "index", intersect: false },
      plugins: {
        legend: {
          position: "bottom",
          labels: {
            usePointStyle: true,
            padding: 12,
            font: { family: "'Plus Jakarta Sans', sans-serif", size: 11 },
            boxWidth: 8
          }
        }
      },
      scales: {
        x: {
          grid: { color: "rgba(99, 102, 241, 0.06)" },
          ticks: { font: { family: "'Plus Jakarta Sans', sans-serif" } }
        },
        y: {
          beginAtZero: true,
          ticks: { precision: 0 },
          grid: { color: "rgba(99, 102, 241, 0.08)" }
        }
      }
    }
  });
}

document.getElementById("sendTextBtn").addEventListener("click", analyzeText);
document.getElementById("uploadBtn").addEventListener("click", uploadFile);
document.getElementById("postBtn").addEventListener("click", createPeerPost);
document.querySelectorAll(".preset-chip").forEach((btn) => {
  btn.addEventListener("click", () => applyTextPreset(btn.dataset.preset));
});

// File input debugging
const fileInput = document.getElementById("fileInput");
if (fileInput) {
  fileInput.addEventListener("change", function(e) {
    console.log("File selected:", this.files.length, this.files[0]?.name);
  });
}

loadPeerFeed();
loadMoodChart();
loadLaunchMeta();
