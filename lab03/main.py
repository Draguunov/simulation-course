import tkinter as tk
from tkinter import ttk
import numpy as np
import random

EMPTY = 0
ASH = 1
TREE_YOUNG = 2
TREE_MEDIUM = 3
TREE_OLD = 4
BURNING = 5
WATER = 6

# Darker palette
COLORS = {
    EMPTY: "#1f2329",
    ASH: "#4b4f57",
    TREE_YOUNG: "#2ecc71",
    TREE_MEDIUM: "#1f8f4a",
    TREE_OLD: "#145a32",
    BURNING: "#e74c3c",
    WATER: "#2980b9"
}

WIND_DIRECTIONS = {
    "Нет": (0, 0),
    "Север ↑": (-1, 0),
    "Юг ↓": (1, 0),
    "Восток →": (0, 1),
    "Запад ←": (0, -1),
}
class ForestFireWindModel:
    def __init__(self, root):
        self.root = root
        self.root.title("Клеточный автомат: лесной пожар")

        # Grid settings
        self.grid_size = 50
        self.canvas_size_px = 600
        self.cell_px = self.canvas_size_px // self.grid_size

        self.grid = np.zeros((self.grid_size, self.grid_size), dtype=np.uint8)

        # Probabilities
        self.age_prob = 0.005          # aging: young->medium->old
        self.ash_clear_prob = 0.05     # ash -> empty
        self.wind_dir = (0, 0)         # (wy, wx)

        self.running = False

        self._build_ui()
        self._draw_full_grid()

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        legend_frame = ttk.Frame(main)
        legend_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 12))

        canvas_frame = ttk.Frame(main)
        canvas_frame.pack(side=tk.LEFT)

        controls = ttk.Frame(main)
        controls.pack(side=tk.RIGHT, fill=tk.Y, padx=(12, 0))

        ttk.Label(legend_frame, text="Легенда", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        self._legend_item(legend_frame, "Пусто", EMPTY)
        self._legend_item(legend_frame, "Пепел", ASH)
        self._legend_item(legend_frame, "Дерево (молод.)", TREE_YOUNG)
        self._legend_item(legend_frame, "Дерево (сред.)", TREE_MEDIUM)
        self._legend_item(legend_frame, "Дерево (стар.)", TREE_OLD)
        self._legend_item(legend_frame, "Огонь", BURNING)
        self._legend_item(legend_frame, "Вода", WATER)

        ttk.Label(
            legend_frame,
            text="\nМышь:\nЛКМ — огонь\nПКМ — вода",
            foreground="#555"
        ).pack(anchor="w", pady=(8, 0))

        self.canvas = tk.Canvas(
            canvas_frame,
            width=self.canvas_size_px,
            height=self.canvas_size_px,
            bg=COLORS[EMPTY],
            highlightthickness=0
        )
        self.canvas.pack()

        # Mouse: LMB = fire, RMB = water
        self.canvas.bind("<Button-1>", self.paint_fire)
        self.canvas.bind("<B1-Motion>", self.paint_fire)
        self.canvas.bind("<Button-3>", self.paint_water)
        self.canvas.bind("<B3-Motion>", self.paint_water)

        # --- Controls (right) ---
        ttk.Label(controls, text="Настройки", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 8))

        self.btn_start = ttk.Button(controls, text="Старт", command=self.toggle)
        self.btn_start.pack(fill=tk.X, pady=5)

        ttk.Button(controls, text="Очистить поле", command=self.clear_all).pack(fill=tk.X)

        ttk.Label(controls, text="\nВероятность роста (p):").pack(anchor="w")
        self.grow_slider = ttk.Scale(controls, from_=0.0, to=0.05, value=0.01)
        self.grow_slider.pack(fill=tk.X)

        ttk.Label(controls, text="Вероятность молнии (f):").pack(anchor="w")
        self.lightning_slider = ttk.Scale(controls, from_=0.0, to=0.005, value=0.0005)
        self.lightning_slider.pack(fill=tk.X)

        ttk.Label(controls, text="\nНаправление ветра:", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(10, 5))
        self.wind_var = tk.StringVar(value="Нет")

        for text, vec in WIND_DIRECTIONS.items():
            ttk.Radiobutton(
                controls,
                text=text,
                variable=self.wind_var,
                value=text,
                command=lambda v=vec: self.set_wind(v)
            ).pack(anchor=tk.W)

    def _legend_item(self, parent, text, state):
        row = ttk.Frame(parent)
        row.pack(anchor="w", pady=1)

        swatch = tk.Canvas(row, width=14, height=14, highlightthickness=0)
        swatch.create_rectangle(0, 0, 14, 14, fill=COLORS[state], outline="")
        swatch.pack(side="left", padx=(0, 6))

        ttk.Label(row, text=text).pack(side="left")

    # ---------------- Controls ----------------
    def set_wind(self, vec):
        self.wind_dir = vec

    def toggle(self):
        self.running = not self.running
        self.btn_start.config(text="Стоп" if self.running else "Старт")
        if self.running:
            self.loop()

    def clear_all(self):
        self.running = False
        self.btn_start.config(text="Старт")
        self.grid.fill(EMPTY)
        self._draw_full_grid()

    # ---------------- Mouse painting ----------------
    def _cell_from_event(self, event):
        x = event.x // self.cell_px
        y = event.y // self.cell_px
        if 0 <= x < self.grid_size and 0 <= y < self.grid_size:
            return int(x), int(y)
        return None

    def paint_fire(self, event):
        cell = self._cell_from_event(event)
        if not cell:
            return
        x, y = cell
        # Fire can be placed only on trees (optional rule; can remove if needed)
        if self.grid[y, x] in (TREE_YOUNG, TREE_MEDIUM, TREE_OLD):
            self.grid[y, x] = BURNING
            self._draw_cell(x, y)

    def paint_water(self, event):
        cell = self._cell_from_event(event)
        if not cell:
            return
        x, y = cell
        self.grid[y, x] = WATER
        self._draw_cell(x, y)

    # ---------------- Drawing ----------------
    def _draw_cell(self, x, y):
        self.canvas.create_rectangle(
            x * self.cell_px, y * self.cell_px,
            (x + 1) * self.cell_px, (y + 1) * self.cell_px,
            fill=COLORS[int(self.grid[y, x])],
            outline=""
        )

    def _draw_full_grid(self):
        self.canvas.delete("all")
        for y in range(self.grid_size):
            for x in range(self.grid_size):
                if self.grid[y, x] != EMPTY:
                    self._draw_cell(x, y)

    # ---------------- Simulation step ----------------
    def loop(self):
        if not self.running:
            return

        new_grid = self.grid.copy()

        p_grow = float(self.grow_slider.get())
        f_lightning = float(self.lightning_slider.get())
        wy, wx = self.wind_dir

        for y in range(self.grid_size):
            for x in range(self.grid_size):
                state = int(self.grid[y, x])

                # WATER: stays water (blocks everything)
                if state == WATER:
                    continue

                # ASH -> EMPTY with some probability
                if state == ASH:
                    if random.random() < self.ash_clear_prob:
                        new_grid[y, x] = EMPTY

                # EMPTY -> TREE_YOUNG with probability p
                elif state == EMPTY:
                    if random.random() < p_grow:
                        new_grid[y, x] = TREE_YOUNG

                # TREE (any age): can age, can ignite from lightning or neighbors
                elif state in (TREE_YOUNG, TREE_MEDIUM, TREE_OLD):
                    # Aging
                    if state == TREE_YOUNG and random.random() < self.age_prob:
                        new_grid[y, x] = TREE_MEDIUM
                        state = TREE_MEDIUM
                    elif state == TREE_MEDIUM and random.random() < self.age_prob:
                        new_grid[y, x] = TREE_OLD
                        state = TREE_OLD

                    # Lightning
                    if random.random() < f_lightning:
                        new_grid[y, x] = BURNING
                    else:
                        ignited = False

                        # Check 8 neighbors
                        for dy in (-1, 0, 1):
                            for dx in (-1, 0, 1):
                                if dy == 0 and dx == 0:
                                    continue

                                ny, nx = y + dy, x + dx
                                if 0 <= ny < self.grid_size and 0 <= nx < self.grid_size:
                                    if self.grid[ny, nx] == BURNING:
                                        # Base ignition chance depends on tree age
                                        if state == TREE_YOUNG:
                                            chance = 0.2
                                        elif state == TREE_MEDIUM:
                                            chance = 0.5
                                        else:
                                            chance = 0.8

                                        # Wind effect:
                                        # If neighbor is upwind (wind pushes from neighbor to current cell) -> increase chance
                                        if (wy == -dy and wy != 0) or (wx == -dx and wx != 0):
                                            chance += 0.5
                                        # If wind pushes from current cell to neighbor -> decrease chance
                                        elif (wy == dy and wy != 0) or (wx == dx and wx != 0):
                                            chance -= 0.15

                                        # Clamp chance to [0..1]
                                        chance = max(0.0, min(1.0, chance))

                                        if random.random() < chance:
                                            ignited = True
                                            break
                            if ignited:
                                break

                        if ignited:
                            new_grid[y, x] = BURNING

                # BURNING -> ASH
                elif state == BURNING:
                    new_grid[y, x] = ASH

        self.grid = new_grid
        self._draw_full_grid()
        self.root.after(100, self.loop)

if __name__ == "__main__":
    root = tk.Tk()
    app = ForestFireWindModel(root)
    root.mainloop()