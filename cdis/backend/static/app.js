const API_BASE = "/api";

const statusBadge = document.getElementById("status-badge");
const syncOutput = document.getElementById("sync-output");
const scanOutput = document.getElementById("scan-output");
const tableBody = document.querySelector("#kev-table tbody");

async function refreshHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    const data = await res.json();
    statusBadge.textContent = `online - ${data.kev_count} CVE - mvt: ${data.mvt_available ? "ready" : "not installed"}`;
    statusBadge.className = "badge ok";
  } catch (e) {
    statusBadge.textContent = "backend unreachable";
    statusBadge.className = "badge down";
  }
}

function renderRows(rows) {
  tableBody.innerHTML = "";
  for (const item of rows) {
    const tr = document.createElement("tr");
    const cells = [
      item.cveID || "N/A",
      item.vulnerabilityName || "N/A",
      item.vendorProject || "N/A",
      item.dateAdded || "N/A",
    ];
    for (const value of cells) {
      const td = document.createElement("td");
      td.textContent = value;
      tr.appendChild(td);
    }
    tableBody.appendChild(tr);
  }
}

async function loadAll() {
  const res = await fetch(`${API_BASE}/kev`);
  const data = await res.json();
  renderRows(data.slice(0, 200));
}

async function search(keyword) {
  const res = await fetch(`${API_BASE}/kev/search?q=${encodeURIComponent(keyword)}`);
  const data = await res.json();
  renderRows(data.slice(0, 200));
}

document.getElementById("btn-list").addEventListener("click", loadAll);

document.getElementById("btn-search").addEventListener("click", () => {
  const keyword = document.getElementById("search-input").value;
  search(keyword);
});

document.getElementById("search-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") search(e.target.value);
});

document.getElementById("btn-sync").addEventListener("click", async () => {
  syncOutput.textContent = "Syncing...";
  const res = await fetch(`${API_BASE}/sync`, { method: "POST" });
  const data = await res.json();
  syncOutput.textContent = JSON.stringify(data, null, 2);
  refreshHealth();
  loadAll();
});

document.getElementById("btn-scan").addEventListener("click", async () => {
  const platform = document.getElementById("scan-platform").value;
  const backupPath = document.getElementById("scan-path").value;
  if (!backupPath) {
    scanOutput.textContent = "Isi path backup dulu.";
    return;
  }
  scanOutput.textContent = "Scanning...";
  const res = await fetch(`${API_BASE}/scan/${platform}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ backup_path: backupPath }),
  });
  const data = await res.json();
  scanOutput.textContent = JSON.stringify(data, null, 2);
});

refreshHealth();
loadAll();
