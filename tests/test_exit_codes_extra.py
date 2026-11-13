"""Testes adicionais: códigos de saída e validação defensiva da entrada."""

import pytest
from cli_support import run, run_files, run_rows


@pytest.mark.parametrize("top", ["0", "-1", "abc"])
def test_invalid_top_exits_2(tmp_path, top):
    result = run_rows(tmp_path, [{}], top=top)
    assert result.returncode == 2
    assert not result.output_path.exists()


def test_missing_required_argument_exits_2(tmp_path):
    result = run(["--rates", "data/taxas_cambio.csv"], tmp_path / "report.json")
    assert result.returncode == 2


def test_missing_input_file_exits_2(tmp_path):
    rates = tmp_path / "rates.csv"
    rates.write_text("currency,rate_to_brl\nBRL,1\n", encoding="utf-8")
    result = run_files(tmp_path, tmp_path / "nao-existe.csv", rates)
    assert result.returncode == 2
    assert "não encontrado" in result.stderr


def test_missing_column_exits_2(tmp_path):
    input_path = tmp_path / "reservas.csv"
    input_path.write_text("reservation_id,hotel_id\nR-1,H01\n", encoding="utf-8")
    rates = tmp_path / "rates.csv"
    rates.write_text("currency,rate_to_brl\nBRL,1\n", encoding="utf-8")
    result = run_files(tmp_path, input_path, rates)
    assert result.returncode == 2
    assert "colunas obrigatórias ausentes" in result.stderr


@pytest.mark.parametrize(
    ("row", "message"),
    [
        ({"currency": "GBP"}, "moeda sem taxa de câmbio"),
        ({"status": "PENDING"}, "status desconhecido"),
        ({"rooms": "0"}, "rooms deve ser >= 1"),
        ({"checkin_date": "2025-01-10", "checkout_date": "2025-01-10"}, "deve ser posterior"),
        ({"checkin_date": "2025-01-10", "checkout_date": "2025-01-09"}, "deve ser posterior"),
        ({"checkin_date": "10/01/2025"}, "inválida"),
        ({"amount": "abc"}, "inválida"),
    ],
)
def test_invalid_row_exits_2_with_line_number(tmp_path, row, message):
    result = run_rows(tmp_path, [{"reservation_id": "R-1"}, {"reservation_id": "R-2", **row}])
    assert result.returncode == 2, result.stderr
    assert message in result.stderr
    assert "linha 3" in result.stderr  # cabeçalho = linha 1; segunda reserva = linha 3
    assert not result.output_path.exists()


def test_lowercase_currency_is_normalized_like_rates(tmp_path):
    summary = run_rows(tmp_path, [{"currency": "usd", "amount": "100.00"}]).report()["summary"]
    assert summary["total_amount_brl"] == "542.00"


def test_unexpected_write_error_exits_1(tmp_path):
    blocker = tmp_path / "arquivo"
    blocker.write_text("", encoding="utf-8")
    input_path = tmp_path / "reservas.csv"
    input_path.write_text(
        "reservation_id,traveler_name,company_id,hotel_id,hotel_name,city,country,checkin_date,"
        "checkout_date,rooms,status,currency,amount,payment_method,booked_at\n"
        "R-1,P,EMP-001,H01,Hotel,SP,BR,2025-01-10,2025-01-11,1,CONFIRMED,BRL,100.00,PIX,x\n",
        encoding="utf-8",
    )
    result = run(
        [
            "--input", str(input_path),
            "--rates", "data/taxas_cambio.csv",
            "--output", str(blocker / "report.json"),
        ],
        blocker / "report.json",
    )
    assert result.returncode == 1
