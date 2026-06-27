#!/usr/bin/env python3
"""
Replace Audio — Argonautas Lab
Substitui o áudio de um vídeo MOV/MP4 por um novo arquivo de áudio.
Codec de vídeo preservado · áudio copiado ou convertido conforme o container.

Requisitos:
  - Python 3.8+  (já vem no macOS)
  - ffmpeg instalado:  brew install ffmpeg
"""

import subprocess
import shutil
import sys
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading
import shlex


# ─── verificação de ffmpeg ────────────────────────────────────────────────────

def find_ffmpeg():
    for path in ("/usr/local/bin/ffmpeg", "/opt/homebrew/bin/ffmpeg"):
        if os.path.isfile(path):
            return path
    return shutil.which("ffmpeg")


# ─── lógica de processamento ──────────────────────────────────────────────────

def build_output_path(video_path):
    path = Path(video_path)
    return str(path.with_name(path.stem + "_new_audio" + path.suffix))


def audio_codec_args(audio_path, output_path):
    audio_ext = Path(audio_path).suffix.lower()
    output_ext = Path(output_path).suffix.lower()

    if output_ext in {".mp4", ".m4v"}:
        return ["-c:a", "aac", "-b:a", "320k"]

    if output_ext == ".mov" and audio_ext in {
            ".wav", ".aif", ".aiff", ".aac", ".m4a", ".mp3"}:
        return ["-c:a", "copy"]

    return ["-c:a", "aac", "-b:a", "320k"]


def run_replace(ffmpeg, video, audio, output, log_callback, done_callback, proc_callback):
    def worker():
        cmd = [
            ffmpeg, "-y",
            "-i", video,
            "-i", audio,
            "-ignore_unknown",
            "-map", "0",
            "-map", "-0:a",
            "-map", "1:a",
            "-map_metadata", "0",
            "-map_chapters", "0",
            "-c:v", "copy",
            "-c:s", "copy",
            "-c:d", "copy",
            *audio_codec_args(audio, output),
            output,
        ]
        log_callback("Comando:\n  " + " ".join(shlex.quote(part) for part in cmd) + "\n\n")
        try:
            proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            proc_callback(proc)
            if proc.stdout:
                for line in proc.stdout:
                    log_callback(line)
            proc.wait()
            if proc.returncode == 0:
                done_callback(True, "Arquivo salvo em:\n" + output)
            elif proc.returncode < 0:
                done_callback(False, "Processamento cancelado.")
            else:
                done_callback(False, "FFmpeg retornou erro. Veja o log acima.")
        except Exception as exc:
            done_callback(False, "Erro ao rodar FFmpeg:\n" + str(exc))
        finally:
            proc_callback(None)

    threading.Thread(target=worker, daemon=True).start()


# ─── interface ────────────────────────────────────────────────────────────────

BG      = "#1a1a1a"
FG      = "#e8e8e8"
ACCENT  = "#f0a500"
FLD_BG  = "#2a2a2a"
PAD     = {"padx": 16, "pady": 6}


class App(tk.Tk):
    def __init__(self, ffmpeg_path):
        super().__init__()
        self.ffmpeg = ffmpeg_path
        self.proc = None
        self.is_closing = False
        self.title("Replace Audio · Argo Lab")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.protocol("WM_DELETE_WINDOW", self._close)
        self._build_ui()
        self._center()

    def _lbl(self, text, color=FG, size=11, bold=False, **kwargs):
        font = ("Helvetica", size, "bold") if bold else ("Helvetica", size)
        return tk.Label(self, text=text, bg=BG, fg=color, font=font, **kwargs)

    def _btn(self, text, cmd, size=12):
        return tk.Button(
            self, text=text, command=cmd,
            bg=ACCENT, fg="#000", relief="flat",
            font=("Helvetica", size, "bold"),
            cursor="hand2", padx=10, pady=4)

    def _build_ui(self):
        self._lbl("Replace Audio", ACCENT, 18, bold=True).grid(
            row=0, column=0, columnspan=3, pady=(20, 4))
        self._lbl("Substitui o áudio de um vídeo MOV/MP4", "#888").grid(
            row=1, column=0, columnspan=3, pady=(0, 16))

        self.var_video  = tk.StringVar()
        self.var_audio  = tk.StringVar()
        self.var_output = tk.StringVar()

        rows = [
            (2, "Vídeo:",  self.var_video,  self._pick_video),
            (3, "Áudio:",  self.var_audio,  self._pick_audio),
            (4, "Saída:",  self.var_output, self._pick_output),
        ]
        for row, label, var, cmd in rows:
            self._lbl(label, width=8, anchor="e").grid(row=row, column=0, **PAD)
            tk.Entry(
                self, textvariable=var, width=52,
                bg=FLD_BG, fg=FG, insertbackground=FG,
                relief="flat", font=("Helvetica", 11)
            ).grid(row=row, column=1, **PAD)
            self._btn("…", cmd).grid(row=row, column=2, padx=(0, 16))

        self.btn_run = tk.Button(
            self, text="▶  Processar", command=self._run,
            bg=ACCENT, fg="#000", relief="flat",
            font=("Helvetica", 13, "bold"),
            cursor="hand2", padx=20, pady=8)
        self.btn_run.grid(row=5, column=0, columnspan=3, pady=(12, 8))

        self.progress = ttk.Progressbar(self, mode="indeterminate", length=460)
        self.progress.grid(row=6, column=0, columnspan=3, padx=16, pady=(0, 8))

        self._lbl("Log FFmpeg", "#666").grid(
            row=7, column=0, columnspan=3, sticky="w", padx=16)

        frame_log = tk.Frame(self, bg=BG)
        frame_log.grid(row=8, column=0, columnspan=3, padx=16, pady=(0, 20), sticky="nsew")

        self.log = tk.Text(
            frame_log, width=72, height=14,
            bg="#111", fg="#7cfc00",
            font=("Menlo", 10), relief="flat",
            state="disabled", wrap="word")
        scroll = tk.Scrollbar(frame_log, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    # ── seletores ─────────────────────────────────────────────────────────────

    def _pick_video(self):
        path = filedialog.askopenfilename(
            title="Selecionar vídeo",
            filetypes=[("Vídeo", "*.mov *.mp4 *.m4v"), ("Todos", "*.*")])
        if path:
            self.var_video.set(path)
            self.var_output.set(build_output_path(path))

    def _pick_audio(self):
        path = filedialog.askopenfilename(
            title="Selecionar áudio",
            filetypes=[("Áudio", "*.wav *.aif *.aiff *.mp3 *.aac *.m4a *.flac"),
                       ("Todos", "*.*")])
        if path:
            self.var_audio.set(path)

    def _pick_output(self):
        video = self.var_video.get()
        ext = Path(video).suffix if video else ".mp4"
        path = filedialog.asksaveasfilename(
            title="Salvar como",
            defaultextension=ext,
            filetypes=[("Mesmo formato", "*" + ext), ("Todos", "*.*")])
        if path:
            self.var_output.set(path)

    # ── execução ──────────────────────────────────────────────────────────────

    def _run(self):
        video  = self.var_video.get().strip()
        audio  = self.var_audio.get().strip()
        output = self.var_output.get().strip()

        if not video or not os.path.isfile(video):
            messagebox.showerror("Erro", "Selecione um arquivo de vídeo válido.")
            return
        if not audio or not os.path.isfile(audio):
            messagebox.showerror("Erro", "Selecione um arquivo de áudio válido.")
            return
        if not output:
            messagebox.showerror("Erro", "Defina o arquivo de saída.")
            return
        if os.path.abspath(output) == os.path.abspath(video):
            messagebox.showerror(
                "Erro", "O arquivo de saída não pode ser o mesmo vídeo de entrada.")
            return
        output_parent = os.path.dirname(os.path.abspath(output))
        if output_parent and not os.path.isdir(output_parent):
            messagebox.showerror("Erro", "A pasta de saída não existe.")
            return

        self._log_clear()
        self.btn_run.config(state="disabled")
        self.progress.start(12)

        run_replace(self.ffmpeg, video, audio, output,
                    self._log_append, self._on_done, self._set_proc)

    def _set_proc(self, proc):
        self.proc = proc

    def _close(self):
        self.is_closing = True
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass
        self.destroy()

    def _on_done(self, success, msg):
        if self.is_closing:
            return
        self.after(0, self._on_done_main, success, msg)

    def _on_done_main(self, success, msg):
        if self.is_closing:
            return
        self.progress.stop()
        self.btn_run.config(state="normal")
        if success:
            messagebox.showinfo("Concluído", msg)
        else:
            messagebox.showerror("Erro", msg)

    def _log_append(self, text):
        if self.is_closing:
            return
        self.after(0, self._log_append_main, text)

    def _log_append_main(self, text):
        if self.is_closing:
            return
        self.log.config(state="normal")
        self.log.insert("end", text)
        self.log.see("end")
        self.log.config(state="disabled")

    def _log_clear(self):
        self.log.config(state="normal")
        self.log.delete("1.0", "end")
        self.log.config(state="disabled")

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        sw, sh = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f"+{(sw - w) // 2}+{(sh - h) // 2}")


# ─── main ─────────────────────────────────────────────────────────────────────

def main():
    ffmpeg = find_ffmpeg()
    if not ffmpeg:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "FFmpeg não encontrado",
            "FFmpeg não está instalado.\n\n"
            "Instale com:\n  brew install ffmpeg\n\n"
            "Homebrew: https://brew.sh")
        sys.exit(1)

    App(ffmpeg).mainloop()


if __name__ == "__main__":
    main()
