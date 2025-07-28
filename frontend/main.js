const { app, BrowserWindow, ipcMain } = require('electron');
const path = require('path');
const { spawn } = require('child_process');

let mainWindow;
let pythonProcess;

function createWindow() {
  mainWindow = new BrowserWindow({
    width: 1200,
    height: 800,
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
      preload: path.join(__dirname, 'preload.js')
    },
    icon: path.join(__dirname, 'src/assets/icons/icon.png'),
    title: 'Job Application Agent'
  });

  mainWindow.loadFile('src/index.html');

  // Open DevTools in development
  if (process.argv.includes('--dev')) {
    mainWindow.webContents.openDevTools();
  }
}

app.whenReady().then(createWindow);

app.on('window-all-closed', () => {
  if (pythonProcess) {
    pythonProcess.kill();
  }
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// IPC handlers for communication with Python backend
ipcMain.handle('start-agent', async () => {
  if (!pythonProcess) {
    pythonProcess = spawn('python', ['-m', 'job_application_agent'], {
      cwd: path.join(__dirname, '..')
    });

    pythonProcess.stdout.on('data', (data) => {
      console.log(`Python: ${data}`);
      mainWindow.webContents.send('agent-log', data.toString());
    });

    pythonProcess.stderr.on('data', (data) => {
      console.error(`Python Error: ${data}`);
      mainWindow.webContents.send('agent-error', data.toString());
    });
  }
  return { success: true };
});

ipcMain.handle('stop-agent', async () => {
  if (pythonProcess) {
    pythonProcess.kill();
    pythonProcess = null;
  }
  return { success: true };
});

ipcMain.handle('get-dashboard-data', async () => {
  // In a real implementation, this would communicate with the Python backend
  return {
    stats: {
      jobs_found_today: 15,
      applications_sent_today: 3,
      total_jobs: 145,
      total_applications: 23
    },
    recent_jobs: [
      {
        title: "Java Backend Developer",
        company: "Tech Corp",
        location: "Bangalore",
        match_score: 0.85,
        status: "discovered"
      }
    ],
    is_running: !!pythonProcess
  };
});
