import logging
import sys
import json
import time
import asyncio
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.live import Live
from typing_extensions import Literal

from findex.index import open_index, build_index
from findex.scoring import BM25, TfIdf
from findex.search import search
from findex.models import SearchResult
from findex.crawler import crawl

app = typer.Typer(help="Findex Search Engine CLI")
console = Console()
err_console = Console(stderr=True)


def setup_logging(verbose: int, log_file: str | None = None) -> None:
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    handlers = [logging.StreamHandler(sys.stderr)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=handlers
    )


@app.callback()
def main(
        verbose: int = typer.Option(0, "--verbose", "-v", count=True, help="Increase verbosity")
) -> None:
    setup_logging(verbose)


@app.command("crawl")
def cmd_crawl(
        start_url: str = typer.Argument(..., help="Початкова URL адреса"),
        max_pages: int = typer.Option(200, "--max-pages", "-m", help="Максимальна кількість сторінок"),
        concurrency: int = typer.Option(5, "--concurrency", "-c", help="Кількість одночасних запитів"),
        out_dir: Path = typer.Option(Path("data/corpus"), "--out", "-o", help="Папка для збереження jsonl"),
) -> None:
    """Асинхронний збір сторінок з Інтернету (Crawler)."""
    setup_logging(1, log_file="crawl.log")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "crawled.jsonl"

    async def run_crawler():
        start_time = time.time()
        pages = 0

        def generate_table():
            t = Table(title="Статус Краулера")
            t.add_column("Зібрано сторінок", justify="right")
            t.add_column("Швидкість", justify="right")
            t.add_column("У черзі", justify="right")
            t.add_column("Активні запити", justify="right")

            elapsed = time.time() - start_time
            rate = pages / elapsed if elapsed > 0 else 0
            t.add_row(str(pages), f"{rate:.1f} стор/с", "-", "-")
            return t

        with open(out_file, 'w', encoding='utf-8') as f:
            with Live(generate_table(), refresh_per_second=4) as live:
                async for doc in crawl(start_url, max_pages, concurrency):
                    pages += 1

                    json_doc = {"url": doc["url"], "text": doc["text"]}
                    f.write(json.dumps(json_doc, ensure_ascii=False) + "\n")
                    f.flush()

                    elapsed = time.time() - start_time
                    rate = pages / elapsed if elapsed > 0 else 0

                    t = Table(title="Статус Краулера")
                    t.add_column("Зібрано", justify="right", style="green")
                    t.add_column("Швидкість", justify="right", style="cyan")
                    t.add_column("У черзі", justify="right", style="yellow")
                    t.add_column("Активні", justify="right", style="magenta")
                    t.add_row(str(pages), f"{rate:.1f} стор/с", str(doc.get("queue_size", 0)),
                              str(doc.get("active", 0)))
                    live.update(t)

        console.print(f"\n[bold green]✓ Зібрано {pages} сторінок у {out_file}[/bold green]")

    try:
        asyncio.run(run_crawler())
    except KeyboardInterrupt:
        console.print("\n[bold red]Краулер зупинено користувачем.[/bold red]")


# (Команди cmd_index, cmd_search, cmd_stats залишаються без змін з попередньої версії)
@app.command("index")
def cmd_index(
        corpus_dir: Path = typer.Argument(..., help="Path to text corpus directory"),
        out: Path = typer.Option(Path("index.bin"), "--out", "-o", help="Output index file path"),
        workers: int = typer.Option(4, "--workers", "-w", help="Number of workers"),
        executor: Literal["serial", "threads", "processes"] = typer.Option("processes", "--executor", "-e",
                                                                           help="Executor type")
) -> None:
    try:
        with console.status(f"[bold green]Будується індекс ({executor}, {workers} робітників)..."):
            metrics = build_index(corpus_dir, out, executor_type=executor, workers=workers)
        console.print(f"[bold green]✓ Індекс успішно збережено у {out}[/bold green]")
        console.print(f" • Wall time: {metrics['wall_time']:.3f} s")
    except Exception as e:
        err_console.print(f"[bold red]Помилка побудови індексу:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("search")
def cmd_search(
        index_file: Path = typer.Argument(..., help="Path to index.bin file"),
        query: str = typer.Argument(..., help="Search query string"),
        scorer_type: Literal["bm25", "tfidf"] = typer.Option("bm25", "--scorer", "-s", help="Scoring algorithm"),
        top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results"),
        json_output: bool = typer.Option(False, "--json", help="Output results in JSON format")
) -> None:
    try:
        with open_index(index_file) as idx:
            scorer = BM25() if scorer_type == "bm25" else TfIdf()
            corpus_path = index_file.parent / "data" / "corpus"
            results = search(query, idx, scorer, corpus_path, top_k=top_k)

            if json_output:
                sys.stdout.write(
                    json.dumps([{"doc_id": r.doc_id, "name": r.name, "score": r.score} for r in results]) + "\n")
                return

            table = Table(title=f"Результати пошуку: '{query}'")
            table.add_column("Score", style="cyan");
            table.add_column("Document", style="magenta");
            table.add_column("Snippet")
            for r in results: table.add_row(f"{r.score:.4f}", r.name, r.snippet)
            console.print(table)
    except Exception as e:
        err_console.print(f"[bold red]Помилка:[/bold red] {e}")


if __name__ == "__main__":
    app()