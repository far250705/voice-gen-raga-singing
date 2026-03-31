import tkinter as tk
from tkinter import ttk
import json
import os
import random
import threading
from gemini_gen import generate_notes_gemini, GeminiError

# ── Load JSON data ────────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

with open(os.path.join(BASE_DIR, "shruti.json"), "r", encoding="utf-8") as f:
    shruti_data = json.load(f)["shrutis"]

with open(os.path.join(BASE_DIR, "ragas.json"), "r", encoding="utf-8") as f:
    raga_data = json.load(f)["ragas"]

with open(os.path.join(BASE_DIR, "thala.json"), "r", encoding="utf-8") as f:
    thala_data = json.load(f)["thalas"]

shruti_map = {s["key"]: s for s in shruti_data}
raga_map   = {r["name"]: r for r in raga_data}
thala_map  = {t["name"]: t for t in thala_data}

# ── Frequency helper ──────────────────────────────────────────────────────────
def get_note_freq(base_hz: float, semitone_offset: int) -> float:
    return round(base_hz * (2 ** (semitone_offset / 12)), 2)

# ── Colors ────────────────────────────────────────────────────────────────────
BG          = "#0f0f14"
ACCENT      = "#c8973a"
ACCENT2     = "#7f5af0"
ACCENT3     = "#e05a6a"
TEXT        = "#e8e3d8"
SUBTEXT     = "#8a8070"
CARD_BG     = "#1c1c26"
BORDER      = "#2a2a38"
AROHA_CLR   = "#5eead4"
AVARO_CLR   = "#fb923c"
BEAT_COLORS = ["#5eead4", "#c8973a", "#7f5af0", "#fb923c", "#e05a6a"]

# ── Note generation ───────────────────────────────────────────────────────────
def generate_notes(raga: dict, thala: dict, avartanams: int = 4) -> list:
    notes_ordered = list(raga["notes"].items())
    solfege_list  = [info["solfege"] for _, info in notes_ordered]
    full_scale    = solfege_list + ["S'"]

    beats_per_cycle = thala["beats"]
    total_beats     = beats_per_cycle * avartanams
    result          = []
    current_idx     = 0

    for beat in range(total_beats):
        is_last_beat   = (beat == total_beats - 1)
        is_cycle_start = (beat % beats_per_cycle == 0)

        if is_last_beat:
            result.append("S")
            continue
        if is_cycle_start:
            result.append(full_scale[0])
            current_idx = 0
            continue

        move = random.choices([-2, -1, -1, 1, 1, 2], weights=[1, 3, 3, 3, 3, 1])[0]
        current_idx = max(0, min(len(full_scale) - 1, current_idx + move))

        beat_in_cycle = beat % beats_per_cycle
        if beat_in_cycle >= beats_per_cycle - 2:
            current_idx = max(0, current_idx - 1)

        result.append(full_scale[current_idx])

    return [result[i * beats_per_cycle:(i + 1) * beats_per_cycle]
            for i in range(avartanams)]


# ── App ───────────────────────────────────────────────────────────────────────
class RagaApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Raga Explorer")
        self.configure(bg=BG)
        self.resizable(True, False)

        self.fn_title = ("Georgia", 22, "bold")
        self.fn_label = ("Georgia", 11)
        self.fn_note  = ("Courier New", 13, "bold")
        self.fn_small = ("Courier New", 9)
        self.fn_badge = ("Georgia", 9, "bold")
        self.fn_beat  = ("Courier New", 8)

        self._build_ui()
        self.geometry("800x760")
        self._center()

    def _center(self):
        self.update_idletasks()
        w, h = self.winfo_width(), self.winfo_height()
        x = (self.winfo_screenwidth()  - w) // 2
        y = (self.winfo_screenheight() - h) // 2
        self.geometry(f"{w}x{h}+{x}+{y}")

    # ── UI ────────────────────────────────────────────────────────────────────
    def _build_ui(self):
        # header
        hdr = tk.Frame(self, bg=BG)
        hdr.pack(fill="x", padx=32, pady=(18, 0))
        tk.Label(hdr, text="ರಾಗ ದರ್ಶನ", font=("Georgia", 11),
                 bg=BG, fg=ACCENT).pack(anchor="w")
        tk.Label(hdr, text="Raga Explorer", font=self.fn_title,
                 bg=BG, fg=TEXT).pack(anchor="w")
        tk.Frame(hdr, bg=ACCENT, height=2).pack(fill="x", pady=(8, 0))

        # controls
        ctrl = tk.Frame(self, bg=BG)
        ctrl.pack(fill="x", padx=32, pady=(16, 0))

        self._lbl(ctrl, "SHRUTI").grid(row=0, column=0, sticky="w", padx=(0, 16))
        self._lbl(ctrl, "RAGA").grid(row=0, column=1, sticky="w", padx=(0, 16))
        self._lbl(ctrl, "THALA").grid(row=0, column=2, sticky="w")

        self.shruti_var = tk.StringVar(value="C")
        self._combo(ctrl, self.shruti_var,
                    [s["key"] for s in shruti_data], 8
                    ).grid(row=1, column=0, sticky="w", padx=(0, 16), pady=(4, 0))
        self.shruti_var.trace_add("write", lambda *_: self._refresh())

        self.raga_var = tk.StringVar(value=list(raga_map.keys())[0])
        self._combo(ctrl, self.raga_var,
                    list(raga_map.keys()), 20
                    ).grid(row=1, column=1, sticky="w", padx=(0, 16), pady=(4, 0))
        self.raga_var.trace_add("write", lambda *_: self._refresh())

        self.thala_var = tk.StringVar(value=list(thala_map.keys())[0])
        self._combo(ctrl, self.thala_var,
                    list(thala_map.keys()), 16
                    ).grid(row=1, column=2, sticky="w", pady=(4, 0))
        self.thala_var.trace_add("write", lambda *_: self._refresh())

        # info strip
        info = tk.Frame(self, bg=BG)
        info.pack(fill="x", padx=32, pady=(14, 0))
        self.melakarta_lbl = tk.Label(info, text="", font=self.fn_badge,
                                      bg=ACCENT2, fg="#fff")
        self.melakarta_lbl.pack(side="left", pady=3, padx=(0, 6))
        self.thala_lbl = tk.Label(info, text="", font=self.fn_badge,
                                  bg=ACCENT3, fg="#fff")
        self.thala_lbl.pack(side="left", pady=3, padx=(0, 6))
        self.base_freq_lbl = tk.Label(info, text="", font=self.fn_small,
                                      bg=BG, fg=SUBTEXT)
        self.base_freq_lbl.pack(side="left", padx=4)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=32, pady=12)

        # arohanam / avarohanam
        panels = tk.Frame(self, bg=BG)
        panels.pack(fill="x", padx=32)
        panels.columnconfigure(0, weight=1)
        panels.columnconfigure(1, weight=1)
        self.aro_frame   = self._panel(panels, "↑  AROHANAM",   AROHA_CLR, 0)
        self.avaro_frame = self._panel(panels, "↓  AVAROHANAM", AVARO_CLR, 1)

        tk.Frame(self, bg=BORDER, height=1).pack(fill="x", padx=32, pady=16)

        # composition header
        gen_hdr = tk.Frame(self, bg=BG)
        gen_hdr.pack(fill="x", padx=32)
        tk.Label(gen_hdr, text="GENERATED COMPOSITION  — 4 avartanams",
                 font=self.fn_small, bg=BG, fg=SUBTEXT).pack(side="left")
        tk.Button(gen_hdr, text="⟳  Regenerate",
                  font=self.fn_small, bg=CARD_BG, fg=ACCENT,
                  activebackground=BORDER, activeforeground=ACCENT,
                  relief="flat", cursor="hand2",
                  command=self._regenerate).pack(side="right")

        # status label (Gemini feedback)
        self.status_lbl = tk.Label(self, text="", font=self.fn_small, bg=BG, fg=ACCENT)
        self.status_lbl.pack(anchor="w", padx=32, pady=(4, 0))

        # composition area — centered
        self.comp_outer = tk.Frame(self, bg=BG)
        self.comp_outer.pack(fill="both", expand=True, pady=(12, 24))

        self.comp_frame = tk.Frame(self.comp_outer, bg=BG)
        self.comp_frame.pack(anchor="center")

        self._refresh()

    # ── widget helpers ────────────────────────────────────────────────────────
    def _lbl(self, parent, text):
        return tk.Label(parent, text=text, font=self.fn_small, bg=BG, fg=SUBTEXT)

    def _combo(self, parent, var, values, width):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Dark.TCombobox",
                    fieldbackground=CARD_BG, background=CARD_BG,
                    foreground=TEXT, selectbackground=CARD_BG,
                    selectforeground=ACCENT, bordercolor=BORDER,
                    arrowcolor=ACCENT, relief="flat")
        s.map("Dark.TCombobox",
              fieldbackground=[("readonly", CARD_BG)],
              foreground=[("readonly", TEXT)])
        return ttk.Combobox(parent, textvariable=var, values=values,
                            width=width, state="readonly",
                            style="Dark.TCombobox", font=self.fn_label)

    def _panel(self, parent, title, color, col):
        frame = tk.Frame(parent, bg=CARD_BG,
                         highlightbackground=color, highlightthickness=1)
        frame.grid(row=0, column=col, sticky="nsew",
                   padx=(0, 8) if col == 0 else (8, 0), pady=4)
        tk.Label(frame, text=title, font=self.fn_small,
                 bg=CARD_BG, fg=color, anchor="w").pack(fill="x", padx=12, pady=8)
        tk.Frame(frame, bg=color, height=1).pack(fill="x")
        inner = tk.Frame(frame, bg=CARD_BG)
        inner.pack(fill="both", expand=True, padx=12, pady=10)
        return inner

    # ── refresh ───────────────────────────────────────────────────────────────
    def _refresh(self):
        shruti = shruti_map.get(self.shruti_var.get())
        raga   = raga_map.get(self.raga_var.get())
        thala  = thala_map.get(self.thala_var.get())
        if not shruti or not raga or not thala:
            return

        base_hz = shruti["base_frequency_hz"]
        self.melakarta_lbl.config(text=f"Melakarta #{raga['melakarta_number']}")
        self.thala_lbl.config(text=f"{thala['name']}  {thala['beats']} beats")
        self.base_freq_lbl.config(text=f"Sa = {base_hz} Hz  ({shruti['name']})")

        self._render_scale(self.aro_frame,   raga["arohanam"],   raga["notes"], base_hz, AROHA_CLR)
        self._render_scale(self.avaro_frame, raga["avarohanam"], raga["notes"], base_hz, AVARO_CLR)
        self._render_composition(raga, thala)

    def _regenerate(self):
        raga  = raga_map.get(self.raga_var.get())
        thala = thala_map.get(self.thala_var.get())
        if not raga or not thala:
            return
        self._set_status("Asking Gemini for raga-specific notes...", ACCENT)
        threading.Thread(target=self._run_gemini, args=(raga, thala), daemon=True).start()

    def _run_gemini(self, raga, thala):
        try:
            avartanams = generate_notes_gemini(raga, thala, avartanams=4)
            self.after(0, lambda: self._set_status(
                f"Generated using Gemini ✓", AROHA_CLR))
            self.after(0, lambda: self._render_composition(raga, thala, avartanams=avartanams))
        except GeminiError as e:
            self.after(0, lambda: self._set_status(str(e), ACCENT3))

    def _set_status(self, msg, color):
        self.status_lbl.config(text=msg, fg=color)
        self.update_idletasks()

    # ── scale panels ─────────────────────────────────────────────────────────
    def _render_scale(self, frame, scale, notes_dict, base_hz, color):
        for w in frame.winfo_children():
            w.destroy()
        row_f = tk.Frame(frame, bg=CARD_BG)
        row_f.pack(fill="x")
        for note in scale:
            is_upper = note == "Sa'"
            key      = "Sa" if is_upper else note
            info     = notes_dict.get(key)
            offset   = 12 if is_upper else (info["semitone_offset"] if info else 0)
            freq     = get_note_freq(base_hz, offset)
            display  = "S'" if is_upper else (info["solfege"] if info else note)
            cell = tk.Frame(row_f, bg=CARD_BG)
            cell.pack(side="left", padx=3, pady=2)
            tk.Label(cell, text=display, font=self.fn_note,
                     bg=CARD_BG, fg=color).pack()
            tk.Label(cell, text=str(freq), font=self.fn_small,
                     bg=CARD_BG, fg=SUBTEXT).pack()

    # ── composition ───────────────────────────────────────────────────────────
    def _render_composition(self, raga: dict, thala: dict, avartanams=None):
        for w in self.comp_frame.winfo_children():
            w.destroy()

        if avartanams is None:
            avartanams = generate_notes(raga, thala, avartanams=4)
        subdivs    = thala["subdivisions"]
        beats      = thala["beats"]

        group_of_beat = {}
        idx = 0
        for g, size in enumerate(subdivs):
            for _ in range(size):
                group_of_beat[idx] = g
                idx += 1

        group_boundaries = set()
        idx = 0
        for size in subdivs:
            group_boundaries.add(idx)
            idx += size

        roman = ["I", "II", "III", "IV"]

        # ── fixed layout constants
        CELL_W   = 38
        PIPE_W   = 18
        PREFIX_W = 36
        ENDBAR_W = 24
        ROW_H    = 52
        BEAT_Y   = 16
        NUM_Y    = 36

        n_pipes = len([b for b in group_boundaries if b > 0])
        row_w   = PREFIX_W + beats * CELL_W + n_pipes * PIPE_W + ENDBAR_W + 8
        canvas_h = len(avartanams) * ROW_H + 36

        cv = tk.Canvas(self.comp_frame, bg=BG,
                       width=row_w, height=canvas_h,
                       highlightthickness=0, bd=0)
        cv.pack(anchor="center")

        note_font  = ("Courier New", 13, "bold")
        beat_font  = ("Courier New", 8)
        roman_font = ("Courier New", 9)

        for av_idx, cycle in enumerate(avartanams):
            y_base = av_idx * ROW_H

            cv.create_text(PREFIX_W - 6, y_base + BEAT_Y,
                           text=roman[av_idx], font=roman_font,
                           fill=SUBTEXT, anchor="e")

            x = PREFIX_W
            for beat_idx, note in enumerate(cycle):
                group = group_of_beat.get(beat_idx, 0)
                color = BEAT_COLORS[group % len(BEAT_COLORS)]

                if beat_idx in group_boundaries and beat_idx > 0:
                    cv.create_text(x + PIPE_W // 2, y_base + BEAT_Y,
                                   text="|", font=note_font,
                                   fill=SUBTEXT, anchor="center")
                    x += PIPE_W

                cx = x + CELL_W // 2
                cv.create_text(cx, y_base + BEAT_Y,
                               text=note, font=note_font,
                               fill=color, anchor="center")
                cv.create_text(cx, y_base + NUM_Y,
                               text=str(beat_idx + 1), font=beat_font,
                               fill=BORDER, anchor="center")
                x += CELL_W

            cv.create_text(x + 6, y_base + BEAT_Y,
                           text="‖", font=note_font,
                           fill=ACCENT, anchor="w")

        # legend
        leg_y = len(avartanams) * ROW_H + 14
        lx = 4
        cv.create_text(lx, leg_y, text="Groups: ", font=beat_font,
                       fill=SUBTEXT, anchor="w")
        lx += 52
        for g, (name, size) in enumerate(zip(thala["subdivision_names"], subdivs)):
            color = BEAT_COLORS[g % len(BEAT_COLORS)]
            label = f"{name} ({size})   "
            cv.create_text(lx, leg_y, text=label, font=beat_font,
                           fill=color, anchor="w")
            lx += len(label) * 6


# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = RagaApp()
    app.mainloop()