const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("argo", {
  home: () => ipcRenderer.invoke("app:home"),

  listTemplates: () => ipcRenderer.invoke("templates:list"),
  today: () => ipcRenderer.invoke("core:today"),

  chooseFolder: () => ipcRenderer.invoke("dialog:folder"),
  chooseRollback: () => ipcRenderer.invoke("dialog:rollback"),

  previewStructure: (opts) => ipcRenderer.invoke("structure:preview", opts),
  applyStructure: (opts) => ipcRenderer.invoke("structure:apply", opts),

  previewRename: (opts) => ipcRenderer.invoke("rename:preview", opts),
  applyRename: (opts) => ipcRenderer.invoke("rename:apply", opts),
  rollback: (file) => ipcRenderer.invoke("rename:rollback", file)
});
