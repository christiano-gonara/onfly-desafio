# Onfly Report

[![tests](https://github.com/christiano-gonara/onfly-desafio/actions/workflows/tests.yml/badge.svg)](https://github.com/christiano-gonara/onfly-desafio/actions/workflows/tests.yml)

Programa de linha de comando que lê as **reservas de hotel** de uma empresa e gera um **relatório em JSON**: quantas reservas, quantas noites, quanto foi gasto em reais e quais hotéis mais faturaram.

Nasceu de um desafio da Onfly, em que o programa original entregava números errados. Aqui ele está corrigido e testado.

## O que ele faz

1. Lê o CSV de reservas e o CSV de taxas de câmbio.
2. Conta as reservas por status: confirmadas, canceladas e no-show.
3. Considera só as **confirmadas** para noites e valores.
4. Converte tudo para reais.
5. Gera `output/report.json` com o resumo, o total por mês e o ranking de hotéis.

## Como rodar

Precisa do Python 3.11 ou mais novo.

```bash
python3.11 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt

PYTHONPATH=src python -m onfly_report \
  --input data/reservas_hoteis.csv \
  --rates data/taxas_cambio.csv \
  --output output/report.json
```

Ele imprime um resumo e grava o relatório:

```text
Reservas: 300 | Confirmadas: 235 | Noites: 1347 | Total BRL: 396170.00
```

| Opção | Precisa? | O que é |
|---|---|---|
| `--input` | sim | CSV de reservas |
| `--rates` | sim | CSV de câmbio para real |
| `--output` | não | Onde salvar o JSON (padrão: `output/report.json`) |
| `--top` | não | Quantos hotéis no ranking (padrão: 5) |

Se algum dado estiver errado (moeda sem taxa, status desconhecido, check-out antes do check-in), o programa para com a mensagem da linha com problema e código de saída `2`.

## O que sai no relatório

```json
{
  "summary": {
    "total_reservations": 300,
    "confirmed_reservations": 235,
    "total_room_nights": 1347,
    "total_amount_brl": "396170.00",
    "average_nightly_rate_brl": "294.11"
  },
  "by_month": [{ "month": "2025-01", "reservations": 37, "room_nights": 235, "total_brl": "64662.89" }],
  "top_hotels": [{ "hotel_id": "H01", "hotel_name": "...", "room_nights": 0, "total_brl": "0.00" }]
}
```

O arquivo completo também tem `report_version`, `generated_at` e a contagem de canceladas e no-show.

## Regras importantes

- Só reservas `CONFIRMED` entram em noites e valores.
- Noites = (check-out menos check-in) em dias, vezes o número de quartos.
- Valor em reais = valor original vezes a taxa de câmbio.
- O dinheiro usa `Decimal`, nunca `float`, e só é arredondado no final, para 2 casas.

## Testes

```bash
pytest -q
```

São 39 testes: 5 que vieram com o desafio e 34 que adicionei. O GitHub roda todos a cada push.

## Pastas

```text
src/onfly_report/   o programa
tests/              os testes
data/               CSVs de reservas e de câmbio
entrega/            o que foi entregue: defeitos corrigidos e uso de IA
output/             relatório gerado (não vai para o Git)
```

## Os 5 defeitos que foram corrigidos

1. Lia só 200 das 300 reservas.
2. Dividia o câmbio em vez de multiplicar.
3. Faturava reservas `NO_SHOW`.
4. Calculava noites pelo dia do mês, o que dava número negativo na virada de mês.
5. Mostrava o ranking de hotéis do menor para o maior.

O passo a passo está em [`entrega/README-ENTREGA.md`](entrega/README-ENTREGA.md) e a análise em [`entrega/ANALISE.md`](entrega/ANALISE.md).
