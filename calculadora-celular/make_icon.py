"""Gera icon.ico (ícone próprio da calculadora). Requer Pillow.

    python make_icon.py
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

S = 512  # desenha grande e reduz, para ficar nítido


def font(size):
    for name in ("segoeuib.ttf", "DejaVuSans-Bold.ttf", "arialbd.ttf"):
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def draw() -> Image.Image:
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # corpo
    d.rounded_rectangle((40, 16, S - 40, S - 16), radius=70, fill="#2F3A4A")
    d.rounded_rectangle((40, 16, S - 40, S - 16), radius=70, outline="#1E2733", width=8)
    # visor
    d.rounded_rectangle((84, 62, S - 84, 176), radius=22, fill="#DDEBF7")
    f = font(84)
    d.text((S - 104, 120), "%", font=f, fill="#2F3A4A", anchor="rm")
    # teclas 3 x 3
    gap, top, left = 18, 206, 84
    size = (S - 84 - left - 2 * gap) / 3
    for r in range(3):
        for c in range(3):
            x0 = left + c * (size + gap)
            y0 = top + r * (size * 0.78 + gap)
            color = "#4CC2FF" if c == 2 else "#5B6878"
            if r == 2 and c == 2:
                color = "#FF9F0A"
            d.rounded_rectangle((x0, y0, x0 + size, y0 + size * 0.78), radius=18, fill=color)
    return img


def main():
    out = Path(__file__).with_name("icon.ico")
    big = draw()
    big.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
    big.resize((256, 256), Image.LANCZOS).save(out.with_name("icon.png"))
    print("gerado", out)


if __name__ == "__main__":
    main()
