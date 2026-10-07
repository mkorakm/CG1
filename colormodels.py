
import tkinter as tk
from tkinter import colorchooser

def rgb_to_cmyk(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    k = 1 - max(r, g, b)
    if k == 1:
        return 0, 0, 0, 100
    c = (1 - r - k) / (1 - k)
    m = (1 - g - k) / (1 - k)
    y = (1 - b - k) / (1 - k)
    return c * 100, m * 100, y * 100, k * 100


def cmyk_to_rgb(c, m, y, k):
    c, m, y, k = c / 100, m / 100, y / 100, k / 100
    r = 255 * (1 - c) * (1 - k)
    g = 255 * (1 - m) * (1 - k)
    b = 255 * (1 - y) * (1 - k)
    return r, g, b


def rgb_to_hsv(r, g, b):
    r, g, b = r / 255, g / 255, b / 255
    mx, mn = max(r, g, b), min(r, g, b)
    d = mx - mn

    if d == 0:
        h = 0
    elif mx == r:
        h = 60 * (((g - b) / d) % 6)
    elif mx == g:
        h = 60 * ((b - r) / d + 2)
    else:
        h = 60 * ((r - g) / d + 4)
    s = 0 if mx == 0 else d / mx
    v = mx
    return h, s * 100, v * 100


def hsv_to_rgb(h, s, v):
    s, v = s / 100, v / 100
    c = v * s
    hp = (h % 360) / 60
    x = c * (1 - abs(hp % 2 - 1))
    m = v - c
    sector = int(hp)
    r, g, b = [(c, x, 0), (x, c, 0), (0, c, x),
               (0, x, c), (x, 0, c), (c, 0, x)][sector]
    return (r + m) * 255, (g + m) * 255, (b + m) * 255


MODELS = {
    "RGB":  [("R", 0, 255, 1), ("G", 0, 255, 1), ("B", 0, 255, 1)],
    "CMYK": [("C", 0, 100, 0.1), ("M", 0, 100, 0.1),
             ("Y", 0, 100, 0.1), ("K", 0, 100, 0.1)],
    "HSV":  [("H", 0, 360, 0.1), ("S", 0, 100, 0.1), ("V", 0, 100, 0.1)],
}


def to_rgb(model, values):

    if model == "RGB":
        rgb = values
    elif model == "CMYK":
        rgb = cmyk_to_rgb(*values)
    else:
        rgb = hsv_to_rgb(*values)
    return [min(255, max(0, x)) for x in rgb]


def from_rgb(model, rgb):

    if model == "RGB":
        return list(rgb)
    if model == "CMYK":
        return list(rgb_to_cmyk(*rgb))
    return list(rgb_to_hsv(*rgb))

class Row:

    def __init__(self, parent, name, lo, hi, step, on_change):
        self.lo, self.hi, self.step = lo, hi, step
        self.on_change = on_change
        self.var = tk.StringVar()

        frame = tk.Frame(parent)
        frame.pack(fill="x", pady=2)
        tk.Label(frame, text=name, width=2, font=("Arial", 11, "bold")).pack(side="left")

        self.scale = tk.Scale(frame, from_=lo, to=hi, resolution=step,
                              orient="horizontal", showvalue=False, length=230,
                              command=self._scale_moved)
        self.scale.pack(side="left", padx=5)

        self.entry = tk.Spinbox(frame, from_=lo, to=hi, increment=step, width=7,
                                textvariable=self.var, command=self._entry_changed)
        self.entry.pack(side="left")
        self.entry.bind("<Return>", lambda e: self._entry_changed())
        self.entry.bind("<FocusOut>", lambda e: self._entry_changed())

    def fmt(self, value):
        return str(round(value)) if self.step >= 1 else f"{value:.1f}"

    def set(self, value):

        self.scale.set(value)
        self.var.set(self.fmt(value))

    def get(self):
        return float(self.scale.get())

    def _scale_moved(self, value):
        self.var.set(self.fmt(float(value)))
        self.on_change()

    def _entry_changed(self):
        try:
            x = float(self.var.get().replace(",", "."))
        except ValueError:
            x = self.get()
        x = min(self.hi, max(self.lo, x))
        self.set(x)
        self.on_change()


class App:
    def __init__(self, root):
        root.title("Цветовые модели: CMYK - RGB - HSV")
        self.lock = False
        self.rgb = [255, 128, 0]

        left = tk.Frame(root, padx=10, pady=10)
        left.pack(side="left", fill="y")
        self.preview = tk.Label(left, width=22, height=10)
        self.preview.pack()
        self.hex_label = tk.Label(left, font=("Courier", 14, "bold"))
        self.hex_label.pack(pady=8)
        tk.Button(left, text="Выбрать из палитры...",
                  command=self.pick_from_palette).pack()

        right = tk.Frame(root, padx=10, pady=10)
        right.pack(side="left")
        self.rows = {}
        for model, comps in MODELS.items():
            box = tk.LabelFrame(right, text=model, padx=8, pady=5,
                                font=("Arial", 11, "bold"))
            box.pack(fill="x", pady=4)
            self.rows[model] = [
                Row(box, name, lo, hi, step, lambda m=model: self.on_change(m))
                for name, lo, hi, step in comps
            ]

        self.refresh(skip=None)

    def on_change(self, model):

        if self.lock:
            return
        values = [row.get() for row in self.rows[model]]
        self.rgb = to_rgb(model, values)        # 1) переводим в RGB
        self.refresh(skip=model)                # 2) обновляем остальные модели

    def refresh(self, skip):

        self.lock = True
        for model, rows in self.rows.items():
            if model == skip:
                continue
            for row, value in zip(rows, from_rgb(model, self.rgb)):
                row.set(value)
        hex_color = "#%02x%02x%02x" % tuple(round(x) for x in self.rgb)
        self.preview.config(bg=hex_color)
        self.hex_label.config(text=hex_color.upper())
        self.lock = False

    def pick_from_palette(self):

        hex_color = self.hex_label.cget("text")
        rgb, _ = colorchooser.askcolor(color=hex_color, title="Палитра")
        if rgb:
            self.rgb = list(rgb)
            self.refresh(skip=None)


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()