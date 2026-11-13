"""Testes adicionais: exatidão do dinheiro e contrato do JSON."""

import re
from datetime import date
from decimal import Decimal

from cli_support import run_rows

from onfly_report.services.currency_converter import convert_to_brl
from onfly_report.services.status_policy import is_billable
from onfly_report.services.stay_calculator import calculate_room_nights

RATES = {"BRL": Decimal("1"), "USD": Decimal("5.42"), "EUR": Decimal("5.88")}


def test_convert_to_brl_is_exact_decimal_multiplication():
    result = convert_to_brl(Decimal("0.10"), "USD", RATES)
    assert isinstance(result, Decimal)
    assert result == Decimal("0.542")


def test_calculate_room_nights_uses_date_difference():
    assert calculate_room_nights(date(2025, 2, 27), date(2025, 3, 2), 3) == 9
    assert calculate_room_nights(date(2024, 2, 28), date(2024, 3, 1), 1) == 2  # ano bissexto


def test_only_confirmed_is_billable():
    assert is_billable("CONFIRMED")
    assert not is_billable("CANCELLED")
    assert not is_billable("NO_SHOW")


def test_rounding_is_half_up_on_serialization(tmp_path):
    """0.005 vira 0.01 (half-up); ROUND_HALF_EVEN daria 0.00."""
    summary = run_rows(tmp_path, [{"amount": "0.005"}]).report()["summary"]
    assert summary["total_amount_brl"] == "0.01"


def test_sums_exact_values_and_rounds_only_at_the_end(tmp_path):
    """3 x 0.004 = 0.012 -> 0.01. Arredondar cada parcela antes daria 0.00."""
    rows = [{"reservation_id": f"R-{i}", "amount": "0.004"} for i in range(3)]
    summary = run_rows(tmp_path, rows).report()["summary"]
    assert summary["total_amount_brl"] == "0.01"


def test_converted_value_rounds_after_sum(tmp_path):
    """USD 0.10 * 5.42 = 0.542 cada; 3 parcelas = 1.626 -> 1.63 (por parcela daria 1.62)."""
    rows = [{"reservation_id": f"R-{i}", "currency": "USD", "amount": "0.10"} for i in range(3)]
    summary = run_rows(tmp_path, rows).report()["summary"]
    assert summary["total_amount_brl"] == "1.63"


def test_average_is_zero_without_confirmed_nights(tmp_path):
    report = run_rows(
        tmp_path,
        [
            {"reservation_id": "R-1", "status": "CANCELLED"},
            {"reservation_id": "R-2", "status": "NO_SHOW"},
        ],
    ).report()
    assert report["summary"] == {
        "total_reservations": 2,
        "confirmed_reservations": 0,
        "cancelled_reservations": 1,
        "no_show_reservations": 1,
        "total_room_nights": 0,
        "total_amount_brl": "0.00",
        "average_nightly_rate_brl": "0.00",
    }
    assert report["by_month"] == []
    assert report["top_hotels"] == []


def test_money_has_two_decimals_and_no_thousand_separator(tmp_path):
    summary = run_rows(tmp_path, [{"amount": "1234567.5"}]).report()["summary"]
    assert summary["total_amount_brl"] == "1234567.50"


def test_report_shape_matches_contract(tmp_path):
    report = run_rows(tmp_path, [{}]).report()
    assert list(report) == ["report_version", "generated_at", "summary", "by_month", "top_hotels"]
    assert report["report_version"] == "1.0"
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}-03:00", report["generated_at"])
    assert list(report["summary"]) == [
        "total_reservations",
        "confirmed_reservations",
        "cancelled_reservations",
        "no_show_reservations",
        "total_room_nights",
        "total_amount_brl",
        "average_nightly_rate_brl",
    ]
    assert list(report["by_month"][0]) == ["month", "reservations", "room_nights", "total_brl"]
    assert list(report["top_hotels"][0]) == ["hotel_id", "hotel_name", "room_nights", "total_brl"]
    money = [report["summary"]["total_amount_brl"], report["summary"]["average_nightly_rate_brl"]]
    money += [item["total_brl"] for item in report["by_month"] + report["top_hotels"]]
    assert all(isinstance(value, str) and re.fullmatch(r"-?\d+\.\d{2}", value) for value in money)


def test_stdout_summary_is_printed(tmp_path):
    result = run_rows(tmp_path, [{}])
    assert result.returncode == 0
    assert result.stdout.strip() == "Reservas: 1 | Confirmadas: 1 | Noites: 1 | Total BRL: 100.00"
