import logging
import sys
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from typing_extensions import Literal

from findex.index import open_index, build_index
from findex.scoring import BM25, TfIdf
from findex.search import search
from findex.models import SearchResult

app = typer.Typer(help="Findex Search Engine CLI")
console = Console()
err_console = Console(stderr=True)


def setup_logging(verbose: int) -> None:
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr
    )


@app.callback()
def main(
        verbose: int = typer.Option(0, "--verbose", "-v", count=True,
                                    help="Increase verbosity (-v for INFO, -vv for DEBUG)")
) -> None:
    setup_logging(verbose)


@app.command("index")
def cmd_index(
        corpus_dir: Path = typer.Argument(..., help="Path to text corpus directory"),
        out: Path = typer.Option(Path("index.bin"), "--out", "-o", help="Output index file path"),
        workers: int = typer.Option(4, "--workers", "-w", help="Number of workers"),
        executor: Literal["serial", "threads", "processes"] = typer.Option("processes", "--executor", "-e",
                                                                           help="Executor type")
) -> None:
    """Побудова та збереження індексу з паралелізмом."""
    try:
        logging.info(f"Побудова індексу: {executor} x {workers}")

        try:
            gil_status = "Вимкнено" if not sys._is_gil_enabled() else "Увімкнено"
        except AttributeError:
            gil_status = "Увімкнено (стандартний Python)"
        logging.info(f"Статус GIL: {gil_status}")

        with console.status(f"[bold green]Будується індекс ({executor}, {workers} робітників)..."):
            metrics = build_index(corpus_dir, out, executor_type=executor, workers=workers)

        console.print(f"[bold green]✓ Індекс успішно збережено у {out}[/bold green]")
        console.print(f" • Wall time: {metrics['wall_time']:.3f} s")
        console.print(f" • CPU time: {metrics['cpu_time']:.3f} s")
        console.print(f" • Merge time: {metrics['merge_time']:.3f} s")
        console.print(f" • Peak RSS: {metrics['rss_mb']:.2f} MB")
        console.print(f" • GIL Status: {gil_status}")
    except Exception as e:
        err_console.print(f"[bold red]Помилка побудови індексу:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("search")
def cmd_search(
        index_file: Path = typer.Argument(..., help="Path to index.bin file"),
        query: str = typer.Argument(..., help="Search query string"),
        scorer_type: Literal["bm25", "tfidf"] = typer.Option("bm25", "--scorer", "-s", help="Scoring algorithm"),
        top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results"),
        json_output: bool = typer.Option(False, "--json", help="Output results in JSON format to stdout"),
) -> None:
    try:
        if not index_file.exists():
            raise FileNotFoundError(f"Файл індексу не знайдено: {index_file}")

        logging.debug(f"Завантаження індексу з {index_file}")
        with open_index(index_file) as idx:
            scorer = BM25() if scorer_type == "bm25" else TfIdf()
            corpus_path = index_file.parent / "data" / "corpus"

            logging.info(f"Виконання запиту: '{query}' з алгоритмом {scorer_type}")
            results: list[SearchResult] = search(query, idx, scorer, corpus_path, top_k=top_k)

            if json_output:
                import json
                out_data = [{"doc_id": r.doc_id, "name": r.name, "score": r.score, "snippet": r.snippet} for r in
                            results]
                sys.stdout.write(json.dumps(out_data, ensure_ascii=False, indent=2) + "\n")
                return

            table = Table(title=f"Результати пошуку: '{query}' ({scorer_type.upper()})")
            table.add_column("Score", style="cyan", justify="right")
            table.add_column("Document", style="magenta")
            table.add_column("Snippet", style="green")

            for r in results:
                table.add_row(f"{r.score:.4f}", r.name, r.snippet)
            console.print(table)

    except Exception as e:
        err_console.print(f"[bold red]Помилка пошуку:[/bold red] {e}")
        raise typer.Exit(code=1)


@app.command("stats")
def cmd_stats(
        index_file: Path = typer.Argument(..., help="Path to index.bin file")
) -> None:
    try:
        if not index_file.exists():
            raise FileNotFoundError(f"Файл індексу не знайдено: {index_file}")

        with open_index(index_file) as idx:
            console.print(f"[bold]Статистика індексу ({index_file}):[/bold]")
            console.print(f" • Кількість документів: {idx.num_docs}")
            console.print(f" • Розмір словника (vocab size): {len(idx)}")
            console.print(f" • Середня довжина документа: {idx.avg_doc_length:.2f} слів")
    except Exception as e:
        err_console.print(f"[bold red]Помилка читання статистики:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()