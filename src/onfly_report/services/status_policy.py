"""Política de status das reservas."""

from __future__ import annotations

BILLABLE_STATUS = "CONFIRMED"
KNOWN_STATUSES = frozenset({"CONFIRMED", "CANCELLED", "NO_SHOW"})


def is_known_status(status: str) -> bool:
    """Indica se o status faz parte do contrato do relatório."""
    return status in KNOWN_STATUSES


def is_billable(status: str) -> bool:
    """Indica se a reserva entra nos totais financeiros e de noites (só CONFIRMED)."""
    return status == BILLABLE_STATUS
