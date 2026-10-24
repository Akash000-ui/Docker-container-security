(() => {
  const chartColors = ["#ff6b6b", "#ff922b", "#ffd166", "#74c0fc", "#9aaac0"];
  const byId = (id) => document.getElementById(id);
  const makeChart = (id, type, labels, values, colors = chartColors) => {
    const canvas = byId(id);
    if (!canvas) return;
    new Chart(canvas, { type, data: { labels, datasets: [{ data: values, backgroundColor: colors, borderColor: "#293548", borderWidth: 1 }] }, options: { responsive: true, plugins: { legend: { labels: { color: "#eef4fb" } } }, scales: type === "bar" ? { x: { ticks: { color: "#9aaac0" }, grid: { color: "#293548" } }, y: { beginAtZero: true, ticks: { color: "#9aaac0", precision: 0 }, grid: { color: "#293548" } } } : {} } });
  };

  fetch("/api/dashboard/summary").then((response) => response.json()).then((payload) => {
    const status = payload.container_status || {};
    const alertSeverity = payload.alert_severity || {};
    const vulnerabilitySeverity = payload.vulnerability_severity || {};
    makeChart("container-status-chart", "doughnut", Object.keys(status), Object.values(status), ["#63e6be", "#ffb36b", "#ff8f8f", "#74c0fc"]);
    makeChart("alert-severity-chart", "bar", Object.keys(alertSeverity), Object.values(alertSeverity));
    makeChart("vulnerability-severity-chart", "bar", Object.keys(vulnerabilitySeverity), Object.values(vulnerabilitySeverity));
  }).catch(() => { document.querySelectorAll(".chart-empty").forEach((element) => { element.textContent = "Chart data is unavailable."; }); });
})();
