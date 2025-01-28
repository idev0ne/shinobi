import random
import subprocess
import imageio_ffmpeg

def make_unique_video(input_path, output_path):
    # Генерация случайных параметров (пример)
    brightness = random.uniform(-0.1, 0.1)
    contrast   = random.uniform(0.9, 1.2)
    saturation = random.uniform(0.9, 1.3)
    noise_level = random.randint(5, 30)
    hue_shift = random.uniform(-20, 20)
    hue_sat   = random.uniform(0.9, 1.2)
    rs        = random.uniform(-0.3, 0.3)
    gs        = random.uniform(-0.3, 0.3)
    bs        = random.uniform(-0.3, 0.3)

    volume_gain = random.uniform(0.9, 1.1)
    atempo_val  = random.uniform(0.95, 1.05)

    video_filters = (
        f"eq=brightness={brightness:.3f}:contrast={contrast:.3f}:saturation={saturation:.3f},"
        f"colorbalance=rs={rs:.3f}:gs={gs:.3f}:bs={bs:.3f},"
        f"noise=alls={noise_level}:allf=t+u,"
        f"hue=h={hue_shift:.3f}:s={hue_sat:.3f}"
    )
    audio_filters = f"volume={volume_gain:.3f},atempo={atempo_val:.3f}"

    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()

    cmd = [
        ffmpeg_exe,
        '-y',
        '-i', input_path,
        '-vf', video_filters,
        '-af', audio_filters,
        '-c:v', 'libx264',
        '-profile:v', 'baseline',   # более совместимый профиль H.264
        '-level', '3.0',            # ограничиваем уровень совместимости
        '-pix_fmt', 'yuv420p',      # классический формат пикселей
        '-preset', 'medium',
        '-movflags', '+faststart',  # улучшает совместимость и позволяет стримить MP4
        '-c:a', 'aac',
        output_path
    ]

    subprocess.run(cmd, check=True)

    print("=== Использованные параметры ===")
    print(f"Brightness={brightness:.3f}, Contrast={contrast:.3f}, Saturation={saturation:.3f}")
    print(f"Noise={noise_level}, Hue shift={hue_shift:.3f}, Hue sat={hue_sat:.3f}")
    print(f"Colorbalance: rs={rs:.3f}, gs={gs:.3f}, bs={bs:.3f}")
    print(f"Volume={volume_gain:.3f}, Atempo={atempo_val:.3f}")
    print("Файл сохранён как:", output_path)

