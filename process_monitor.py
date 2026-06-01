"""
██████╗ ██████╗  ██████╗  ██████╗███████╗███████╗███████╗
██╔══██╗██╔══██╗██╔═══██╗██╔════╝██╔════╝██╔════╝██╔════╝
██████╔╝██████╔╝██║   ██║██║     █████╗  ███████╗███████╗
██╔═══╝ ██╔══██╗██║   ██║██║     ██╔══╝  ╚════██║╚════██║
██║     ██║  ██║╚██████╔╝╚██████╗███████╗███████║███████║
╚═╝     ╚═╝  ╚═╝ ╚═════╝  ╚═════╝╚══════╝╚══════╝╚══════╝
          MONITOR  —  Windows Process Manager
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import psutil
import threading
import time
import os
import sys

# ── Colour palette ──────────────────────────────────────────────────
BG         = "#0d0f14"
PANEL      = "#13161e"
CARD       = "#1a1e2a"
BORDER     = "#252a38"
ACCENT     = "#00e5ff"
ACCENT2    = "#7c3aed"
DANGER     = "#ff4757"
WARN       = "#ffa502"
SUCCESS    = "#2ed573"
TEXT       = "#e2e8f0"
TEXT_DIM   = "#64748b"
TEXT_MID   = "#94a3b8"
HEADER_BG  = "#0f1219"

# ── Column definitions ───────────────────────────────────────────────
COLUMNS = [
    ("PID",      60,  "center"),
    ("Процесс",  220, "w"),
    ("CPU %",    70,  "center"),
    ("RAM (MB)", 90,  "center"),
    ("Статус",   90,  "center"),
    ("Пользователь", 130, "w"),
    ("Потоки",   70,  "center"),
]

REFRESH_MS = 2000  # refresh every 2 s

# ────────────────────────────────────────────────────────────────────
class ProcessMonitor(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("PROCESS MONITOR")
        self.geometry("1100x720")
        self.minsize(900, 580)
        self.configure(bg=BG)
        self._running   = True
        self._sort_col  = "CPU %"
        self._sort_rev  = True
        self._filter    = ""
        self._proc_data = []
        self._selected_pid = None

        self._setup_fonts()
        self._build_ui()
        self._start_refresh()

    # ── Fonts ────────────────────────────────────────────────────────
    def _setup_fonts(self):
        self.fnt_mono  = font.Font(family="Consolas",    size=10)
        self.fnt_title = font.Font(family="Consolas",    size=16, weight="bold")
        self.fnt_label = font.Font(family="Segoe UI",    size=9)
        self.fnt_btn   = font.Font(family="Segoe UI",    size=9,  weight="bold")
        self.fnt_stat  = font.Font(family="Consolas",    size=14, weight="bold")
        self.fnt_head  = font.Font(family="Segoe UI",    size=8,  weight="bold")

    # ── Build full UI ────────────────────────────────────────────────
    def _build_ui(self):
        self._build_header()
        self._build_stats_bar()
        self._build_toolbar()
        self._build_table()
        self._build_footer()

    # ── Header ───────────────────────────────────────────────────────
    def _build_header(self):
        hdr = tk.Frame(self, bg=HEADER_BG, height=56)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        # left accent line
        tk.Frame(hdr, bg=ACCENT, width=4).pack(side="left", fill="y")

        # title
        tk.Label(hdr, text="⬡ PROCESS", font=self.fnt_title,
                 fg=ACCENT, bg=HEADER_BG).pack(side="left", padx=(14, 4), pady=10)
        tk.Label(hdr, text="MONITOR", font=self.fnt_title,
                 fg=TEXT, bg=HEADER_BG).pack(side="left", pady=10)

        # live indicator
        self._dot_lbl = tk.Label(hdr, text="● LIVE", font=self.fnt_btn,
                                 fg=SUCCESS, bg=HEADER_BG)
        self._dot_lbl.pack(side="left", padx=18)

        # host info
        info = f"{os.environ.get('COMPUTERNAME','PC')}  ·  {os.cpu_count()} CPU"
        tk.Label(hdr, text=info, font=self.fnt_label,
                 fg=TEXT_DIM, bg=HEADER_BG).pack(side="right", padx=20)

    # ── Stats bar ────────────────────────────────────────────────────
    def _build_stats_bar(self):
        bar = tk.Frame(self, bg=PANEL, height=64)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        self._stat_widgets = {}
        defs = [
            ("cpu_lbl",  "CPU", "%"),
            ("mem_lbl",  "RAM", "%"),
            ("proc_lbl", "ПРОЦЕССЫ", ""),
            ("thr_lbl",  "ПОТОКИ", ""),
        ]
        for key, label, unit in defs:
            cell = tk.Frame(bar, bg=PANEL)
            cell.pack(side="left", padx=28, pady=8)
            tk.Label(cell, text=label, font=self.fnt_head,
                     fg=TEXT_DIM, bg=PANEL).pack(anchor="w")
            val_frm = tk.Frame(cell, bg=PANEL)
            val_frm.pack(anchor="w")
            lbl = tk.Label(val_frm, text="—", font=self.fnt_stat,
                           fg=ACCENT, bg=PANEL)
            lbl.pack(side="left")
            if unit:
                tk.Label(val_frm, text=unit, font=self.fnt_label,
                         fg=TEXT_DIM, bg=PANEL).pack(side="left", padx=(2,0))
            self._stat_widgets[key] = lbl

        # separator
        tk.Frame(bar, bg=BORDER, width=1).pack(side="left", fill="y", pady=10)

        # kill button
        kill_frm = tk.Frame(bar, bg=PANEL)
        kill_frm.pack(side="right", padx=20)
        self._kill_btn = self._icon_btn(
            kill_frm, "⛔  ЗАВЕРШИТЬ ПРОЦЕСС",
            DANGER, self._kill_selected, disabled=True)
        self._kill_btn.pack()

        self._sus_btn = self._icon_btn(
            kill_frm, "⏸  ПРИОСТАНОВИТЬ",
            WARN, self._suspend_selected, disabled=True)
        self._sus_btn.pack(pady=(6,0))

    def _icon_btn(self, parent, text, color, cmd, disabled=False):
        state = "disabled" if disabled else "normal"
        btn = tk.Button(parent, text=text, font=self.fnt_btn,
                        fg="white", bg=color,
                        activebackground=color, activeforeground="white",
                        relief="flat", bd=0, padx=12, pady=5,
                        cursor="hand2", command=cmd, state=state)
        return btn

    # ── Toolbar ──────────────────────────────────────────────────────
    def _build_toolbar(self):
        bar = tk.Frame(self, bg=CARD, pady=8, padx=14)
        bar.pack(fill="x")

        # search
        tk.Label(bar, text="🔍", font=self.fnt_label,
                 fg=TEXT_DIM, bg=CARD).pack(side="left")
        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", self._on_filter)
        entry = tk.Entry(bar, textvariable=self._search_var,
                         font=self.fnt_mono, bg=BORDER, fg=TEXT,
                         insertbackground=ACCENT, relief="flat",
                         bd=0, width=28)
        entry.pack(side="left", padx=6, ipady=4)
        tk.Label(bar, text="Поиск процесса...", font=self.fnt_label,
                 fg=TEXT_DIM, bg=CARD).pack(side="left")

        # sort buttons
        tk.Frame(bar, bg=BORDER, width=1).pack(side="left", fill="y",
                                                padx=12, pady=2)
        tk.Label(bar, text="Сортировка:", font=self.fnt_label,
                 fg=TEXT_MID, bg=CARD).pack(side="left")
        for col in ("CPU %", "RAM (MB)", "PID", "Процесс"):
            b = tk.Button(bar, text=col, font=self.fnt_label,
                          fg=TEXT_MID, bg=CARD, activebackground=BORDER,
                          activeforeground=ACCENT, relief="flat", bd=0,
                          padx=8, pady=2, cursor="hand2",
                          command=lambda c=col: self._set_sort(c))
            b.pack(side="left", padx=2)

        # refresh toggle
        self._auto_var = tk.BooleanVar(value=True)
        tk.Checkbutton(bar, text="Авто-обновление", variable=self._auto_var,
                       font=self.fnt_label, fg=TEXT_MID, bg=CARD,
                       selectcolor=CARD, activebackground=CARD,
                       activeforeground=ACCENT,
                       relief="flat", bd=0).pack(side="right")

    # ── Table ────────────────────────────────────────────────────────
    def _build_table(self):
        wrapper = tk.Frame(self, bg=BG)
        wrapper.pack(fill="both", expand=True, padx=10, pady=(0,6))

        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("P.Treeview",
                        background=CARD,
                        foreground=TEXT,
                        fieldbackground=CARD,
                        font=("Consolas", 9),
                        rowheight=26,
                        borderwidth=0)
        style.configure("P.Treeview.Heading",
                        background=PANEL,
                        foreground=ACCENT,
                        font=("Segoe UI", 8, "bold"),
                        relief="flat",
                        borderwidth=0)
        style.map("P.Treeview",
                  background=[("selected", ACCENT2)],
                  foreground=[("selected", "white")])
        style.map("P.Treeview.Heading",
                  background=[("active", BORDER)])

        cols = [c[0] for c in COLUMNS]
        self._tree = ttk.Treeview(wrapper, columns=cols, show="headings",
                                   style="P.Treeview", selectmode="browse")

        for name, width, anchor in COLUMNS:
            self._tree.heading(name, text=name,
                               command=lambda c=name: self._set_sort(c))
            self._tree.column(name, width=width, anchor=anchor, minwidth=40)

        # tag colours
        self._tree.tag_configure("high_cpu",  foreground=DANGER)
        self._tree.tag_configure("med_cpu",   foreground=WARN)
        self._tree.tag_configure("ok",        foreground=TEXT)
        self._tree.tag_configure("running",   foreground=SUCCESS)
        self._tree.tag_configure("sleeping",  foreground=TEXT_DIM)
        self._tree.tag_configure("stripe",    background="#161925")

        # scrollbars
        vsb = ttk.Scrollbar(wrapper, orient="vertical",
                            command=self._tree.yview)
        self._tree.configure(yscrollcommand=vsb.set)
        self._tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        self._tree.bind("<<TreeviewSelect>>", self._on_select)
        self._tree.bind("<Double-1>",         self._on_double_click)

    # ── Footer ───────────────────────────────────────────────────────
    def _build_footer(self):
        foot = tk.Frame(self, bg=HEADER_BG, height=26)
        foot.pack(fill="x", side="bottom")
        foot.pack_propagate(False)

        self._status_lbl = tk.Label(foot, text="Загрузка...",
                                    font=self.fnt_label,
                                    fg=TEXT_DIM, bg=HEADER_BG)
        self._status_lbl.pack(side="left", padx=12)

        tk.Label(foot, text="DoubleClick → детали  ·  Del → завершить",
                 font=self.fnt_label, fg=TEXT_DIM,
                 bg=HEADER_BG).pack(side="right", padx=12)

        self.bind("<Delete>", lambda _: self._kill_selected())

    # ── Refresh loop ─────────────────────────────────────────────────
    def _start_refresh(self):
        self._refresh()

    def _refresh(self):
        if not self._running:
            return
        if self._auto_var.get():
            threading.Thread(target=self._fetch_procs, daemon=True).start()
        self.after(REFRESH_MS, self._refresh)

    def _fetch_procs(self):
        procs = []
        attrs = ["pid","name","cpu_percent","memory_info",
                 "status","username","num_threads"]
        for p in psutil.process_iter(attrs=attrs):
            try:
                i = p.info
                ram = round(i["memory_info"].rss / 1024 / 1024, 1) \
                      if i.get("memory_info") else 0
                procs.append({
                    "pid":     i["pid"],
                    "name":    i["name"] or "—",
                    "cpu":     i["cpu_percent"] or 0.0,
                    "ram":     ram,
                    "status":  i["status"] or "—",
                    "user":    (i["username"] or "").split("\\")[-1],
                    "threads": i["num_threads"] or 0,
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

        self._proc_data = procs
        self.after(0, self._update_ui)

    def _update_ui(self):
        # stats
        cpu  = psutil.cpu_percent()
        mem  = psutil.virtual_memory().percent
        filt = self._filter.lower()

        visible = [p for p in self._proc_data
                   if filt in p["name"].lower() or filt in str(p["pid"])]

        # sort
        key_map = {"CPU %":"cpu","RAM (MB)":"ram","PID":"pid",
                   "Процесс":"name","Потоки":"threads","Статус":"status"}
        sk = key_map.get(self._sort_col, "cpu")
        visible.sort(key=lambda p: p[sk], reverse=self._sort_rev)

        # remember selection
        sel_pid = self._selected_pid

        # repopulate tree
        self._tree.delete(*self._tree.get_children())
        for i, p in enumerate(visible):
            cpu_tag = ("high_cpu" if p["cpu"] > 50
                       else "med_cpu" if p["cpu"] > 15
                       else "ok")
            status_tag = ("running"  if p["status"] == "running"
                          else "sleeping")
            tags = [cpu_tag, status_tag]
            if i % 2 == 0:
                tags.append("stripe")

            iid = self._tree.insert("", "end", iid=str(p["pid"]),
                values=(p["pid"], p["name"],
                        f"{p['cpu']:.1f}", f"{p['ram']:.1f}",
                        p["status"], p["user"], p["threads"]),
                tags=tags)

        # restore selection
        if sel_pid and self._tree.exists(str(sel_pid)):
            self._tree.selection_set(str(sel_pid))
            self._tree.see(str(sel_pid))

        # update stats
        self._stat_widgets["cpu_lbl"].config(
            text=f"{cpu:.0f}",
            fg=DANGER if cpu > 80 else WARN if cpu > 50 else ACCENT)
        self._stat_widgets["mem_lbl"].config(
            text=f"{mem:.0f}",
            fg=DANGER if mem > 85 else WARN if mem > 65 else ACCENT)
        self._stat_widgets["proc_lbl"].config(text=str(len(visible)))
        total_thr = sum(p["threads"] for p in visible)
        self._stat_widgets["thr_lbl"].config(text=str(total_thr))

        self._status_lbl.config(
            text=f"Показано {len(visible)} из {len(self._proc_data)} процессов  ·  "
                 f"Обновлено: {time.strftime('%H:%M:%S')}")

        # blink dot
        self._dot_lbl.config(fg=SUCCESS if int(time.time()) % 2 == 0 else TEXT_DIM)

    # ── Events ───────────────────────────────────────────────────────
    def _on_select(self, _=None):
        sel = self._tree.selection()
        if sel:
            self._selected_pid = int(sel[0])
            self._kill_btn.config(state="normal")
            self._sus_btn.config(state="normal")
        else:
            self._selected_pid = None
            self._kill_btn.config(state="disabled")
            self._sus_btn.config(state="disabled")

    def _on_double_click(self, event):
        item = self._tree.identify_row(event.y)
        if not item:
            return
        pid = int(item)
        try:
            p = psutil.Process(pid)
            with p.oneshot():
                info = (
                    f"PID:        {pid}\n"
                    f"Имя:        {p.name()}\n"
                    f"Статус:     {p.status()}\n"
                    f"CPU %:      {p.cpu_percent(interval=0.1):.2f}\n"
                    f"RAM MB:     {p.memory_info().rss/1024/1024:.2f}\n"
                    f"Потоки:     {p.num_threads()}\n"
                    f"Создан:     {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(p.create_time()))}\n"
                    f"Исп-ль:     {p.username()}\n"
                    f"Путь:       {p.exe() if p.exe() else '—'}\n"
                )
            self._detail_window(pid, p.name(), info)
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            messagebox.showwarning("Нет доступа", str(e))

    def _detail_window(self, pid, name, info):
        win = tk.Toplevel(self)
        win.title(f"Детали — {name} [{pid}]")
        win.configure(bg=BG)
        win.geometry("460x340")
        win.resizable(False, False)

        tk.Frame(win, bg=ACCENT, height=3).pack(fill="x")
        tk.Label(win, text=f"⬡ {name}", font=self.fnt_title,
                 fg=ACCENT, bg=BG).pack(padx=20, pady=(14,4), anchor="w")
        tk.Label(win, text=f"PID {pid}", font=self.fnt_label,
                 fg=TEXT_DIM, bg=BG).pack(padx=20, anchor="w")

        box = tk.Text(win, font=self.fnt_mono, bg=CARD, fg=TEXT,
                      relief="flat", bd=0, padx=14, pady=10,
                      state="normal", height=10)
        box.pack(fill="both", expand=True, padx=14, pady=10)
        box.insert("1.0", info)
        box.config(state="disabled")

        tk.Button(win, text="Закрыть", font=self.fnt_btn,
                  fg="white", bg=ACCENT2, relief="flat", bd=0,
                  padx=16, pady=6, cursor="hand2",
                  command=win.destroy).pack(pady=(0,14))

    def _on_filter(self, *_):
        self._filter = self._search_var.get()
        self._update_ui()

    def _set_sort(self, col):
        if self._sort_col == col:
            self._sort_rev = not self._sort_rev
        else:
            self._sort_col = col
            self._sort_rev = True
        self._update_ui()

    # ── Actions ──────────────────────────────────────────────────────
    def _kill_selected(self):
        pid = self._selected_pid
        if pid is None:
            return
        name = self._proc_name(pid)
        if not messagebox.askyesno(
                "Подтверждение",
                f"Завершить процесс?\n\n{name}  [PID {pid}]",
                icon="warning"):
            return
        try:
            psutil.Process(pid).kill()
            self._status_lbl.config(text=f"✓ Процесс {name} [{pid}] завершён")
            self._selected_pid = None
        except psutil.AccessDenied:
            messagebox.showerror("Отказано в доступе",
                                 "Запустите программу от имени администратора.")
        except psutil.NoSuchProcess:
            self._status_lbl.config(text=f"Процесс {pid} уже завершён")

    def _suspend_selected(self):
        pid = self._selected_pid
        if pid is None:
            return
        name = self._proc_name(pid)
        try:
            p = psutil.Process(pid)
            if p.status() == psutil.STATUS_STOPPED:
                p.resume()
                self._status_lbl.config(text=f"▶ Процесс {name} [{pid}] возобновлён")
            else:
                p.suspend()
                self._status_lbl.config(text=f"⏸ Процесс {name} [{pid}] приостановлен")
        except psutil.AccessDenied:
            messagebox.showerror("Отказано в доступе",
                                 "Запустите программу от имени администратора.")
        except psutil.NoSuchProcess:
            pass

    def _proc_name(self, pid):
        try:
            return psutil.Process(pid).name()
        except Exception:
            return str(pid)

    # ── Cleanup ──────────────────────────────────────────────────────
    def destroy(self):
        self._running = False
        super().destroy()


# ── Entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    # On Windows ask for DPI awareness for sharp rendering
    try:
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass

    app = ProcessMonitor()
    app.mainloop()
