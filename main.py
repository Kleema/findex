from findex.stats import gather_stats_lazy, gather_stats_greedy

if __name__ == "__main__":
    corpus = "data/corpus"  # Покладіть сюди кілька .txt файлів (книг)

    print("=== Запуск Лінивої версії ===")
    lazy_stats = gather_stats_lazy(corpus)
    print(lazy_stats)

    print("\n=== Запуск Жадібної версії ===")
    greedy_stats = gather_stats_greedy(corpus)
    print(greedy_stats)