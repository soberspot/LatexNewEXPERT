import cv2
import numpy as np
import random
import tkinter as tk
from tkinter import filedialog
import os

def put_watermark(alpha):
    logo = "ApplicationName"
    sub_logo = "Free version"
    font_scale = 1.0
    max_font_scale = 15.0
    thickness = 7
    font = cv2.FONT_HERSHEY_COMPLEX
    
    x = random.random() * alpha.shape[1] / 10 + 15
    y1 = alpha.shape[0] / 10
    y2 = alpha.shape[0] * 0.9
    y = y1 + random.random() * (y2 - y1)
    begin_logo = (int(x), int(y))
    
    max_length = alpha.shape[1] - begin_logo[0]
    text_size = (100, 100)
    for d in np.arange(max_font_scale, 0, -0.5):
        (w, h), baseline = cv2.getTextSize(logo, font, d, thickness)
        text_size = (w, h)
        if text_size[0] < max_length:
            font_scale = d
            break
    
    cv2.putText(alpha, logo, begin_logo, font, font_scale, (255, 255, 255), thickness)
    begin_logo = (begin_logo[0], begin_logo[1] + text_size[1])
    cv2.putText(alpha, sub_logo, begin_logo, font, font_scale / 2, (255, 255, 255), thickness - 3)

def select_and_process_image():
    root = tk.Tk()
    root.withdraw()
    
    # Диалог выбора файла
    file_path = filedialog.askopenfilename(
        title="Выберите изображение",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.bmp")],
        initialdir=os.getcwd()
    )
    
    if file_path:
        # Проверяем существование файла
        if os.path.exists(file_path):
            # Читаем файл с явным указанием кодировки пути
            try:
                img = cv2.imdecode(np.fromfile(file_path, dtype=np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    put_watermark(img)
                    output_path = os.path.splitext(file_path)[0] + "_watermarked.jpg"
                    # Сохраняем с учетом кодировки
                    cv2.imencode('.jpg', img)[1].tofile(output_path)
                    print(f"Изображение сохранено как: {output_path}")
                    cv2.imshow("Watermarked Image", img)
                    cv2.waitKey(0)
                    cv2.destroyAllWindows()
                else:
                    print(f"Ошибка: не удалось загрузить изображение из {file_path}")
            except Exception as e:
                print(f"Ошибка при обработке файла: {e}")
        else:
            print(f"Файл не найден: {file_path}")
    else:
        print("Файл не выбран")
    
    root.destroy()

if __name__ == "__main__":
    select_and_process_image()