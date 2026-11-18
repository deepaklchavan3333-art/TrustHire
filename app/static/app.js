const esc = (value) => String(value ?? "").replace(/[&<>"']/g, ch => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[ch]));
async function readJson(response) {
  const data = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(data.error || `Request failed (${response.status})`);
  return data;
}
const form = document.getElementById("predict-form");
if (form) {
  document.getElementById("sample").addEventListener("click", event => {
    event.preventDefault(); form.elements.title.value = "Work From Home Data Entry";
    form.elements.description.value = "Earn $8000 per month! Pay a registration fee to start immediately. No experience needed.";
  });
  form.addEventListener("submit", async event => {
    event.preventDefault();
    const error = document.getElementById("error"); error.hidden = true;
    const button = document.getElementById("submit-button"); button.disabled = true; button.textContent = "Checking…";
    const fields = Object.fromEntries(new FormData(form).entries());
    try {
      const result = await readJson(await fetch("/api/predict", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(fields) }));
      const section = document.getElementById("result");
      const fake = result.label === "fake";
      section.innerHTML = `<div class="eyebrow">Screening result · ${esc(result.model_version)}</div><h1 class="${fake ? "fake" : "genuine"}">${fake ? "Likely fake" : "Looks genuine"}</h1><p>Estimated fake probability <strong>${(result.probability_fake * 100).toFixed(1)}%</strong></p><div class="meter"><i style="width:${Math.max(0, Math.min(100, result.probability_fake * 100))}%"></i></div><p class="muted">Confidence in this verdict: ${esc(result.confidence)}%</p><h3>Signals to review</h3><ul>${result.top_signals.map(s => `<li>${esc(s)}</li>`).join("")}</ul>${result.red_flags.length ? `<h3>Red flags</h3><ul>${result.red_flags.map(s => `<li>${esc(s)}</li>`).join("")}</ul>` : ""}<aside>Never pay to apply for a job. Verify the employer's website and contact details independently before sharing sensitive information.</aside><p><a href="/">← Check another posting</a></p>`;
      section.hidden = false; form.hidden = true;
    } catch (err) { error.textContent = err.message; error.hidden = false; }
    finally { button.disabled = false; button.innerHTML = 'Check posting <span>→</span>'; }
  });
}
const bulkForm = document.getElementById("bulk-form");
if (bulkForm) {
  bulkForm.addEventListener("submit", async event => {
    event.preventDefault();
    const error = document.getElementById("error"); error.hidden = true;
    const button = bulkForm.querySelector("button"); button.disabled = true; button.textContent = "Analyzing…";
    try {
      const data = await readJson(await fetch("/api/bulk", { method: "POST", body: new FormData(bulkForm) }));
      const tbody = document.getElementById("bulk-body"); tbody.replaceChildren();
      data.results.forEach(row => {
        const tr = document.createElement("tr");
        const vals = [row.title, row.label, row.probability_fake == null ? "" : `${(row.probability_fake * 100).toFixed(1)}%`, (row.top_signals || []).join(", ")];
        vals.forEach(value => { const td = document.createElement("td"); td.textContent = value; tr.appendChild(td); }); tbody.appendChild(tr);
      });
      document.getElementById("bulk-results").hidden = false;
    } catch (err) { error.textContent = err.message; error.hidden = false; }
    finally { button.disabled = false; button.textContent = "Analyze CSV →"; }
  });
  document.getElementById("download-results").addEventListener("click", () => {
    const quote = value => `"${String(value).replaceAll('"', '""')}"`;
    const rows = [["Title", "Verdict", "Fake probability", "Signals"], ...[...document.querySelectorAll("#bulk-body tr")].map(tr => [...tr.cells].map(td => td.textContent))];
    const blob = new Blob([rows.map(row => row.map(quote).join(",")).join("\r\n")], { type: "text/csv;charset=utf-8" });
    const link = document.createElement("a"); link.href = URL.createObjectURL(blob); link.download = "jobcheck-results.csv"; link.click(); URL.revokeObjectURL(link.href);
  });
}
const historyBody = document.getElementById("history-body");
if (historyBody) readJson(fetch("/api/history")).then(data => {
  historyBody.replaceChildren();
  if (!data.rows.length) { historyBody.innerHTML = '<tr><td colspan="4">No predictions yet.</td></tr>'; return; }
  data.rows.forEach(row => { const tr = document.createElement("tr"); const vals = [row.created_at, row.label, `${(row.probability_fake * 100).toFixed(1)}%`, `${row.text_hash.slice(0, 16)}…`]; vals.forEach(value => { const td = document.createElement("td"); td.textContent = value; tr.appendChild(td); }); historyBody.appendChild(tr); });
}).catch(err => { historyBody.innerHTML = `<tr><td colspan="4">${esc(err.message)}</td></tr>`; });
const metricsContent = document.getElementById("metrics-content");
if (metricsContent) readJson(fetch("/api/metrics")).then(data => {
  if (!data.metrics) { metricsContent.innerHTML = `<section class="card"><h2>No evaluation metrics yet</h2><p>Current service: <strong>${esc(data.model_version)}</strong>. Add the EMSCAD CSV and run <code>python ml/train.py</code> to create the model and metrics file.</p></section>`; return; }
  const m = data.metrics;
  metricsContent.innerHTML = `<section class="stats">${[["accuracy", "Accuracy"], ["precision_fake", "Fake precision"], ["recall_fake", "Fake recall"], ["f1_fake", "Fake F1"]].map(([k, label]) => `<div class="card stat"><span>${label}</span><strong>${(m[k] * 100).toFixed(1)}%</strong></div>`).join("")}</section><section class="card"><h2>Confusion matrix</h2><p>Rows = actual class; columns = predicted class. Order: genuine, fake.</p><pre>${esc(JSON.stringify(m.confusion_matrix, null, 2))}</pre><p>${esc(m.model)} · ${esc(m.test_size)} test examples</p></section>`;
}).catch(err => { metricsContent.innerHTML = `<div class="alert">${esc(err.message)}</div>`; });
