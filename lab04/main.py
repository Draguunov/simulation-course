import random
import time

class MultiplicativeCongruentialGenerator:
    """
    Мультипликативный конгруэнтный генератор (MCG).
    Реализует формулу: X_{n+1} = (a * X_n) mod m.
    Параметры выбраны по минимальному стандарту Park–Miller:
        a = 16807, m = 2^31 - 1 (простое число Мерсенна).
    """
    def __init__(self, seed=None):
        self.a = 16807
        self.m = 2**31 - 1
        if seed is None:
            # Используем текущее время для инициализации, если seed не задан
            seed = int(time.time() * 1e9) % self.m
        self.state = seed % self.m

    def random(self):
        """Возвращает следующее псевдослучайное число в интервале [0, 1)."""
        self.state = (self.a * self.state) % self.m
        return self.state / self.m


def compute_statistics(rng_func, n):
    """
    Вычисляет выборочное среднее и смещённую дисперсию (population variance)
    для n чисел, полученных вызовом rng_func.
    """
    values = [rng_func() for _ in range(n)]
    mean = sum(values) / n
    variance = sum((x - mean) ** 2 for x in values) / n
    return mean, variance


def main():
    # Ввод размера выборки (по умолчанию 100 000)
    try:
        n = int(input("Введите размер выборки (по умолчанию 100000): ") or 100000)
        if n <= 0:
            raise ValueError
    except ValueError:
        n = 100000
        print("Используется размер выборки по умолчанию: 100000")

    # Теоретические значения для равномерного распределения на [0,1]
    theo_mean = 0.5
    theo_var = 1.0 / 12.0

    # 1. Реализованный генератор (MCG)
    fixed_seed = 123456789
    my_rng = MultiplicativeCongruentialGenerator(seed=fixed_seed)
    my_mean, my_var = compute_statistics(my_rng.random, n)

    # 2. Встроенный генератор Python
    random.seed(fixed_seed)   # для сопоставимости результатов
    builtin_mean, builtin_var = compute_statistics(random.random, n)

    # Вывод результатов
    print("\n" + "=" * 60)
    print(f"Сравнение генераторов (размер выборки: {n})")
    print("=" * 60)
    print(f"{'Генератор':<20} | {'Среднее':<12} | {'Дисперсия':<12} | {'Погрешность ср.':<15} | {'Погрешность дисп.':<15}")
    print("-" * 80)

    print(f"{'Теоретическое':<20} | {theo_mean:<12.6f} | {theo_var:<12.6f} | {'-':<15} | {'-':<15}")

    print(f"{'MCG (Park–Miller)':<20} | {my_mean:<12.6f} | {my_var:<12.6f} | "
          f"{abs(my_mean - theo_mean):<15.6e} | {abs(my_var - theo_var):<15.6e}")

    print(f"{'Python random':<20} | {builtin_mean:<12.6f} | {builtin_var:<12.6f} | "
          f"{abs(builtin_mean - theo_mean):<15.6e} | {abs(builtin_var - theo_var):<15.6e}")

if __name__ == "__main__":
    main()