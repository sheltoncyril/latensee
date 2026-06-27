"""Generates icon.ico and icon.png for use with PyInstaller builds."""
from PIL import Image, ImageDraw


def draw_icon(size: int) -> Image.Image:
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    r = max(3, size // 5)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=r, fill="#0f111a")

    colors = ["#f6821f", "#4285f4", "#7c3aed", "#5fb955"]
    fracs  = [0.26, 0.48, 0.69, 0.91]
    n      = len(colors)
    pad    = max(2, int(size * 0.15))
    inner_w = size - 2 * pad
    inner_h = size - 2 * pad
    bar_w  = max(1, int(inner_w / n) - max(1, int(size * 0.04)))
    gap    = max(1, (inner_w - n * bar_w) // (n - 1))
    bottom = size - pad

    for i, (color, frac) in enumerate(zip(colors, fracs)):
        bh = max(2, int(inner_h * frac))
        x0 = pad + i * (bar_w + gap)
        y0 = bottom - bh
        x1 = x0 + bar_w
        br = max(1, bar_w // 4)
        d.rounded_rectangle([x0, y0, x1, bottom], radius=br, fill=color)

    return img


if __name__ == "__main__":
    sizes  = [16, 24, 32, 48, 64, 128, 256]
    images = [draw_icon(s) for s in sizes]
    images[0].save("icon.ico", format="ICO", sizes=[(s, s) for s in sizes],
                   append_images=images[1:])
    images[-1].save("icon.png", format="PNG")
    print("Generated icon.ico and icon.png")
