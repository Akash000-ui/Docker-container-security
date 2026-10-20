(() => {
  const id = window.containerMonitorId;
  const endpoint = (name) => `/api/containers/${encodeURIComponent(id)}/${name}`;
  const byId = (name) => document.getElementById(name);

  const formatBytes = (value) => {
    if (!Number.isFinite(value) || value <= 0) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB"];
    const index = Math.min(Math.floor(Math.log(value) / Math.log(1024)), units.length - 1);
    return `${(value / (1024 ** index)).toFixed(index ? 1 : 0)} ${units[index]}`;
  };

  const setMeter = (id, percentage) => {
    const meter = byId(id);
    meter.style.width = `${Math.min(Math.max(percentage || 0, 0), 100)}%`;
  };

  const showError = (message) => {
    const error = byId("monitor-error");
    error.textContent = message;
    error.classList.remove("hidden");
    byId("monitor-status").textContent = "Unavailable";
  };

  const fetchJson = async (url) => {
    const response = await fetch(url);
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.error || "Request failed");
    return payload;
  };

  const refreshStats = async () => {
    try {
      const stats = await fetchJson(endpoint("stats"));
      byId("cpu-value").textContent = `${stats.cpu_percent.toFixed(2)}%`;
      byId("memory-value").textContent = `${stats.memory_percent.toFixed(2)}%`;
      byId("memory-note").textContent = `${formatBytes(stats.memory_usage)} of ${formatBytes(stats.memory_limit)}`;
      byId("network-value").textContent = `${formatBytes(stats.network_rx + stats.network_tx)}`;
      byId("network-note").textContent = `RX ${formatBytes(stats.network_rx)} / TX ${formatBytes(stats.network_tx)}`;
      byId("block-value").textContent = `${formatBytes(stats.block_read + stats.block_write)}`;
      byId("block-note").textContent = `Read ${formatBytes(stats.block_read)} / Write ${formatBytes(stats.block_write)}`;
      byId("updated-at").textContent = new Date(stats.captured_at).toLocaleTimeString();
      setMeter("cpu-meter", stats.cpu_percent);
      setMeter("memory-meter", stats.memory_percent);
      byId("monitor-status").textContent = stats.status;
      byId("monitor-error").classList.add("hidden");
    } catch (error) { showError(error.message); }
  };

  const refreshLogs = async () => {
    try { byId("logs-output").textContent = (await fetchJson(endpoint("logs?tail=200"))).logs || "No logs available."; }
    catch (error) { byId("logs-output").textContent = error.message; }
  };

  const refreshProcesses = async () => {
    const target = byId("processes-table");
    try {
      const payload = await fetchJson(endpoint("processes"));
      const titles = payload.Titles || [];
      const processes = payload.Processes || [];
      if (!processes.length) { target.innerHTML = '<p class="muted">No process information available.</p>'; return; }
      const head = titles.map((title) => `<th>${title}</th>`).join("");
      const rows = processes.map((process) => `<tr>${process.map((value) => `<td>${value}</td>`).join("")}</tr>`).join("");
      target.innerHTML = `<table><thead><tr>${head}</tr></thead><tbody>${rows}</tbody></table>`;
    } catch (error) { target.innerHTML = `<p class="muted">${error.message}</p>`; }
  };

  byId("refresh-logs").addEventListener("click", refreshLogs);
  refreshStats();
  refreshLogs();
  refreshProcesses();
  window.setInterval(refreshStats, 5000);
})();

