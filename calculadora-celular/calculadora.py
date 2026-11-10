"""Calculadora com visual do Windows 11 e porcentagem estilo celular (Tkinter).

Execute com:  python calculadora.py
"""

from __future__ import annotations

import os
import sys
import tkinter as tk
import tkinter.font as tkfont
from decimal import Decimal

from calc_engine import (DIVIDE, MINUS, PLUS, TIMES, Calculator, display,
                         format_number)

APP_ID = "G3.CalculadoraCelular"


# --------------------------------------------------------------------------
# Tema (claro/escuro, segue a configuração do Windows)
# --------------------------------------------------------------------------

LIGHT = {
    "bg": "#F3F3F3", "panel": "#F3F3F3", "text": "#1A1A1A", "dim": "#5F5F5F",
    "num": "#FFFFFF", "num_hover": "#F9F9F9", "num_press": "#F0F0F0",
    "fn": "#F9F9F9", "fn_hover": "#F3F3F3", "fn_press": "#EDEDED",
    "border": "#E5E5E5", "accent": "#005FB8", "accent_hover": "#1A6FC0",
    "accent_press": "#3381CA", "accent_text": "#FFFFFF", "disabled": "#A0A0A0",
    "tab_line": "#005FB8", "hist_hover": "#EAEAEA",
}
DARK = {
    "bg": "#202020", "panel": "#202020", "text": "#FFFFFF", "dim": "#C5C5C5",
    "num": "#3B3B3B", "num_hover": "#323232", "num_press": "#2B2B2B",
    "fn": "#323232", "fn_hover": "#3B3B3B", "fn_press": "#2B2B2B",
    "border": "#2E2E2E", "accent": "#4CC2FF", "accent_hover": "#48B1E8",
    "accent_press": "#42A1D2", "accent_text": "#000000", "disabled": "#6E6E6E",
    "tab_line": "#4CC2FF", "hist_hover": "#2D2D2D",
}


def windows_uses_dark_mode() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize")
        value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
        return value == 0
    except Exception:
        return False


T = DARK if (windows_uses_dark_mode() or os.environ.get("CALC_THEME") == "dark") else LIGHT


def resource_path(name: str) -> str:
    """Acha arquivos tanto rodando o .py quanto dentro do .exe (PyInstaller)."""
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, name)


def pick_font(*names: str) -> str:
    available = set(tkfont.families())
    for n in names:
        if n in available:
            return n
    return "Segoe UI"


# --------------------------------------------------------------------------
# Botão retangular com cantos arredondados (estilo Fluent)
# --------------------------------------------------------------------------

def round_rect(canvas, x0, y0, x1, y1, r, **kw):
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
           x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return canvas.create_polygon(pts, smooth=True, **kw)


class FluentButton(tk.Canvas):
    def __init__(self, master, text, command, kind="num", font=None):
        super().__init__(master, bg=T["bg"], highlightthickness=0, bd=0)
        self.text = text
        self.command = command
        self.kind = kind
        self.font = font
        self.state = "normal"  # normal | hover | press
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Enter>", lambda e: self._set("hover"))
        self.bind("<Leave>", lambda e: self._set("normal"))
        self.bind("<ButtonPress-1>", lambda e: self._set("press"))
        self.bind("<ButtonRelease-1>", self._release)

    def _set(self, state):
        self.state = state
        self.redraw()

    def _release(self, event):
        inside = 0 <= event.x <= self.winfo_width() and 0 <= event.y <= self.winfo_height()
        was = self.state == "press"
        self._set("hover" if inside else "normal")
        if was and inside:
            self.command()

    def flash(self):
        self._set("press")
        self.after(100, lambda: self._set("normal"))

    def colors(self):
        suffix = {"normal": "", "hover": "_hover", "press": "_press"}[self.state]
        if self.kind == "accent":
            return T["accent" + suffix], T["accent_text"], T["accent" + suffix]
        fg = T["text"] if self.state != "press" else T["dim"]
        return T[self.kind + suffix], fg, T["border"]

    def redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 6 or h < 6:
            return
        fill, fg, border = self.colors()
        round_rect(self, 1, 1, w - 2, h - 2, 6, fill=fill, outline=border)
        self.create_text(w / 2, h / 2, text=self.text, fill=fg, font=self.font)


class FlatButton(tk.Label):
    """Botões de texto simples (MC, MR, M+...)."""

    def __init__(self, master, text, command, font):
        super().__init__(master, text=text, bg=T["bg"], fg=T["text"], font=font,
                         padx=6, pady=6, cursor="hand2")
        self.command = command
        self.enabled = True
        self.bind("<Enter>", lambda e: self.enabled and self.configure(bg=T["hist_hover"]))
        self.bind("<Leave>", lambda e: self.configure(bg=T["bg"]))
        self.bind("<Button-1>", lambda e: self.enabled and self.command())

    def set_enabled(self, enabled: bool):
        self.enabled = enabled
        self.configure(fg=T["text"] if enabled else T["disabled"],
                       cursor="hand2" if enabled else "arrow")


# --------------------------------------------------------------------------
# Aplicativo
# --------------------------------------------------------------------------

class App:
    SIDE_PANEL_MIN_WIDTH = 620

    def __init__(self, root: tk.Tk):
        self.root = root
        self.calc = Calculator()
        self.error_text = ""
        self.memory: list[Decimal] = []
        self.last_expr = ""  # conta mostrada em cima depois do "="
        self.side_tab = "hist"

        ui = pick_font("Segoe UI Variable Text", "Segoe UI")
        disp = pick_font("Segoe UI Variable Display", "Segoe UI")
        self.f_title = tkfont.Font(family=disp, size=-20, weight="bold")
        self.f_big_family = disp
        self.f_big = tkfont.Font(family=disp, size=-48, weight="bold")
        self.f_expr = tkfont.Font(family=ui, size=-15)
        self.f_key = tkfont.Font(family=ui, size=-17)
        self.f_key_num = tkfont.Font(family=ui, size=-19, weight="bold")
        self.f_key_op = tkfont.Font(family=ui, size=-24)
        self.f_small = tkfont.Font(family=ui, size=-13)
        self.f_tab = tkfont.Font(family=ui, size=-15)
        self.f_tab_on = tkfont.Font(family=ui, size=-15, weight="bold")
        self.f_hist_expr = tkfont.Font(family=ui, size=-13)
        self.f_hist_res = tkfont.Font(family=disp, size=-22, weight="bold")

        root.title("Calculadora")
        root.configure(bg=T["bg"])
        root.geometry("340x540")
        root.minsize(320, 500)
        self._set_icon(root)

        # ---- coluna da calculadora ----
        self.main = tk.Frame(root, bg=T["bg"])
        self.side = tk.Frame(root, bg=T["panel"], width=300)
        self.side.pack_propagate(False)
        self.side_visible = False
        self.main.pack(side="left", fill="both", expand=True)

        header = tk.Frame(self.main, bg=T["bg"])
        header.pack(fill="x", padx=12, pady=(10, 0))
        tk.Label(header, text="Padrão", bg=T["bg"], fg=T["text"], font=self.f_title).pack(side="left")
        self.hist_btn = tk.Label(header, text="🕘", bg=T["bg"], fg=T["text"],
                                 font=(ui, 14), cursor="hand2", padx=6)
        self.hist_btn.pack(side="right")
        self.hist_btn.bind("<Button-1>", lambda e: self.show_history_popup())

        # visor
        screen = tk.Frame(self.main, bg=T["bg"])
        screen.pack(fill="both", expand=True, padx=14)
        self.expr_label = tk.Label(screen, text="", bg=T["bg"], fg=T["dim"], anchor="e",
                                   font=self.f_expr)
        self.big_label = tk.Label(screen, text="0", bg=T["bg"], fg=T["text"], anchor="e",
                                  font=self.f_big)
        self.big_label.pack(side="bottom", fill="x")
        self.expr_label.pack(side="bottom", fill="x")
        self.big_label.bind("<Configure>", lambda e: self._fit_big())

        # memória
        mem = tk.Frame(self.main, bg=T["bg"])
        mem.pack(fill="x", padx=4)
        self.mem_buttons = {}
        for i, (label, cmd) in enumerate([
            ("MC", self.mem_clear), ("MR", self.mem_recall), ("M+", lambda: self.mem_add(1)),
            ("M−", lambda: self.mem_add(-1)), ("MS", self.mem_store),
        ]):
            mem.columnconfigure(i, weight=1, uniform="m")
            b = FlatButton(mem, label, cmd, self.f_small)
            b.grid(row=0, column=i, sticky="nsew", padx=1)
            self.mem_buttons[label] = b

        # teclado
        pad = tk.Frame(self.main, bg=T["bg"])
        pad.pack(fill="both", expand=True, padx=4, pady=(2, 4))
        layout = [
            ["%", "CE", "C", "⌫"],
            ["¹⁄ₓ", "x²", "²√x", DIVIDE],
            ["7", "8", "9", TIMES],
            ["4", "5", "6", MINUS],
            ["1", "2", "3", PLUS],
            ["+/−", "0", ",", "="],
        ]
        self.buttons: dict[str, FluentButton] = {}
        for r, row in enumerate(layout):
            pad.rowconfigure(r, weight=1, uniform="r")
            for c, label in enumerate(row):
                pad.columnconfigure(c, weight=1, uniform="c")
                if label == "=":
                    kind, font = "accent", self.f_key_op
                elif label in (PLUS, MINUS, TIMES, DIVIDE):
                    kind, font = "fn", self.f_key_op
                elif label.isdigit() or label in ("+/−", ","):
                    kind, font = "num", self.f_key_num
                else:
                    kind, font = "fn", self.f_key
                btn = FluentButton(pad, label, lambda l=label: self.on_key(l), kind, font)
                btn.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
                self.buttons[label] = btn

        self._build_side_panel()
        root.bind("<Key>", self.on_keyboard)
        root.bind("<Configure>", self._on_resize)
        self.refresh()

    # ------------------------------------------------------------------
    def _set_icon(self, window):
        ico = resource_path("icon.ico")
        if os.path.exists(ico):
            try:
                window.iconbitmap(default=ico)
            except tk.TclError:
                pass

    def _on_resize(self, event):
        if event.widget is not self.root:
            return
        want = event.width >= self.SIDE_PANEL_MIN_WIDTH
        if want and not self.side_visible:
            self.side.pack(side="right", fill="y", before=self.main)
            self.hist_btn.pack_forget()
            self.side_visible = True
        elif not want and self.side_visible:
            self.side.pack_forget()
            self.hist_btn.pack(side="right")
            self.side_visible = False

    # ---- painel lateral (Histórico / Memória) -------------------------
    def _build_side_panel(self):
        tabs = tk.Frame(self.side, bg=T["panel"])
        tabs.pack(fill="x", padx=12, pady=(14, 0))
        self.tab_labels = {}
        for key, text in (("hist", "Histórico"), ("mem", "Memória")):
            f = tk.Frame(tabs, bg=T["panel"])
            f.pack(side="left", padx=(0, 18))
            lbl = tk.Label(f, text=text, bg=T["panel"], fg=T["text"], font=self.f_tab, cursor="hand2")
            lbl.pack()
            line = tk.Frame(f, bg=T["panel"], height=3, width=18)
            line.pack(pady=(3, 0))
            lbl.bind("<Button-1>", lambda e, k=key: self._select_tab(k))
            self.tab_labels[key] = (lbl, line)
        self.side_list = tk.Frame(self.side, bg=T["panel"])
        self.side_list.pack(fill="both", expand=True, padx=8, pady=8)

    def _select_tab(self, key):
        self.side_tab = key
        self._render_side()

    def _render_side(self):
        for key, (lbl, line) in self.tab_labels.items():
            active = key == self.side_tab
            line.configure(bg=T["tab_line"] if active else T["panel"])
            lbl.configure(font=self.f_tab_on if active else self.f_tab)
        for w in self.side_list.winfo_children():
            w.destroy()
        if self.side_tab == "hist":
            items = list(reversed(self.calc.history[-30:]))
            empty = "Ainda não há histórico."
        else:
            items = [("", format_number(v)) for v in reversed(self.memory)]
            empty = "Não há nada salvo na memória."
        if not items:
            tk.Label(self.side_list, text=empty, bg=T["panel"], fg=T["text"],
                     font=self.f_small, anchor="w").pack(fill="x", padx=6, pady=4)
            return
        for expr, result in items:
            self._history_item(self.side_list, expr, result, self.use_result)

    def _history_item(self, parent, expr, result, on_click):
        box = tk.Frame(parent, bg=T["panel"], cursor="hand2")
        box.pack(fill="x", pady=1)
        widgets = [box]
        if expr:
            l1 = tk.Label(box, text=f"{expr} =", bg=T["panel"], fg=T["dim"],
                          font=self.f_hist_expr, anchor="e")
            l1.pack(fill="x", padx=8, pady=(6, 0))
            widgets.append(l1)
        l2 = tk.Label(box, text=result, bg=T["panel"], fg=T["text"],
                      font=self.f_hist_res, anchor="e")
        l2.pack(fill="x", padx=8, pady=(0, 6))
        widgets.append(l2)
        for w in widgets:
            w.bind("<Enter>", lambda e: [x.configure(bg=T["hist_hover"]) for x in widgets])
            w.bind("<Leave>", lambda e: [x.configure(bg=T["panel"]) for x in widgets])
            w.bind("<Button-1>", lambda e: on_click(result, expr))

    def use_result(self, result: str, expr: str = ""):
        self.error_text = ""
        self.calc.clear()
        self.calc.expr = result.replace(".", "").replace("-", MINUS)
        self.calc.just_evaluated = True
        self.last_expr = f"{expr} =" if expr else ""
        self.refresh()

    def show_history_popup(self):
        """Com a janela estreita, o histórico abre numa janelinha."""
        win = tk.Toplevel(self.root)
        win.title("Histórico")
        win.configure(bg=T["panel"])
        win.geometry("300x420")
        frame = tk.Frame(win, bg=T["panel"])
        frame.pack(fill="both", expand=True, padx=8, pady=8)
        if not self.calc.history:
            tk.Label(frame, text="Ainda não há histórico.", bg=T["panel"], fg=T["text"],
                     font=self.f_small).pack(anchor="w")
            return

        def pick(result, expr):
            self.use_result(result, expr)
            win.destroy()

        for expr, result in reversed(self.calc.history[-30:]):
            self._history_item(frame, expr, result, pick)

    # ---- memória -------------------------------------------------------
    def mem_store(self):
        self.memory.append(self.calc.current_value())
        self.refresh()

    def mem_add(self, sign):
        value = self.calc.current_value() * sign
        if self.memory:
            self.memory[-1] += value
        else:
            self.memory.append(value)
        self.refresh()

    def mem_recall(self):
        if self.memory:
            self.calc.insert_value(self.memory[-1])
            self.last_expr = ""
            self.refresh()

    def mem_clear(self):
        self.memory.clear()
        self.refresh()

    # ---- teclas --------------------------------------------------------
    def on_key(self, label: str):
        c = self.calc
        if self.error_text:
            self.error_text = ""
            c.clear()
            if label in ("C", "CE", "⌫"):
                self.refresh()
                return
        was_evaluated = c.just_evaluated
        if label.isdigit():
            c.press_digit(label)
        elif label == ",":
            c.press_decimal()
        elif label in (PLUS, MINUS, TIMES, DIVIDE):
            c.press_operator(label)
        elif label == "%":
            c.press_percent()
        elif label == "+/−":
            c.press_sign()
        elif label == "⌫":
            if not c.just_evaluated:
                c.backspace()
        elif label == "C":
            c.clear()
        elif label == "CE":
            c.clear_entry()
        elif label in ("¹⁄ₓ", "x²", "²√x"):
            func = {"¹⁄ₓ": "inv", "x²": "sqr", "²√x": "sqrt"}[label]
            if not c.apply_function(func):
                self.error_text = ("Não é possível dividir por zero" if func == "inv"
                                   else "Entrada inválida")
        elif label == "=":
            if c.expr and not c.just_evaluated:
                if c.equals() == "Erro":
                    self.error_text = "Não é possível dividir por zero"
                else:
                    self.last_expr = c.history[-1][0] + " ="
        if was_evaluated and not c.just_evaluated:
            self.last_expr = ""
        self.refresh()

    def on_keyboard(self, event):
        key, ch = event.keysym, event.char
        mapping = {
            "Return": "=", "KP_Enter": "=", "equal": "=",
            "BackSpace": "⌫", "Escape": "C", "Delete": "CE",
            "plus": PLUS, "KP_Add": PLUS, "minus": MINUS, "KP_Subtract": MINUS,
            "asterisk": TIMES, "KP_Multiply": TIMES, "slash": DIVIDE, "KP_Divide": DIVIDE,
            "percent": "%", "comma": ",", "period": ",", "KP_Decimal": ",",
            "KP_Separator": ",", "F9": "+/−", "r": "¹⁄ₓ", "q": "x²", "at": "²√x",
        }
        label = mapping.get(key)
        if label is None and ch and ch.isdigit():
            label = ch
        if label is None:
            return
        btn = self.buttons.get(label)
        if btn:
            btn.flash()
        self.on_key(label)

    # ---- tela ----------------------------------------------------------
    def refresh(self):
        c = self.calc
        if self.error_text:
            self.expr_label.configure(text="")
            self.big_label.configure(text=self.error_text)
        elif c.just_evaluated:
            self.expr_label.configure(text=self.last_expr)
            self.big_label.configure(text=display(c.expr) if c.expr else "0")
        else:
            preview = c.preview()
            if preview:
                self.expr_label.configure(text=display(c.expr))
                self.big_label.configure(text=preview)
            else:
                self.expr_label.configure(text="")
                self.big_label.configure(text=display(c.expr) if c.expr else "0")
        has_mem = bool(self.memory)
        for k in ("MC", "MR"):
            self.mem_buttons[k].set_enabled(has_mem)
        self._fit_big()
        self._render_side()

    def _fit_big(self):
        width = self.big_label.winfo_width()
        if width < 50:
            return
        text = self.big_label.cget("text")
        size = 26 if self.error_text else 48
        f = tkfont.Font(family=self.f_big_family, size=-size, weight="bold")
        while size > 14 and f.measure(text) > width - 6:
            size -= 2
            f.configure(size=-size)
        if self.f_big.cget("size") != -size:
            self.f_big.configure(size=-size)


def main():
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_ID)
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
