const API_BASE = "/api";
const PAGE_SIZE = 25;

const statusBadge = document.getElementById("status-badge");
const syncOutput = document.getElementById("sync-output");
const scanOutput = document.getElementById("scan-output");
const tableBody = document.querySelector("#kev-table tbody");
const scanTableBody = document.querySelector("#scan-table tbody");
const statsCards = document.getElementById("stats-cards");
const pageInfo = document.getElementById("page-info");
const btnPrev = document.getElementById("btn-prev");
const btnNext = document.getElementById("btn-next");

let state = { offset: 0, total: 0, keyword: "" };

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

function formatTimestamp(value) {
  if (!value) return "N/A";
  const n = Number(value);
  if (!Number.isFinite(n)) return value;
  return new Date(n * 1000).toLocaleString();
}

async function refreshStats() {
  try {
    const res = await fetch(`${API_BASE}/stats`);
    const data = await res.json();
    const topVendors = (data.top_vendors || [])
      .map((v) => `${v.vendor} (${v.count})`)
      .join(", ") || "-";
    statsCards.innerHTML = "";
    const cards = [
      ["Total CVE", data.total ?? 0],
      ["Ransomware-linked", data.ransomware_count ?? 0],
      ["Terakhir ditambahkan", data.latest_date_added || "N/A"],
      ["Sync terakhir", formatTimestamp(data.last_sync_at)],
      ["Top vendor", topVendors],
    ];
    for (const [label, value] of cards) {
      const div = document.createElement("div");
      div.className = "stat-card";
      div.innerHTML = `<div class="stat-label">${label}</div><div class="stat-value">${value}</div>`;
      statsCards.appendChild(div);
    }
  } catch (e) {
    statsCards.innerHTML = "<div class=\"stat-card\">Gagal memuat statistik</div>";
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

function updatePagination() {
  const shownTo = Math.min(state.offset + PAGE_SIZE, state.total);
  pageInfo.textContent = state.total > 0
    ? `${state.offset + 1}-${shownTo} dari ${state.total}`
    : "Tidak ada data";
  btnPrev.disabled = state.offset <= 0;
  btnNext.disabled = shownTo >= state.total;
}

async function loadPage() {
  const params = new URLSearchParams({ limit: PAGE_SIZE, offset: state.offset });
  if (state.keyword) params.set("q", state.keyword);
  const res = await fetch(`${API_BASE}/kev?${params.toString()}`);
  const data = await res.json();
  state.total = data.total || 0;
  renderRows(data.items || []);
  updatePagination();
}

async function loadAll() {
  state.keyword = "";
  state.offset = 0;
  await loadPage();
}

async function search(keyword) {
  state.keyword = keyword;
  state.offset = 0;
  await loadPage();
}

async function refreshScans() {
  try {
    const res = await fetch(`${API_BASE}/scans`);
    const data = await res.json();
    scanTableBody.innerHTML = "";
    for (const entry of data) {
      const tr = document.createElement("tr");
      const cells = [
        entry.id,
        entry.platform,
        entry.status,
        entry.backup_path || "",
        formatTimestamp(entry.created_at),
      ];
      for (const value of cells) {
        const td = document.createElement("td");
        td.textContent = value;
        tr.appendChild(td);
      }
      scanTableBody.appendChild(tr);
    }
  } catch (e) {
    scanTableBody.innerHTML = "";
  }
}

document.getElementById("btn-list").addEventListener("click", loadAll);

document.getElementById("btn-search").addEventListener("click", () => {
  const keyword = document.getElementById("search-input").value;
  search(keyword);
});

document.getElementById("search-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") search(e.target.value);
});

btnPrev.addEventListener("click", () => {
  state.offset = Math.max(0, state.offset - PAGE_SIZE);
  loadPage();
});

btnNext.addEventListener("click", () => {
  state.offset += PAGE_SIZE;
  loadPage();
});

document.getElementById("btn-sync").addEventListener("click", async () => {
  syncOutput.textContent = "Syncing...";
  const res = await fetch(`${API_BASE}/sync`, { method: "POST" });
  const data = await res.json();
  syncOutput.textContent = JSON.stringify(data, null, 2);
  refreshHealth();
  refreshStats();
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
  refreshScans();
});

refreshHealth();
refreshStats();
loadAll();
refreshScans();
