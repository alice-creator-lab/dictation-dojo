from PIL import Image, ImageDraw, ImageFont
import glob, os

OUT = "/home/admin/dictation-dojo/icons"
os.makedirs(OUT, exist_ok=True)

cands = glob.glob("/usr/share/fonts/google-noto-cjk/*Black*") + glob.glob("/usr/share/fonts/google-noto-cjk/*.ttc")
FONT = sorted(cands)[0]

BG = (200, 64, 47)      # 朱紅
CREAM = (255, 253, 248)
INK = (38, 34, 29)


def glyph(size, ratio, color=CREAM):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    f = ImageFont.truetype(FONT, int(size * ratio))
    bb = d.textbbox((0, 0), "默", font=f)
    w, h = bb[2] - bb[0], bb[3] - bb[1]
    d.text(((size - w) / 2 - bb[0], (size - h) / 2 - bb[1]), "默", font=f, fill=color)
    return img


def make(size, ratio, rounded=True, grid=True, bg=BG):
    S = size * 4
    img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    if rounded:
        d.rounded_rectangle([0, 0, S - 1, S - 1], radius=int(S * 0.22), fill=bg)
    else:
        d.rectangle([0, 0, S - 1, S - 1], fill=bg)
    if grid:
        # 田字格：淡淡十字
        col = (255, 255, 255, 26)
        lw = max(2, int(S * 0.005))
        pad = int(S * 0.18)
        d.line([S // 2, pad, S // 2, S - pad], fill=col, width=lw)
        d.line([pad, S // 2, S - pad, S // 2], fill=col, width=lw)
    img = Image.alpha_composite(img, glyph(S, ratio))
    return img.resize((size, size), Image.LANCZOS)


make(192, 0.50).save(f"{OUT}/icon-192.png")
make(512, 0.50).save(f"{OUT}/icon-512.png")
make(512, 0.40, rounded=False).save(f"{OUT}/icon-maskable-512.png")
make(180, 0.50, rounded=False).save(f"{OUT}/apple-touch-icon.png")
make(32, 0.56, rounded=False, grid=False).save(f"{OUT}/favicon-32.png")

for f in sorted(os.listdir(OUT)):
    p = os.path.join(OUT, f)
    print(f, Image.open(p).size, os.path.getsize(p) // 1024, "KB")
