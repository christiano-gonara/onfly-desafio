"""Testes adicionais: regressão com os arquivos reais de data/.

Os valores esperados vêm da tabela do README (amostra) e de um recálculo independente das regras
sobre data/reservas_hoteis.csv (entrega/ANALISE.md).
"""

from cli_support import run_files
from helpers import PROJECT_ROOT

DATA = PROJECT_ROOT / "data"


def test_validation_sample_matches_readme(tmp_path):
    report = run_files(tmp_path, DATA / "exemplo-validacao.csv", DATA / "taxas_cambio.csv").report()
    assert report["summary"] == {
        "total_reservations": 12,
        "confirmed_reservations": 9,
        "cancelled_reservations": 2,
        "no_show_reservations": 1,
        "total_room_nights": 28,
        "total_amount_brl": "7566.00",
        "average_nightly_rate_brl": "270.21",
    }
    assert report["by_month"] == [
        {"month": "2025-01", "reservations": 8, "room_nights": 25, "total_brl": "6684.00"},
        {"month": "2025-02", "reservations": 1, "room_nights": 3, "total_brl": "882.00"},
    ]
    assert report["top_hotels"] == [
        {"hotel_id": "H01", "hotel_name": "Hotel Aurora Paulista", "room_nights": 3, "total_brl": "1200.00"},
        {"hotel_id": "H02", "hotel_name": "Hotel Mirante", "room_nights": 2, "total_brl": "1084.00"},
        {"hotel_id": "H12", "hotel_name": "Hotel Miami Beach", "room_nights": 1, "total_brl": "1000.00"},
        {"hotel_id": "H10", "hotel_name": "Hotel Madrid, Gran Vía", "room_nights": 4, "total_brl": "900.00"},
        {"hotel_id": "H09", "hotel_name": "Hotel Lisboa, Centro", "room_nights": 3, "total_brl": "882.00"},
    ]


def test_full_dataset_matches_reference(tmp_path):
    report = run_files(tmp_path, DATA / "reservas_hoteis.csv", DATA / "taxas_cambio.csv").report()
    assert report["summary"] == {
        "total_reservations": 300,
        "confirmed_reservations": 235,
        "cancelled_reservations": 31,
        "no_show_reservations": 34,
        "total_room_nights": 1347,
        "total_amount_brl": "396170.00",
        "average_nightly_rate_brl": "294.11",
    }
    assert [item["month"] for item in report["by_month"]] == [
        "2024-12", "2025-01", "2025-02", "2025-03", "2025-04", "2025-05", "2025-06",
    ]
    assert sum(item["reservations"] for item in report["by_month"]) == 235
    assert sum(item["room_nights"] for item in report["by_month"]) == 1347
    assert [item["hotel_id"] for item in report["top_hotels"]] == ["H06", "H10", "H12", "H07", "H11"]
