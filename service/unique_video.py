import random
import subprocess
import imageio_ffmpeg

def make_unique_video(input_path, output_path):
    # Генерация "мягких" случайных параметров
    brightness   = random.uniform(-0.05, 0.05)   # вместо -0.1..0.1
    contrast     = random.uniform(0.95, 1.10)    # уже не 0.9..1.2
    saturation   = random.uniform(0.95, 1.10)    # уже не 0.9..1.3
    noise_level  = random.randint(3, 15)         # уменьшим шум
    hue_shift    = random.uniform(-10, 10)       # вместо -20..20
    hue_sat      = random.uniform(0.95, 1.05)    # диапазон насыщенности hue
    rs           = random.uniform(-0.1, 0.1)     # меньше разброс colorbalance
    gs           = random.uniform(-0.1, 0.1)
    bs           = random.uniform(-0.1, 0.1)

    # Аудио тоже сделаем чуть мягче
    volume_gain  = random.uniform(0.95, 1.05)
    atempo_val   = random.uniform(0.98, 1.02)

    # Формируем цепочку видеофильтров
    video_filters = (
        f"eq=brightness={brightness:.3f}:contrast={contrast:.3f}:saturation={saturation:.3f},"
        f"colorbalance=rs={rs:.3f}:gs={gs:.3f}:bs={bs:.3f},"
        f"noise=alls={noise_level}:allf=t+u,"
        f"hue=h={hue_shift:.3f}:s={hue_sat:.3f}"
    )

    # Фильтр для аудио
    audio_filters = f"volume={volume_gain:.3f},atempo={atempo_val:.3f}"

    # Путь к локальному ffmpeg
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg_exe,
        '-y',
        '-i', input_path,
        '-vf', video_filters,
        '-af', audio_filters,
        '-c:v', 'libx264',
        '-profile:v', 'baseline',
        '-level', '3.0',
        '-pix_fmt', 'yuv420p',
        '-preset', 'medium',
        '-movflags', '+faststart',
        '-c:a', 'aac',
        output_path
    ]

    subprocess.run(cmd, check=True)

    # Выводим информацию о применённых параметрах
    print("=== Использованные параметры (мягкая коррекция) ===")
    print(f"Brightness={brightness:.3f}, Contrast={contrast:.3f}, Saturation={saturation:.3f}")
    print(f"Noise={noise_level}, Hue shift={hue_shift:.3f}, Hue sat={hue_sat:.3f}")
    print(f"Colorbalance: rs={rs:.3f}, gs={gs:.3f}, bs={bs:.3f}")
    print(f"Volume={volume_gain:.3f}, Atempo={atempo_val:.3f}")
    print("Файл сохранён как:", output_path)


