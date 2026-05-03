from PIL import Image, ImageDraw

# ---- настройки ----
IMG_PATH = "фронт2.jpg"                 # исходное изображение
OUT_PATH = "front_with_grid_16x11.png"  # результат

COLS = 16  # столбцов по горизонтали
ROWS = 11  # рядов по вертикали

# зона деформации (1-based): rows 6–7, cols 7–8
ROW_TOP = 6
ROW_BOTTOM = 7
COL_LEFT = 7
COL_RIGHT = 8

# ---- загрузка ----
img = Image.open(IMG_PATH).convert("RGBA")
width, height = img.size

dx = width / COLS
dy = height / ROWS

# слой для сетки
grid_layer = Image.new("RGBA", (width, height), (0, 0, 0, 0))
draw = ImageDraw.Draw(grid_layer)

grid_alpha = 120  # прозрачность линий (0–255)

# вертикальные линии
for c in range(COLS + 1):
    x = int(round(c * dx))
    draw.line([(x, 0), (x, height)], fill=(255, 255, 255, grid_alpha), width=1)

# горизонтальные линии
for r in range(ROWS + 1):
    y = int(round(r * dy))
    draw.line([(0, y), (width, y)], fill=(255, 255, 255, grid_alpha), width=1)

# выделение зоны деформации
r_top = int(round((ROW_TOP - 1) * dy))
r_bottom = int(round(ROW_BOTTOM * dy))
c_left = int(round((COL_LEFT - 1) * dx))
c_right = int(round(COL_RIGHT * dx))

draw.rectangle(
    [(c_left, r_top), (c_right, r_bottom)],
    outline=(255, 0, 0, 255),
    width=3
)

# наложение на исходное изображение
result = Image.alpha_composite(img, grid_layer)
result.convert("RGB").save(OUT_PATH, format="PNG")

print("Готово, сохранено в", OUT_PATH)
