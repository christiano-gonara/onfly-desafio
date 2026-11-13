"""Testes adicionais: lacunas de agregação não cobertas pelos testes fornecidos."""

from cli_support import run_rows


def test_reads_more_than_200_rows(tmp_path):
    """Defeito 1: o leitor parava em 200 linhas e descartava o resto."""
    rows = [{"reservation_id": f"R-{i}"} for i in range(250)]
    summary = run_rows(tmp_path, rows).report()["summary"]
    assert summary["total_reservations"] == 250
    assert summary["confirmed_reservations"] == 250
    assert summary["total_room_nights"] == 250
    assert summary["total_amount_brl"] == "25000.00"


def test_nights_across_year_boundary(tmp_path):
    """Virada de ano: 30/12 a 02/01 = 3 noites, e o mês é o do check-in."""
    report = run_rows(
        tmp_path,
        [{"checkin_date": "2024-12-30", "checkout_date": "2025-01-02"}],
    ).report()
    assert report["summary"]["total_room_nights"] == 3
    assert report["by_month"] == [
        {"month": "2024-12", "reservations": 1, "room_nights": 3, "total_brl": "100.00"}
    ]


def test_room_nights_multiply_by_rooms(tmp_path):
    report = run_rows(
        tmp_path,
        [{"checkin_date": "2025-01-10", "checkout_date": "2025-01-13", "rooms": "2"}],
    ).report()
    assert report["summary"]["total_room_nights"] == 6
    assert report["summary"]["average_nightly_rate_brl"] == "16.67"


def test_by_month_sorted_and_only_confirmed(tmp_path):
    report = run_rows(
        tmp_path,
        [
            {"reservation_id": "R-1", "checkin_date": "2025-03-01", "checkout_date": "2025-03-03"},
            {"reservation_id": "R-2", "checkin_date": "2025-01-05", "checkout_date": "2025-01-06"},
            {"reservation_id": "R-3", "checkin_date": "2025-01-20", "checkout_date": "2025-01-21",
             "currency": "EUR", "amount": "10.00"},
            {"reservation_id": "R-4", "checkin_date": "2025-02-01", "checkout_date": "2025-02-02",
             "status": "CANCELLED"},
            {"reservation_id": "R-5", "checkin_date": "2025-02-01", "checkout_date": "2025-02-02",
             "status": "NO_SHOW"},
        ],
    ).report()
    assert report["by_month"] == [
        {"month": "2025-01", "reservations": 2, "room_nights": 2, "total_brl": "158.80"},
        {"month": "2025-03", "reservations": 1, "room_nights": 2, "total_brl": "100.00"},
    ]


def test_top_hotels_tie_breaks_by_hotel_id(tmp_path):
    report = run_rows(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H03", "hotel_name": "C", "amount": "500.00"},
            {"reservation_id": "R-2", "hotel_id": "H01", "hotel_name": "A", "amount": "500.00"},
            {"reservation_id": "R-3", "hotel_id": "H02", "hotel_name": "B", "amount": "900.00"},
        ],
    ).report()
    assert [hotel["hotel_id"] for hotel in report["top_hotels"]] == ["H02", "H01", "H03"]


def test_top_hotels_excludes_non_confirmed_and_aggregates_per_hotel(tmp_path):
    report = run_rows(
        tmp_path,
        [
            {"reservation_id": "R-1", "hotel_id": "H01", "amount": "100.00"},
            {"reservation_id": "R-2", "hotel_id": "H01", "amount": "150.00", "rooms": "2"},
            {"reservation_id": "R-3", "hotel_id": "H02", "amount": "9999.00", "status": "CANCELLED"},
            {"reservation_id": "R-4", "hotel_id": "H03", "amount": "9999.00", "status": "NO_SHOW"},
        ],
    ).report()
    assert report["top_hotels"] == [
        {"hotel_id": "H01", "hotel_name": "Hotel Teste", "room_nights": 3, "total_brl": "250.00"}
    ]


def test_top_default_is_five_and_respects_top_argument(tmp_path):
    rows = [
        {"reservation_id": f"R-{i}", "hotel_id": f"H{i:02d}", "amount": f"{100 + i}.00"}
        for i in range(1, 8)
    ]
    assert len(run_rows(tmp_path, rows).report()["top_hotels"]) == 5
    assert [h["hotel_id"] for h in run_rows(tmp_path, rows, top=2).report()["top_hotels"]] == ["H07", "H06"]
    assert len(run_rows(tmp_path, rows, top=50).report()["top_hotels"]) == 7
