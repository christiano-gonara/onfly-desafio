"""Apoio aos testes adicionais: executa o CLI sem exigir código de saída 0.

`helpers.run_cli` (fornecido) só cobre o caminho de sucesso; aqui também é possível testar os
códigos de saída 1 e 2 e usar arquivos de entrada arbitrários.
"""

from __future__ import annotations

import csv
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from helpers import BASE, COLUMNS, PROJECT_ROOT, SRC_DIR

DEFAULT_RATES = "currency,rate_to_brl\nBRL,1.000000\nUSD,5.420000\nEUR,5.880000\n"


@dataclass
class CliResult:
    returncode: int
    stdout: str
    stderr: str
    output_path: Path

    def report(self) -> dict:
        assert self.returncode == 0, self.stderr
        return json.loads(self.output_path.read_text(encoding="utf-8"))


def write_reservations(path: Path, rows: list[dict[str, str]]) -> Path:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows({**BASE, **row} for row in rows)
    return path


def run(args: list[str], output_path: Path) -> CliResult:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SRC_DIR) + os.pathsep + environment.get("PYTHONPATH", "")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    process = subprocess.run(
        [sys.executable, "-m", "onfly_report", *args],
        cwd=str(PROJECT_ROOT),
        env=environment,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return CliResult(process.returncode, process.stdout, process.stderr, output_path)


def run_rows(
    tmp_path: Path,
    rows: list[dict[str, str]],
    top: str | int | None = None,
    rates: str = DEFAULT_RATES,
) -> CliResult:
    input_path = write_reservations(tmp_path / "reservas.csv", rows)
    rates_path = tmp_path / "rates.csv"
    rates_path.write_text(rates, encoding="utf-8")
    output_path = tmp_path / "report.json"
    args = ["--input", str(input_path), "--rates", str(rates_path), "--output", str(output_path)]
    if top is not None:
        args += ["--top", str(top)]
    return run(args, output_path)


def run_files(tmp_path: Path, input_path: Path, rates_path: Path) -> CliResult:
    output_path = tmp_path / "report.json"
    return run(
        ["--input", str(input_path), "--rates", str(rates_path), "--output", str(output_path)],
        output_path,
    )
