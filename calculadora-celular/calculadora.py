"""Calculadora estilo celular para Windows (Tkinter).

Execute com:  python calculadora.py
Ou gere o .exe com:  pyinstaller --onefile --windowed --name Calculadora calculadora.py
"""

from __future__ import annotations

import tkinter as tk
import tkinter.font as tkfont

from calc_engine import DIVIDE, MINUS, PLUS, TIMES, Calculator, display

# Cores (tema escuro, parecido com calculadoras de celular)
BG = "#000000"
FG = "#FFFFFF"
FG_DIM = "#8E8E93"
KEY_NUM = "#333333"
KEY_NUM_HOVER = "#4A4A4A"
KEY_FN = "#A5A5A5"
KEY_FN_HOVER = "#C7C7C7"
KEY_OP = "#FF9F0A"
KEY_OP_HOVER = "#FFB940"

FONT_FAMILY = "Segoe UI"


class RoundButton(tk.Canvas):
    """Botão redondo/arredondado desenhado num Canvas, que se ajusta ao tamanho."""

    def __init__(self, master, text, command, bg, hover, fg=FG, font_size=26):
        super().__init__(master, bg=BG, highlightthickness=0, bd=0, cursor="hand2")
        self.text = text
        self.command = command
        self.color = bg
        self.hover_color = hover
        self.fg = fg
        self.font = tkfont.Font(family=FONT_FAMILY, size=font_size)
        self._hover = False
        self._pressed = False
        self.bind("<Configure>", lambda e: self.redraw())
        self.bind("<Enter>", lambda e: self._set_hover(True))
        self.bind("<Leave>", lambda e: self._set_hover(False))
        self.bind("<ButtonPress-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)

    def _set_hover(self, value):
        self._hover = value
        if not value:
            self._pressed = False
        self.redraw()

    def _on_press(self, _event):
        self._pressed = True
        self.redraw()

    def _on_release(self, _event):
        was_pressed = self._pressed
        self._pressed = False
        self.redraw()
        if was_pressed and self._hover:
            self.command()

    def flash(self):
        """Pisca o botão quando a tecla correspondente é usada no teclado."""
        self._pressed = True
        self.redraw()
        self.after(110, self._unflash)

    def _unflash(self):
        self._pressed = False
        self.redraw()

    def redraw(self):
        self.delete("all")
        w, h = self.winfo_width(), self.winfo_height()
        if w < 4 or h < 4:
            return
        pad = 6
        x0, y0, x1, y1 = pad, pad, w - pad, h - pad
        r = min(x1 - x0, y1 - y0) / 2
        color = self.hover_color if (self._hover or self._pressed) else self.color
        if self._pressed:
            color = _mix(color, "#FFFFFF", 0.25)
        # retângulo com cantos totalmente arredondados (vira círculo quando quadrado)
        self.create_oval(x0, y0, x0 + 2 * r, y0 + 2 * r, fill=color, outline=color)
        self.create_oval(x1 - 2 * r, y1 - 2 * r, x1, y1, fill=color, outline=color)
        self.create_oval(x0, y1 - 2 * r, x0 + 2 * r, y1, fill=color, outline=color)
        self.create_oval(x1 - 2 * r, y0, x1, y0 + 2 * r, fill=color, outline=color)
        self.create_rectangle(x0 + r, y0, x1 - r, y1, fill=color, outline=color)
        self.create_rectangle(x0, y0 + r, x1, y1 - r, fill=color, outline=color)
        size = max(12, int(min(w, h) * 0.32))
        self.font.configure(size=-size)  # negativo = pixels
        self.create_text(w / 2, h / 2, text=self.text, fill=self.fg, font=self.font)


def _mix(c1, c2, t):
    a = [int(c1[i:i + 2], 16) for i in (1, 3, 5)]
    b = [int(c2[i:i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b))


class App:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.calc = Calculator()
        self.error = False
        self.buttons: dict[str, RoundButton] = {}

        root.title("Calculadora")
        root.configure(bg=BG)
        root.geometry("380x640")
        root.minsize(300, 480)

        # ---- Topo: botão de histórico ----
        top = tk.Frame(root, bg=BG)
        top.pack(fill="x", padx=14, pady=(10, 0))
        hist = tk.Label(top, text="🕘 Histórico", bg=BG, fg=KEY_OP, cursor="hand2",
                        font=(FONT_FAMILY, 11))
        hist.pack(side="left")
        hist.bind("<Button-1>", lambda e: self.show_history())

        # ---- Visor ----
        screen = tk.Frame(root, bg=BG)
        screen.pack(fill="both", expand=True, padx=18)
        self.expr_var = tk.StringVar(value="0")
        self.preview_var = tk.StringVar(value="")
        self.preview_label = tk.Label(screen, textvariable=self.preview_var, bg=BG, fg=FG_DIM,
                                      anchor="e", font=(FONT_FAMILY, 22))
        self.expr_label = tk.Label(screen, textvariable=self.expr_var, bg=BG, fg=FG,
                                   anchor="e", font=(FONT_FAMILY, 44))
        self.preview_label.pack(side="bottom", fill="x")
        self.expr_label.pack(side="bottom", fill="x")
        self.expr_label.bind("<Configure>", lambda e: self._fit_text())

        # ---- Teclado ----
        pad = tk.Frame(root, bg=BG)
        pad.pack(fill="both", expand=True, padx=8, pady=(4, 12))
        layout = [
            [("C", "fn"), ("⌫", "fn"), ("%", "fn"), (DIVIDE, "op")],
            [("7", "num"), ("8", "num"), ("9", "num"), (TIMES, "op")],
            [("4", "num"), ("5", "num"), ("6", "num"), (MINUS, "op")],
            [("1", "num"), ("2", "num"), ("3", "num"), (PLUS, "op")],
            [("±", "num"), ("0", "num"), (",", "num"), ("=", "op")],
        ]
        styles = {
            "num": (KEY_NUM, KEY_NUM_HOVER, FG),
            "fn": (KEY_FN, KEY_FN_HOVER, "#000000"),
            "op": (KEY_OP, KEY_OP_HOVER, FG),
        }
        for r, row in enumerate(layout):
            pad.rowconfigure(r, weight=1, uniform="row")
            for c, (label, kind) in enumerate(row):
                pad.columnconfigure(c, weight=1, uniform="col")
                bg, hover, fg = styles[kind]
                btn = RoundButton(pad, label, lambda l=label: self.on_key(l), bg, hover, fg)
                btn.grid(row=r, column=c, sticky="nsew")
                self.buttons[label] = btn

        root.bind("<Key>", self.on_keyboard)
        self.refresh()

    # ---------------------------------------------------------------
    def on_key(self, label: str):
        if self.error and label not in ("C", "⌫"):
            self.calc.clear()
        self.error = False
        c = self.calc
        if label.isdigit():
            c.press_digit(label)
        elif label == ",":
            c.press_decimal()
        elif label in (PLUS, MINUS, TIMES, DIVIDE):
            c.press_operator(label)
        elif label == "%":
            c.press_percent()
        elif label == "±":
            c.press_sign()
        elif label == "⌫":
            c.backspace()
        elif label == "C":
            c.clear()
        elif label == "=":
            result = c.equals()
            if result == "Erro":
                self.error = True
        self.refresh()

    def on_keyboard(self, event):
        key = event.keysym
        ch = event.char
        mapping = {
            "Return": "=", "KP_Enter": "=", "equal": "=",
            "BackSpace": "⌫", "Escape": "C", "Delete": "C",
            "plus": PLUS, "KP_Add": PLUS,
            "minus": MINUS, "KP_Subtract": MINUS,
            "asterisk": TIMES, "KP_Multiply": TIMES, "x": TIMES, "X": TIMES,
            "slash": DIVIDE, "KP_Divide": DIVIDE,
            "percent": "%",
            "comma": ",", "period": ",", "KP_Decimal": ",", "KP_Separator": ",",
            "F9": "±",
        }
        label = mapping.get(key)
        if label is None and ch and ch.isdigit():
            label = ch
        if label is None and ch in mapping.values():
            label = ch
        if label is None:
            return
        btn = self.buttons.get(label)
        if btn:
            btn.flash()
        self.on_key(label)

    # ---------------------------------------------------------------
    def refresh(self):
        if self.error:
            self.expr_var.set("Erro")
            self.preview_var.set("Não dá para dividir por zero")
        else:
            self.expr_var.set(display(self.calc.expr) if self.calc.expr else "0")
            preview = self.calc.preview()
            self.preview_var.set(f"= {preview}" if preview else "")
        self.buttons["C"].text = "AC" if not self.calc.expr else "C"
        self.buttons["C"].redraw()
        self._fit_text()

    def _fit_text(self):
        """Diminui a fonte do visor quando a conta fica comprida."""
        width = self.expr_label.winfo_width()
        if width < 50:  # janela ainda não desenhada
            return
        text = self.expr_var.get()
        size = 48
        f = tkfont.Font(family=FONT_FAMILY, size=-size)
        while size > 16 and f.measure(text) > width - 8:
            size -= 2
            f.configure(size=-size)
        self.expr_label.configure(font=(FONT_FAMILY, -size))

    def show_history(self):
        win = tk.Toplevel(self.root)
        win.title("Histórico")
        win.configure(bg=BG)
        win.geometry("340x420")
        if not self.calc.history:
            tk.Label(win, text="Nenhuma conta ainda", bg=BG, fg=FG_DIM,
                     font=(FONT_FAMILY, 13)).pack(expand=True)
            return
        box = tk.Listbox(win, bg="#1C1C1E", fg=FG, font=(FONT_FAMILY, 13), bd=0,
                         highlightthickness=0, selectbackground=KEY_OP, activestyle="none")
        box.pack(fill="both", expand=True, padx=10, pady=10)
        entries = list(reversed(self.calc.history))
        for expr, result in entries:
            box.insert("end", f"{expr} = {result}")

        def use(_e):
            sel = box.curselection()
            if sel:
                result = entries[sel[0]][1]
                self.calc.clear()
                self.calc.expr = result.replace(".", "").replace("-", MINUS)
                self.calc.just_evaluated = True
                self.refresh()
                win.destroy()

        box.bind("<Double-Button-1>", use)
        tk.Label(win, text="Clique duas vezes para usar o resultado", bg=BG, fg=FG_DIM,
                 font=(FONT_FAMILY, 10)).pack(pady=(0, 8))


def main():
    try:  # deixa o texto nítido em telas com escala (Windows)
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
