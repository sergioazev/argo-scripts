const { app, BrowserWindow, ipcMain, dialog } = require("electron");
const path = require("path");
const os = require("os");
const core = require("./core");

function createWindow() {
  const preloadPath = path.join(__dirname, "preload.js");

  const win = new BrowserWindow({
    width: 1180,
    height: 820,
    title: "Argo Organizador",
    backgroundColor: "#0b0b0d",
    webPreferences: {
      preload: preloadPath,
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false
    }
  });

  win.loadFile(path.join(__dirname, "renderer", "index.html"));
}

app.whenReady().then(createWindow);

app.on("window-all-closed", () => {
  if (process.platform !== "darwin") app.quit();
});

app.on("activate", () => {
  if (BrowserWindow.getAllWindows().length === 0) createWindow();
});

ipcMain.handle("app:home", () => os.homedir());

ipcMain.handle("templates:list", () => Object.keys(core.TEMPLATES));
ipcMain.handle("core:today", () => core.today());

ipcMain.handle("dialog:folder", async () => {
  const res = await dialog.showOpenDialog({
    properties: ["openDirectory", "createDirectory"]
  });
  return res.canceled ? "" : res.filePaths[0];
});

ipcMain.handle("dialog:rollback", async () => {
  const res = await dialog.showOpenDialog({
    properties: ["openFile"],
    filters: [{ name: "Argo Rollback", extensions: ["json"] }]
  });
  return res.canceled ? "" : res.filePaths[0];
});

ipcMain.handle("structure:preview", (_, opts) => core.preview(opts));
ipcMain.handle("structure:apply", (_, opts) => core.applyStructure(opts));
ipcMain.handle("rename:preview", (_, opts) => core.renamePreview(opts));
ipcMain.handle("rename:apply", (_, opts) => core.applyRename(opts));
ipcMain.handle("rename:rollback", (_, rollbackFile) => core.rollback(rollbackFile));
