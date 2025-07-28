// electron-frontend/preload.js

const { contextBridge, ipcRenderer } = require('electron');

contextBridge.exposeInMainWorld('electronAPI', {
  startAgent: () => ipcRenderer.invoke('start-agent'),
  onAgentLog: (callback) => ipcRenderer.on('agent-log', (_, msg) => callback(msg)),
  onAgentError: (callback) => ipcRenderer.on('agent-error', (_, msg) => callback(msg)),
  onAgentStatus: (callback) => ipcRenderer.on('agent-status', (_, msg) => callback(msg)),
});
