import sys
import json
from pathlib import Path
from typing import Literal
import typer
from rich.console import Console
from rich.table import Table

from findex.index import open_index, Index
from findex.search import search
from findex.scoring import BM25, TfIdf

app = typer.Typer(help="Findex search engine CLI")
console = Console()
err_console = Console(stderr=True)


@app.command("search")
def cmd_search(
        index_file: Path = typer.Argument(..., help="Path to index.bin file"),
        query: str = typer.Argument(..., help="Search query string"),
        scorer_type: Literal["bm25", "tfidf"] = typer.Option("bm25", "--scorer", "-s", help="Scoring algorithm"),
        top_k: int = typer.Option(5, "--top-k", "-k", help="Number of results"),
        json_output: bool = typer.Option(False, "--json", help="Output results in JSON format")
) -> None:
    try:
        if not index_file.exists():
            err_console.print(f"[bold red]Файл індексу не знайдено:[/bold red] {index_file}")
            raise typer.Exit(code=1)

        with open_index(index_file) as idx:
            scorer = BM25() if scorer_type == "bm25" else TfIdf()
            corpus_path = index_file.parent / "data" / "corpus"
            results = search(query, idx, scorer, corpus_path, top_k=top_k)

            if json_output:
                out_data = [{"doc_id": r.doc_id, "name": r.name, "score": r.score} for r in results]
                sys.stdout.write(json.dumps(out_data, ensure_ascii=False) + "\n")
                return

            table = Table(title=f"Результати пошуку: '{query}'")
            table.add_column("Score", style="cyan")
            table.add_column("Document", style="magenta")
            table.add_column("Snippet")

            for r in results:
                table.add_row(f"{r.score:.4f}", r.name, r.snippet)

            console.print(table)
    except typer.Exit:
        raise
    except Exception as e:
        err_console.print(f"[bold red]Помилка:[/bold red] {e}")
        raise typer.Exit(code=1)


if __name__ == "__main__":
    app()