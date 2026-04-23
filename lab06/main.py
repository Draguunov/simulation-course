import sys
import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from scipy.stats import chi2, norm
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QComboBox, QLabel, QSpinBox, QFrame, QHeaderView, QTabWidget,
    QMessageBox, QDoubleSpinBox
)

LIGHT_STYLE = """
    QMainWindow, QWidget { 
        background-color: #f5f5f7; 
        color: #1d1d1f; 
        font-family: 'Segoe UI', 'Helvetica Neue', sans-serif; 
    }
    QTabWidget::pane { border: 1px solid #d2d2d7; background: white; border-radius: 5px; }
    QTabBar::tab {
        background: #e5e5e7; padding: 10px 20px; border-top-left-radius: 5px; border-top-right-radius: 5px;
        margin-right: 2px;
    }
    QTabBar::tab:selected { background: white; border-bottom: 2px solid #0071e3; font-weight: bold; }

    QTableWidget { 
        background-color: white; border: 1px solid #d2d2d7; 
        gridline-color: #f2f2f2; selection-background-color: #e8f0fe; 
    }
    QHeaderView::section { 
        background-color: #fbfbfd; color: #86868b; 
        padding: 8px; border: 1px solid #d2d2d7; font-weight: bold;
    }

    QPushButton { 
        background-color: #0071e3; color: white; border: none; 
        border-radius: 8px; padding: 12px; font-weight: 600; 
    }
    QPushButton:hover { background-color: #0077ed; }
    QPushButton:pressed { background-color: #005bb7; }

    QSpinBox, QComboBox, QDoubleSpinBox { 
        background-color: white; border: 1px solid #d2d2d7; 
        border-radius: 6px; padding: 6px; selection-background-color: #0071e3; 
    }
    QLabel { color: #1d1d1f; }
"""


class StatCard(QFrame):
    def __init__(self, title):
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet("""
            QFrame { 
                background-color: white; border-radius: 12px; 
                border: 1px solid #d2d2d7; border-left: 5px solid #0071e3;
            }
        """)
        layout = QVBoxLayout(self)
        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setStyleSheet("color: #86868b; font-size: 11px; border: none; font-weight: bold;")
        self.val_lbl = QLabel("0.0000")
        self.val_lbl.setStyleSheet("color: #1d1d1f; font-size: 20px; font-weight: 700; border: none; margin: 4px 0;")
        self.status_lbl = QLabel("—")
        self.status_lbl.setStyleSheet("font-size: 11px; border: none;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.val_lbl)
        layout.addWidget(self.status_lbl)

    def update_val(self, value, error_pct=None, is_pass=None):
        self.val_lbl.setText(f"{value:.4f}")
        if error_pct is not None:
            self.status_lbl.setText(f"Погрешность: {error_pct:.2f}%")
            self.status_lbl.setStyleSheet(
                f"color: {'#248a3d' if error_pct < 5 else '#b38f00'}; border: none; font-weight: 500;"
            )
        if is_pass is not None:
            status_text = "ПРОЙДЕН ✅" if is_pass else "ОТКЛОНЕН ❌"
            self.status_lbl.setText(status_text)
            self.status_lbl.setStyleSheet(
                f"color: {'#248a3d' if is_pass else '#d70015'}; border: none; font-weight: bold;"
            )


def generate_discrete_manual(x, p, n):
    samples = []
    for _ in range(n):
        alpha = np.random.random()
        for xi, pi in zip(x, p):
            alpha -= pi
            if alpha <= 0:
                samples.append(xi)
                break
    return np.array(samples)


def box_muller_normal(n, mean=0.0, variance=1.0):
    sigma = math.sqrt(variance)
    u1 = np.random.rand(n)
    u2 = np.random.rand(n)
    u1 = np.maximum(u1, 1e-12)
    z = np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2)
    return mean + sigma * z


def relative_error(empirical, theoretical):
    if abs(theoretical) < 1e-12:
        return abs(empirical) * 100
    return abs(empirical - theoretical) / abs(theoretical) * 100


class ModernLabApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Моделирование случайных величин")
        self.resize(1300, 850)
        self.setStyleSheet(LIGHT_STYLE)
        self.series_ns = [10, 100, 1000, 10000]
        self.init_ui()

    def init_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        self.tab_d = QWidget()
        self.init_discrete_tab()
        self.tabs.addTab(self.tab_d, "Дискретные величины")

        self.tab_n = QWidget()
        self.init_normal_tab()
        self.tabs.addTab(self.tab_n, "Нормальное распределение")

    def init_discrete_tab(self):
        layout = QHBoxLayout(self.tab_d)

        side_panel = QVBoxLayout()
        side_panel.setContentsMargins(15, 15, 15, 15)
        side_panel.setSpacing(10)

        side_panel.addWidget(QLabel("<b>Настройки дискретной СВ</b>"))

        self.n_input = QSpinBox()
        self.n_input.setRange(10, 1000000)
        self.n_input.setValue(1000)
        side_panel.addWidget(QLabel("Размер выборки N:"))
        side_panel.addWidget(self.n_input)

        self.presets = QComboBox()
        self.presets.addItems(["Пустая таблица", "Равномерное", "Бернулли"])
        self.presets.currentIndexChanged.connect(self.load_preset)
        side_panel.addWidget(QLabel("Пресет:"))
        side_panel.addWidget(self.presets)

        self.table = QTableWidget(5, 3)
        self.table.setHorizontalHeaderLabels(["X", "P теор.", "P эмп."])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        side_panel.addWidget(self.table)

        self.btn_calc = QPushButton("Сгенерировать для выбранного N")
        self.btn_calc.clicked.connect(self.calculate_discrete)
        side_panel.addWidget(self.btn_calc)

        self.btn_series_d = QPushButton("Серия: 10, 100, 1000, 10000")
        self.btn_series_d.clicked.connect(self.calculate_discrete_series)
        side_panel.addWidget(self.btn_series_d)

        self.card_m = StatCard("Математическое ожидание")
        self.card_v = StatCard("Дисперсия")
        self.card_chi = StatCard("Критерий χ²")
        side_panel.addWidget(self.card_m)
        side_panel.addWidget(self.card_v)
        side_panel.addWidget(self.card_chi)
        side_panel.addStretch()

        self.fig_d, self.ax_d = plt.subplots(facecolor='white', tight_layout=True)
        self.canvas_d = FigureCanvas(self.fig_d)

        self.series_table_d = QTableWidget()
        self.series_table_d.setColumnCount(6)
        self.series_table_d.setHorizontalHeaderLabels([
            "N", "M эмп.", "D эмп.", "Ошибка M, %", "Ошибка D, %", "χ² / решение"
        ])
        self.series_table_d.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        right_panel = QVBoxLayout()
        right_panel.addWidget(self.canvas_d, 3)
        right_panel.addWidget(self.series_table_d, 2)

        layout.addLayout(side_panel, 1)
        layout.addLayout(right_panel, 2)

    def init_normal_tab(self):
        layout = QHBoxLayout(self.tab_n)

        side_panel = QVBoxLayout()
        side_panel.setContentsMargins(15, 15, 15, 15)

        side_panel.addWidget(QLabel("<b>Настройки нормальной СВ</b>"))

        self.mean_box = QDoubleSpinBox()
        self.mean_box.setRange(-1000.0, 1000.0)
        self.mean_box.setValue(0.0)
        self.mean_box.setDecimals(3)

        self.var_box = QDoubleSpinBox()
        self.var_box.setRange(0.001, 1000.0)
        self.var_box.setValue(1.0)
        self.var_box.setDecimals(3)

        self.n_norm = QSpinBox()
        self.n_norm.setRange(10, 1000000)
        self.n_norm.setValue(1000)

        side_panel.addWidget(QLabel("Среднее a:"))
        side_panel.addWidget(self.mean_box)
        side_panel.addWidget(QLabel("Дисперсия σ²:"))
        side_panel.addWidget(self.var_box)
        side_panel.addWidget(QLabel("Размер выборки N:"))
        side_panel.addWidget(self.n_norm)

        btn = QPushButton("Сгенерировать для выбранного N")
        btn.clicked.connect(self.calculate_normal)
        side_panel.addWidget(btn)

        btn_series = QPushButton("Серия: 10, 100, 1000, 10000")
        btn_series.clicked.connect(self.calculate_normal_series)
        side_panel.addWidget(btn_series)

        self.card_m_norm = StatCard("Математическое ожидание")
        self.card_v_norm = StatCard("Дисперсия")
        self.card_chi_norm = StatCard("Критерий χ²")
        side_panel.addWidget(self.card_m_norm)
        side_panel.addWidget(self.card_v_norm)
        side_panel.addWidget(self.card_chi_norm)
        side_panel.addStretch()

        self.fig_n, self.ax_n = plt.subplots(facecolor='white', tight_layout=True)
        self.canvas_n = FigureCanvas(self.fig_n)

        self.series_table_n = QTableWidget()
        self.series_table_n.setColumnCount(6)
        self.series_table_n.setHorizontalHeaderLabels([
            "N", "M эмп.", "D эмп.", "Ошибка M, %", "Ошибка D, %", "χ² / решение"
        ])
        self.series_table_n.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)

        right_panel = QVBoxLayout()
        right_panel.addWidget(self.canvas_n, 3)
        right_panel.addWidget(self.series_table_n, 2)

        layout.addLayout(side_panel, 1)
        layout.addLayout(right_panel, 2)

    def load_preset(self):
        idx = self.presets.currentIndex()
        self.table.setRowCount(0)
        data = []
        if idx == 1:
            data = [(i, 0.2) for i in range(1, 6)]
        elif idx == 2:
            data = [(0, 0.45), (1, 0.55)]

        for x, p in data:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.table.setItem(row, 0, QTableWidgetItem(str(x)))
            self.table.setItem(row, 1, QTableWidgetItem(str(p)))

    def read_discrete_data(self):
        rows = self.table.rowCount()
        x = []
        p = []

        for i in range(rows):
            item_x = self.table.item(i, 0)
            item_p = self.table.item(i, 1)
            if item_x is None or item_p is None:
                continue
            text_x = item_x.text().strip()
            text_p = item_p.text().strip()
            if not text_x or not text_p:
                continue
            x.append(float(text_x))
            p.append(float(text_p))

        if len(x) < 2:
            raise ValueError("Нужно задать хотя бы 2 значения.")

        p = np.array(p, dtype=float)
        x = np.array(x, dtype=float)

        if np.any(p < 0):
            raise ValueError("Вероятности не могут быть отрицательными.")

        total = p.sum()
        if total <= 0:
            raise ValueError("Сумма вероятностей должна быть больше 0.")

        if not np.isclose(total, 1.0):
            reply = QMessageBox.question(
                self,
                "Нормировка",
                f"Сумма вероятностей = {total:.6f}. Выполнить нормировку?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            if reply == QMessageBox.StandardButton.Yes:
                p = p / total
                for i, pi in enumerate(p):
                    self.table.setItem(i, 1, QTableWidgetItem(f"{pi:.6f}"))
            else:
                raise ValueError("Сумма вероятностей должна быть равна 1.")

        return x, p

    def calculate_discrete(self):
        try:
            n = self.n_input.value()
            x, p = self.read_discrete_data()

            samples = generate_discrete_manual(x, p, n)

            unique, counts = np.unique(samples, return_counts=True)
            obs_map = dict(zip(unique, counts))

            m_th = np.sum(x * p)
            d_th = np.sum((x ** 2) * p) - m_th ** 2
            m_emp = np.mean(samples)
            d_emp = np.var(samples)

            err_m = relative_error(m_emp, m_th)
            err_d = relative_error(d_emp, d_th)

            observed = np.array([obs_map.get(xi, 0) for xi in x], dtype=float)
            expected = n * p
            chi_stat = np.sum((observed - expected) ** 2 / expected)
            chi_crit = chi2.ppf(0.95, len(x) - 1)
            is_pass = chi_stat < chi_crit

            emp_probs = observed / n
            for i in range(len(x)):
                self.table.setItem(i, 2, QTableWidgetItem(f"{emp_probs[i]:.4f}"))

            self.card_m.update_val(m_emp, error_pct=err_m)
            self.card_v.update_val(d_emp, error_pct=err_d)
            self.card_chi.update_val(chi_stat, is_pass=is_pass)

            self.ax_d.clear()
            self.ax_d.bar(x - 0.15, p, width=0.3, label='Теоретические')
            self.ax_d.bar(x + 0.15, emp_probs, width=0.3, label='Эмпирические')
            self.ax_d.set_ylim(0, 1)
            self.ax_d.set_xlabel("Значения")
            self.ax_d.set_ylabel("Вероятность")
            self.ax_d.set_title(f"Сравнение распределений (N={n})")
            self.ax_d.grid(axis='y', linestyle='--', alpha=0.3)
            self.ax_d.legend()
            self.canvas_d.draw()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def calculate_discrete_series(self):
        try:
            x, p = self.read_discrete_data()
            self.series_table_d.setRowCount(len(self.series_ns))

            m_th = np.sum(x * p)
            d_th = np.sum((x ** 2) * p) - m_th ** 2

            for row, n in enumerate(self.series_ns):
                samples = generate_discrete_manual(x, p, n)
                m_emp = np.mean(samples)
                d_emp = np.var(samples)

                observed = np.array([np.sum(samples == xi) for xi in x], dtype=float)
                expected = n * p
                chi_stat = np.sum((observed - expected) ** 2 / expected)
                chi_crit = chi2.ppf(0.95, len(x) - 1)
                is_pass = chi_stat < chi_crit

                err_m = relative_error(m_emp, m_th)
                err_d = relative_error(d_emp, d_th)

                values = [
                    str(n),
                    f"{m_emp:.4f}",
                    f"{d_emp:.4f}",
                    f"{err_m:.2f}",
                    f"{err_d:.2f}",
                    f"{chi_stat:.4f} / {'принят' if is_pass else 'откл.'}"
                ]
                for col, value in enumerate(values):
                    self.series_table_d.setItem(row, col, QTableWidgetItem(value))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def calculate_normal(self):
        try:
            n = self.n_norm.value()
            mean = self.mean_box.value()
            variance = self.var_box.value()
            sigma = math.sqrt(variance)

            samples = box_muller_normal(n, mean, variance)
            m_emp = np.mean(samples)
            d_emp = np.var(samples)

            err_m = relative_error(m_emp, mean)
            err_d = relative_error(d_emp, variance)

            counts, edges = np.histogram(samples, bins='sturges')
            probs = norm.cdf(edges[1:], loc=mean, scale=sigma) - norm.cdf(edges[:-1], loc=mean, scale=sigma)
            expected = n * probs
            mask = expected > 0
            chi_stat = np.sum((counts[mask] - expected[mask]) ** 2 / expected[mask])
            df = np.sum(mask) - 1
            chi_crit = chi2.ppf(0.95, df) if df > 0 else np.nan
            is_pass = chi_stat < chi_crit if df > 0 else False

            self.card_m_norm.update_val(m_emp, error_pct=err_m)
            self.card_v_norm.update_val(d_emp, error_pct=err_d)
            self.card_chi_norm.update_val(chi_stat, is_pass=is_pass)

            self.ax_n.clear()
            self.ax_n.hist(samples, bins=edges, density=True, color='#0071e3', alpha=0.15, edgecolor='#0071e3')
            x_axis = np.linspace(min(samples), max(samples), 300)
            self.ax_n.plot(x_axis, norm.pdf(x_axis, loc=mean, scale=sigma),
                           color='#d70015', lw=2, label='Теоретическая плотность')
            self.ax_n.set_title(f"Анализ нормального распределения (N={n})")
            self.ax_n.grid(axis='both', linestyle='--', alpha=0.2)
            self.ax_n.legend()
            self.canvas_n.draw()

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def calculate_normal_series(self):
        try:
            mean = self.mean_box.value()
            variance = self.var_box.value()
            sigma = math.sqrt(variance)
            self.series_table_n.setRowCount(len(self.series_ns))

            for row, n in enumerate(self.series_ns):
                samples = box_muller_normal(n, mean, variance)
                m_emp = np.mean(samples)
                d_emp = np.var(samples)

                err_m = relative_error(m_emp, mean)
                err_d = relative_error(d_emp, variance)

                counts, edges = np.histogram(samples, bins='sturges')
                probs = norm.cdf(edges[1:], loc=mean, scale=sigma) - norm.cdf(edges[:-1], loc=mean, scale=sigma)
                expected = n * probs
                mask = expected > 0
                chi_stat = np.sum((counts[mask] - expected[mask]) ** 2 / expected[mask])
                df = np.sum(mask) - 1
                chi_crit = chi2.ppf(0.95, df) if df > 0 else np.nan
                is_pass = chi_stat < chi_crit if df > 0 else False

                values = [
                    str(n),
                    f"{m_emp:.4f}",
                    f"{d_emp:.4f}",
                    f"{err_m:.2f}",
                    f"{err_d:.2f}",
                    f"{chi_stat:.4f} / {'принят' if is_pass else 'откл.'}"
                ]
                for col, value in enumerate(values):
                    self.series_table_n.setItem(row, col, QTableWidgetItem(value))

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ModernLabApp()
    window.show()
    sys.exit(app.exec())