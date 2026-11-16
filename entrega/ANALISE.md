# Análise — consolidador de reservas Onfly

Sessão 1 (análise). Nenhum arquivo do projeto foi alterado nesta etapa.

## Estado inicial

- `pytest -q`: 5 de 5 testes falhando.
- CLI no dataset real: `Reservas: 200 | Confirmadas: 153 | Noites: -1393 | Total BRL: 193218.53`

Valores de referência calculados de forma independente (script à parte, regras do README):

| Métrica | CLI atual | Esperado |
|-|-|-|
| total_reservations | 200 | **300** |
| confirmed_reservations | 153 | **235** |
| cancelled / no_show | — | **31 / 34** |
| total_room_nights | -1393 | **1347** |
| total_amount_brl | 193218.53 | **396170.00** |
| average_nightly_rate_brl | — | **294.11** |
| top 5 hotéis | — | **H06, H10, H12, H07, H11** |

`data/exemplo-validacao.csv` (conferência manual): 9 confirmadas, 28 noites, 7566.00 BRL, média 270.21.

## data/

- `reservas_hoteis.csv`: 300 linhas, sem vazios, sem espaços extras, IDs únicos, valores com 2 casas, `checkout > checkin` em todas, um nome por `hotel_id`.
- Armadilhas intencionais: 16 reservas cruzam a virada de ano; hotéis com vírgula no nome (`"Hotel Lisboa, Centro"`); 300 linhas (acima do corte de 200 do CLI).
- `taxas_cambio.csv`: BRL 1.0, USD 5.42, EUR 5.88.
- Conclusão: os dados estão consistentes, como o README afirma. Não devem ser alterados.

## Defeitos (obrigatórios)

| # | Arquivo | Defeito | Correção | Teste que pega |
|-|-|-|-|-|
| 1 | `repositories/csv_reservation_repository.py:47` | `break` em 200 linhas descarta reservas | remover o corte | nenhum (lacuna) |
| 2 | `services/currency_converter.py:11` | divide pela taxa e usa `float` | `amount * rate` em `Decimal` | `test_currency`, regressão |
| 3 | `services/status_policy.py:8` | `!= "CANCELLED"` fatura NO_SHOW | `== "CONFIRMED"` | `test_status_rules`, regressão |
| 4 | `services/stay_calculator.py:10` | `checkout.day - checkin.day` | `(checkout - checkin).days * rooms` | `test_nights`, regressão |
| 5 | `services/report_builder.py:91` | ranking ascendente | `key=(-amount, hotel_id)` | `test_top_hotels` |

## Fragilidades (não alteram números com os dados atuais)

- Moeda sem taxa gera `KeyError` e sai com código 1; pelo contrato, entrada inválida deveria sair com 2.
- Repositório de câmbio normaliza moeda com `strip().upper()`; o de reservas só faz `strip()`.
- Status desconhecido entra em `total_reservations`, mas em nenhum contador, sem aviso.
- `RowParser` não valida `rooms >= 1` nem `checkout > checkin`.

## Lacunas de teste

Mais de 200 linhas; virada de ano; `by_month`; desempate do ranking por `hotel_id`; arredondamento half-up; média com zero noites; `rooms > 1`; códigos de saída 2 e 1; `--top 0`; regressão com o dataset real.

## Plano para a sessão de ação

1. Corrigir os defeitos 1 a 5, um por vez, rodando os testes a cada passo.
2. Adicionar testes novos para as lacunas (sem alterar os fornecidos).
3. Validação defensiva: moeda sem taxa, status desconhecido, `rooms < 1` e `checkout <= checkin` viram `InputFileError` (saída 2, com número da linha).
4. Gerar `output/report.json` e conferir com a tabela de referência acima.
5. Escrever `entrega/README-ENTREGA.md` (resumo antes/depois, defeito → correção → prova, decisões).

## Decisão sobre tratamento de dados

Não limpar nem alterar os CSVs, e não descartar linhas silenciosamente: o README diz que os defeitos estão no CLI e o `RowParser` define que falha de formato é erro de arquivo. O CLI deve validar e rejeitar com mensagem clara, não corrigir os dados.
