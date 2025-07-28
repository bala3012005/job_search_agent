// electron-frontend/main.js

const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      preload: path.join(__dirname, 'preload.js'),
      contextIsolation: true,
      nodeIntegration: false,
    },
  });

  mainWindow.loadFile(path.join(__dirname, 'renderer', 'index.html'));

  // Open DevTools if needed
  // mainWindow.webContents.openDevTools();
}

app.whenReady().then(createWindow);

// Handle start-agent event from frontend
ipcMain.handle('start-agent', async () => {
  const agentPath = path.join(__dirname, '../job-application-agent/src/job_application_agent/core/agent.py');
  const python = spawn('python', [agentPath]);

  python.stdout.on('data', (data) => {
    mainWindow.webContents.send('agent-log', data.toString());
  });

  python.stderr.on('data', (data) => {
    mainWindow.webContents.send('agent-error', data.toString());
  });

  python.on('close', (code) => {
    mainWindow.webContents.send('agent-status', `Agent exited with code ${code}`);
  });
});

app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') app.quit();
});
