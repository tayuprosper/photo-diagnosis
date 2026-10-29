import sys

from PIL import Image, ImageFilter, ImageOps, ImageStat

STOP = {"long_side": 200, "brightness": 50, "sharpness": 100}
WARN = {"long_side": 600, "brightness": 80, "sharpness": 500}
LABELS = {"long_side": "too small", "brightness": "too dark", "sharpness": "too blurry"}


def measure(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    gray = img.convert("L")
    brightness = ImageStat.Stat(gray).mean[0]

    scale = 800 / max(w, h)
    small = gray.resize((round(w * scale), round(h * scale)))
    small = ImageOps.autocontrast(small, cutoff=1)  # so darkness does not look like blur
    edges = small.filter(ImageFilter.FIND_EDGES)
    sharpness = ImageStat.Stat(edges).var[0]

    return {
        "long_side": max(w, h),
        "brightness": round(brightness),
        "sharpness": round(sharpness),
    }


def check(path):
    m = measure(path)
    stops, warns = [], []
    for key, label in LABELS.items():
        if m[key] < STOP[key]:
            stops.append(label)
        elif m[key] < WARN[key]:
            warns.append(label)
    return m, stops, warns


if __name__ == "__main__":
    for path in sys.argv[1:]:
        m, stops, warns = check(path)
        verdict = "STOP" if stops else "WARN" if warns else "OK"
        print(path, m, verdict, stops or warns)