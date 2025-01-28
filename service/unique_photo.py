import os
import random
import piexif
from PIL import Image, ImageDraw, ImageEnhance

def random_flip(img: Image.Image) -> Image.Image:
    """С 50% шансом отражаем картинку по горизонтали, с 50% - по вертикали."""
    # Можно варьировать логику по вкусу
    do_hflip = random.choice([True, False])
    do_vflip = random.choice([True, False])

    if do_hflip:
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
    if do_vflip:
        img = img.transpose(Image.FLIP_TOP_BOTTOM)

    return img

def random_rotate(img: Image.Image, angle_range=(-5, 5)) -> Image.Image:
    """
    Случайный поворот картинки на угол от -5 до +5 градусов.
    Заполняем "пропуски" чёрным или прозрачным (зависит от режима).
    """
    angle = random.uniform(*angle_range)
    return img.rotate(angle, expand=True, fillcolor=(0, 0, 0, 0))

def scale_image(img: Image.Image, scale_min=0.90, scale_max=1.10) -> Image.Image:
    """ Большее изменение масштаба (±10%). """
    width, height = img.size
    factor = random.uniform(scale_min, scale_max)
    new_w = int(width * factor)
    new_h = int(height * factor)
    if new_w < 1 or new_h < 1:
        return img
    return img.resize((new_w, new_h), Image.Resampling.LANCZOS)

def add_transparent_noise(img: Image.Image, intensity=5):
    """
    Добавляем шум сильнее (intensity=5 вместо 3).
    Увеличиваем кол-во точек и прозрачность в чуть большем диапазоне (5..30).
    """
    result = img.convert("RGBA")
    draw = ImageDraw.Draw(result, "RGBA")
    width, height = result.size

    total_pixels = width * height
    # Увеличим число точек:
    num_points = (total_pixels // 10000) * intensity

    for _ in range(num_points):
        x = random.randint(0, width - 1)
        y = random.randint(0, height - 1)
        color = (
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(0, 255),
            random.randint(5, 30)  # чуть выше альфа
        )
        draw.point((x, y), fill=color)

    return result

def strong_color_corrections(img: Image.Image) -> Image.Image:
    """
    Более сильная цветокоррекция:
      - Насыщенность (0.8..1.2)
      - Яркость (0.85..1.15)
      - Контраст (0.8..1.3)
    """
    # 1) Сильнее насыщенность (Color)
    sat_factor = random.uniform(0.8, 1.2)
    enhancer_color = ImageEnhance.Color(img)
    img = enhancer_color.enhance(sat_factor)

    # 2) Яркость (Brightness)
    bright_factor = random.uniform(0.85, 1.15)
    enhancer_bright = ImageEnhance.Brightness(img)
    img = enhancer_bright.enhance(bright_factor)

    # 3) Контраст (Contrast)
    contrast_factor = random.uniform(0.8, 1.3)
    enhancer_contrast = ImageEnhance.Contrast(img)
    img = enhancer_contrast.enhance(contrast_factor)

    return img

def generate_random_exif() -> bytes:
    """
    Создаём фейковые EXIF-данные.
    (Как и раньше, просто оставляем пример с Make, Model, Software и т.д.)
    """
    exif_dict = {
        "0th": {},
        "Exif": {},
        "GPS": {},
        "1st": {},
        "thumbnail": None
    }

    from piexif import ImageIFD, ExifIFD
    from datetime import datetime, timedelta

    exif_dict["0th"][ImageIFD.Make] = f"CameraBrand_{random.randint(100,999)}"
    exif_dict["0th"][ImageIFD.Model] = f"Model_{random.randint(1000,9999)}"
    exif_dict["0th"][ImageIFD.Software] = f"PhotoshopX_{random.randint(1,99)}"
    exif_dict["0th"][ImageIFD.Artist] = f"User_{random.randint(1000,9999)}"

    random_date = datetime.now() - timedelta(days=random.randint(0,1000))
    exif_dict["Exif"][ExifIFD.DateTimeOriginal] = random_date.strftime("%Y:%m:%d %H:%M:%S")

    exif_bytes = piexif.dump(exif_dict)
    return exif_bytes

def make_unique_photo(input_path: str, output_path: str):
    """
    1) Открываем картинку
    2) Последовательно:
       - Случайно flip (отзеркаливание)
       - Лёгкий поворот ±5 градусов
       - Масштаб ±10%
       - Сильная цветокоррекция
       - Случайный шум
    3) Сохраняем JPEG (без EXIF)
    4) Генерируем рандомный EXIF
    5) Встраиваем EXIF (piexif.insert)
    """
    import tempfile

    with Image.open(input_path) as img:

        # 3) scale ±10%
        img = scale_image(img, 0.90, 1.10)

        # 4) сильная цветокоррекция
        img = strong_color_corrections(img)

        # 5) шум
        img = add_transparent_noise(img, intensity=5)

        # Приводим в RGB (на случай RGBA или др. режим)
        final = img.convert("RGB")

        # Сохраняем во временный файл
        import tempfile
        tmp_fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
        os.close(tmp_fd)

        final.save(tmp_path, format="JPEG", quality=90)

    # 6) генерируем EXIF
    exif_bytes = generate_random_exif()

    # 7) вставляем EXIF
    with open(tmp_path, "rb") as f_in, open(output_path, "wb") as f_out:
        f_out.write(f_in.read())

    piexif.insert(exif_bytes, output_path)
    os.remove(tmp_path)
