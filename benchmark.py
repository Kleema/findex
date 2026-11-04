import os
import statistics
import matplotlib.pyplot as plt
from findex.index import build_index
from pathlib import Path


def run_benchmarks() -> None:
    corpus = Path("data/corpus")
    out_file = Path("index.bin")

    if not corpus.exists():
        print(f"Папка {corpus} не знайдена!")
        return

    cpu_count = os.cpu_count() or 4
    worker_counts = sorted(list(set([1, 2, 4, 8, cpu_count])))

    results = {}
    baseline_wall = None

    print(f"Початок бенчмарку (CPU: {cpu_count} ядер)...")
    for w in worker_counts:
        print(f"\nТестування {w} worker(s)...")
        runs_wall, runs_cpu, runs_rss, runs_merge = [], [], [], []

        for _ in range(3):
            metrics = build_index(corpus, out_file, "processes", w)
            runs_wall.append(metrics["wall_time"])
            runs_cpu.append(metrics["cpu_time"])
            runs_rss.append(metrics["rss_mb"])
            runs_merge.append(metrics["merge_time"])

        med_wall = statistics.median(runs_wall)
        if baseline_wall is None:
            baseline_wall = med_wall

        results[w] = {
            "wall": med_wall,
            "cpu": statistics.median(runs_cpu),
            "rss": statistics.median(runs_rss),
            "merge": statistics.median(runs_merge),
            "speedup": baseline_wall / med_wall
        }
        print(f"Медіана Wall: {med_wall:.2f}s, Speedup: {results[w]['speedup']:.2f}x")

    workers = list(results.keys())
    speedups = [results[w]["speedup"] for w in workers]

    plt.figure(figsize=(8, 5))
    plt.plot(workers, speedups, marker='o', label='Реальне прискорення (ProcessPool)')
    plt.plot(workers, workers, linestyle='--', color='gray', label='Ідеальний лінійний ріст')

    plt.title('Прискорення індексації від кількості воркерів')
    plt.xlabel('Кількість воркерів')
    plt.ylabel('Прискорення (Speedup)')
    plt.xticks(workers)
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.savefig('speedup.png')
    print("\nГрафік збережено у speedup.png")

    print("\nМетрики для README.md:")
    print("| Workers | Wall Time (s) | CPU Time (s) | RSS (MB) | Merge Time (s) | Speedup |")
    print("|---------|---------------|--------------|----------|----------------|---------|")
    for w, m in results.items():
        print(f"| {w} | {m['wall']:.3f} | {m['cpu']:.3f} | {m['rss']:.1f} | {m['merge']:.3f} | {m['speedup']:.2f}x |")


if __name__ == "__main__":
    run_benchmarks()