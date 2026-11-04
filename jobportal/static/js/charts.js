// Reads chart definitions rendered by Django (json_script) and draws them with Chart.js.
(function () {
  var el = document.getElementById("charts-data");
  if (!el || typeof Chart === "undefined") return;
  var charts = JSON.parse(el.textContent);
  var palette = ["#0d6efd", "#198754", "#ffc107", "#dc3545", "#6f42c1", "#20c997", "#fd7e14", "#0dcaf0"];

  charts.forEach(function (c) {
    var canvas = document.getElementById(c.id);
    if (!canvas) return;
    var circular = c.type === "doughnut" || c.type === "pie";
    new Chart(canvas, {
      type: c.type,
      data: {
        labels: c.labels,
        datasets: [{
          label: c.title,
          data: c.data,
          backgroundColor: circular || c.type === "bar" ? palette : "rgba(13,110,253,.15)",
          borderColor: "#0d6efd",
          fill: c.type === "line",
          tension: 0.3
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: circular } },
        scales: circular ? {} : { y: { beginAtZero: true, ticks: { precision: 0 } } }
      }
    });
  });
})();
