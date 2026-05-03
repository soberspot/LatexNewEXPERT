import matplotlib.pyplot as plt
import numpy as np

# Список карт, которые хотим посмотреть
cmap_list = [
    'viridis', 'plasma', 'inferno', 'magma',  # Perceptually Uniform
    'Greys', 'Blues', 'Reds', 'Oranges',      # Sequential
    'hot', 'afmhot', 'bone', 'copper',        # Другие Sequential
    'coolwarm', 'seismic', 'bwr',             # Diverging (расходящиеся)
    'jet', 'rainbow'                          # Miscellaneous (яркие, но часто искажают восприятие)
]

gradient = np.linspace(0, 1, 256)
gradient = np.vstack((gradient, gradient))

fig, axes = plt.subplots(nrows=len(cmap_list), figsize=(8, len(cmap_list) * 0.5))
fig.subplots_adjust(top=0.95, bottom=0.01, left=0.2, right=0.99)

for ax, name in zip(axes, cmap_list):
    ax.imshow(gradient, aspect='auto', cmap=name)
    ax.text(-0.01, 0.5, name, va='center', ha='right', fontsize=12, transform=ax.transAxes)
    ax.set_axis_off()

plt.show()