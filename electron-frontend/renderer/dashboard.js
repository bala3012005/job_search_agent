// electron-frontend/renderer/dashboard.js

document.addEventListener('DOMContentLoaded', () => {
  const logOutput = document.getElementById('log-output');
  const startButton = document.getElementById('start-agent');

  // Stats placeholders (later fetch from SQLite)
  const updateStats = () => {
    document.getElementById('jobs-found').textContent = '15'; // placeholder
    document.getElementById('apps-sent').textContent = '10';  // placeholder
    document.getElementById('total-jobs').textContent = '150';
    document.getElementById('total-apps').textContent = '100';
  };

  // Launch agent on button click
  startButton.addEventListener('click', () => {
    window.electronAPI.startAgent();
    appendLog('🟢 Agent started...');
  });

  // Append log to UI
  const appendLog = (msg) => {
    logOutput.textContent += msg + '\n';
    logOutput.scrollTop = logOutput.scrollHeight;
  };

  // IPC Listeners from backend
  window.electronAPI.onAgentLog(msg => appendLog('📄 ' + msg));
  window.electronAPI.onAgentError(msg => appendLog('❗ ' + msg));
  window.electronAPI.onAgentStatus(msg => appendLog('✅ ' + msg));

  // Initialize chart
  const ctx = document.getElementById('applications-chart');
  const chart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
      datasets: [{
        label: 'Applications Sent',
        data: [1, 2, 4, 3, 5],
        borderColor: 'rgb(75, 192, 192)',
        tension: 0.2
      }]
    },
    options: {
      responsive: true,
      plugins: { legend: { position: 'top' } }
    }
  });

  updateStats();
});
