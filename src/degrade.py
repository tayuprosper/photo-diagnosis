import sys

from PIL import Image, ImageEnhance, ImageFilter

src = Image.open(sys.argv[1]).convert("RGB")
w, h = src.size


def save(img, name, quality=85):
    img.save(name, "JPEG", quality=quality)


blurry = src.filter(ImageFilter.GaussianBlur(60))
save(blurry, "badblurry.jpeg")

dark = ImageEnhance.Brightness(src).enhance(0.25)
save(dark, "bad_dark.jpg")


whatsapp = src.resize((w // 4, h // 4))
save(whatsapp, "bad_whatsapp.jpg", quality=20)

worst = ImageEnhance.Brightness(blurry).enhance(0.4).resize((w // 4, h // 4))
save(worst, "bad_worst.jpg", quality=20)

print("Made 4 bad copies")