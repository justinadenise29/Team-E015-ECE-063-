# ECE-063 – Electronics Retail Chain Stock Transfer and Reorder Engine — Sample Data Pack
Prepared by 10 SECONDS for Team E015.

This pack is the input for the replenishment engine of a 6-branch electronic components chain: 80 SKUs × 6 branches = 480 stock lines as of close of business 2026-10-11, sales for 2026-10-05 … 2026-10-13, open supplier reorders, and three nightly REPLENISH runs (2026-10-12, 10-13, 10-14). All planted scenarios are in the FIRST run.

Pack conventions where the brief is silent: the 7-day window for REPLENISH on date D is D−7 … D−1; a branch-SKU with no sales row on a date sold 0 that day; average daily sales = window total / 7 (unrounded); days of cover = stock / average (unrounded); SHORT lines are ordered by days of cover ascending, then branch_id, then sku_code, with zero-average lines last (same tie order). Sources are tried nearest first; equal distance → lower branch_id first. Per source the quantity is min(remaining need, available surplus) rounded DOWN to whole packs; if that is 0, or the cost guard blocks it, that source is skipped and the next one is tried; any need left after all sources goes to reorder rounded UP to whole packs. An open reorder for the branch-SKU blocks only the reorder, not transfers. Transfers update stock immediately (post-plan stock); new reorders become open reorders. Fast-mover min doubling applies when the 7-day average is strictly above 20.00. `POST_SALES|D` subtracts that day's sales.csv rows from stock; `RECEIVE` adds the reorder quantity and closes it.

## Files
| File | What it holds | Rows |
|---|---|---|
| branches.csv | Branches | 6 |
| distances.csv | Road distance between every ordered pair of branches (symmetric) | 30 |
| skus.csv | SKU master: cost and pack size | 80 |
| stock.csv | Stock, min and max per branch-SKU at close of 2026-10-11 | 480 |
| open_reorders.csv | Supplier reorders already open | 7 |
| sales.csv | Daily sales per branch-SKU (rows only where qty > 0) | 3523 |
| commands.txt | Loads, receipts, sales posting and the three nightly runs | 28 |

## Column reference
Conventions: dates `YYYY-MM-DD`; timestamps `YYYY-MM-DD HH:MM:SS` (24h, IST, no timezone suffix); money in Rs as plain decimals (no commas, no symbol); percentages as plain numbers (12.5 = 12.5%); booleans `true`/`false`; IDs uppercase with a fixed prefix.

### branches.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| branch_id | string | BR-nn | BR-01 … BR-06 | Primary key |
| branch_name | string | - |  |  |
| city | string | - |  |  |

### distances.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| from_branch | string | BR-nn |  |  |
| to_branch | string | BR-nn |  |  |
| distance_km | integer | km |  | Same in both directions |

### skus.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| sku_code | string | SKU-nnnn | SKU-0001 … SKU-0080 | Primary key |
| description | string | - |  |  |
| unit_cost | decimal | Rs |  | Transfer value = qty × unit_cost |
| pack_size | integer | units | 1, 5, 10, 50, 100 |  |

### stock.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| branch_id | string | BR-nn | must exist |  |
| sku_code | string | SKU-nnnn | must exist |  |
| min_qty | integer | units |  | SHORT when stock < min (min doubled for fast movers) |
| max_qty | integer | units |  | SURPLUS when stock > max |
| stock_qty | integer | units |  |  |

### open_reorders.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| reorder_id | string | RO-nnnn | unique |  |
| branch_id | string | BR-nn |  |  |
| sku_code | string | SKU-nnnn |  |  |
| qty | integer | units | whole packs |  |
| raised_date | date | YYYY-MM-DD |  |  |
| expected_date | date | YYYY-MM-DD |  | Informational; stock changes only on RECEIVE |

### sales.csv
| Column | Type | Units / format | Allowed values | Notes |
|---|---|---|---|---|
| sale_date | date | YYYY-MM-DD | 2026-10-05 … 2026-10-13 |  |
| branch_id | string | BR-nn |  |  |
| sku_code | string | SKU-nnnn |  |  |
| qty_sold | integer | units | ≥ 1 |  |

## Command file format
`commands.txt` holds one command per line as `COMMAND_NAME|arg1|arg2|...`. Commands must be processed in file order, top to bottom. Lines starting with `#` are comments and blank lines are ignored.

| Command | Arguments (in order) | Meaning |
|---|---|---|
| LOAD_BRANCHES | file | Load branches.csv |
| LOAD_DISTANCES | file | Load distances.csv |
| LOAD_SKUS | file | Load skus.csv |
| LOAD_STOCK | file | Load stock.csv |
| LOAD_OPEN_REORDERS | file | Load open_reorders.csv |
| LOAD_SALES | file | Load sales.csv |
| RECEIVE | reorder_id \| date | Supplier delivery: add qty to stock, close the reorder |
| POST_SALES | date | Subtract that date's sales from stock |
| REPLENISH | run_date | Plan transfers and reorders, apply transfers to stock |
| PRINT_TRANSFERS | run_date | Write that run's transfers |
| PRINT_REORDERS | run_date | Write that run's reorders (and skipped lines) |
| PRINT_STOCK | run_date | Write the post-plan stock position |

reorders.csv `status` is ORDERED or SKIPPED_OPEN_REORDER. stock_position `status` is SHORT, SURPLUS or OK as evaluated BEFORE the plan; `avg_daily_sales` with 2 decimals; `value` in Rs with 2 decimals.

## Planted scenarios
Line numbers count the header row as line 1, so the first data row of a CSV is line 2. For commands.txt the line number is the physical line in the file (comment lines included).

- **Stock exactly at min and exactly at max** — stock.csv line 32 (BR-01 SKU-0031): stock 40 = min 40 → NOT short; stock.csv line 112 (BR-02 SKU-0031): stock 90 = max 90 → NOT surplus. REPLENISH 2026-10-12 makes no transfer and no reorder for SKU-0031.
- **Need exactly one pack** — stock.csv line 232 (BR-03 SKU-0071): min 95, max 100, stock 90 → SHORT, need = 100 − 90 = 10 = exactly one pack of 10; nearest surplus stock.csv line 72 (BR-01 SKU-0071) (stock 75, max 60, surplus 15, 14 km) → transfer 10 in run 2026-10-12.
- **Two source branches at equal distance** — stock.csv line 465 (BR-06 SKU-0064) needs 50 (pack 10). Surplus sits at stock.csv line 145 (BR-02 SKU-0064) (20) and stock.csv line 385 (BR-05 SKU-0064) (40), both exactly 140 km from BR-06 (distances.csv). Pack convention: equal distance → lower branch_id first → 20 from BR-02, then 30 from BR-05 (BR-05 ends at 70, still above max).
- **SKU with zero sales in 7 days** — SKU-0032 at BR-04 has no sales rows in the 7-day window (2026-10-05 … 2026-10-11) → average 0 → its SHORT line (stock.csv line 273 (BR-04 SKU-0032), need 35) is processed after all others. stock.csv line 113 (BR-02 SKU-0032) (need 35, cover 8.33 days) goes first and takes the only surplus, 10 units from BR-01 → BR-02 reorders 30, BR-04 reorders 40.
- **Transfer that would leave the source exactly at max** — stock.csv line 387 (BR-05 SKU-0066): stock 55, max 40 → surplus 15 (pack 5). stock.csv line 227 (BR-03 SKU-0066): min 50, stock 45 → need 15. Transfer 15 (58 km, value = 15 × 195.50 ≥ Rs 500 so the cost guard does not block it) leaves BR-05 exactly at max 40 — no longer surplus.

Extra traps (realistic things your validation should catch):

- **Transfer cost guard** — stock.csv line 448 (BR-06 SKU-0047) needs 250; the only surplus is stock.csv line 368 (BR-05 SKU-0047) (250) at 140 km, value 250 × 1.70 = 425.00 < Rs 500 → no transfer; reorder 250.
- **Fast mover and the 20/day boundary** — stock.csv line 80 (BR-01 SKU-0079) sold 168 in 7 days (24.00/day > 20) → min doubled 100 → 200, stock 150 → SHORT, need 250 → reorder 250. stock.csv line 160 (BR-02 SKU-0079) sold exactly 140 (20.00/day, not above 20) → min stays 100 → not short.
- **Open reorder blocks a new reorder** — stock.csv line 101 (BR-02 SKU-0020) is SHORT (need 70) with no surplus anywhere, but open_reorders.csv line 8 (RO-0007) is open for it → no new reorder in run 2026-10-12 (log as skipped).
- **Nearest source below one pack** — stock.csv line 81 (BR-01 SKU-0080) needs 250 (pack 50). Nearest surplus stock.csv line 241 (BR-03 SKU-0080) is only 30 (< 1 pack) → skipped; next stock.csv line 401 (BR-05 SKU-0080) gives 100 (70 km, value = 100 × 6.80 ≥ 500); remaining 150 → reorder 150.
- **Days of cover decides scarce surplus** — SKU-0062: BR-01 has 20 surplus. stock.csv line 223 (BR-03 SKU-0062) (cover 10 / 20 = 0.5 days) is processed before stock.csv line 143 (BR-02 SKU-0062) (cover 1.5 days) → BR-03 gets all 20; BR-02 reorders 50.
- **Pack floor on transfer, ceiling on reorder** — stock.csv line 308 (BR-04 SKU-0067) needs 43 (pack 10); stock.csv line 68 (BR-01 SKU-0067) has 40 surplus → transfer 40; the remaining 3 → reorder 10.
- **Unknown reorder id** — commands.txt line 20 RECEIVE|RO-0999 → error line, no stock change.

## What is NOT in this pack
Expected outputs are not provided for this set. Validate your engine with your own test suite against the rules in your brief (BR-01 … BR-07). A separate hidden input set with the same schema will be used at final evaluation; outputs are compared field-for-field, so follow the column formats above exactly in your own output.

## Output format expected at evaluation
Produce these files (CSV, header row, same conventions as above). Column order matters.

### transfers.csv
One row per transfer in the order they were planned.

Columns in order: `run_date`, `seq`, `sku_code`, `from_branch`, `to_branch`, `qty`, `distance_km`, `value`

### reorders.csv
One row per SHORT line with need left after transfers, in processing order.

Columns in order: `run_date`, `branch_id`, `sku_code`, `remaining_need`, `reorder_qty`, `status`

### stock_position.csv
One row per branch-SKU after each run, sorted by branch_id then sku_code.

Columns in order: `run_date`, `branch_id`, `sku_code`, `effective_min`, `max_qty`, `opening_stock`, `transfer_in`, `transfer_out`, `closing_stock`, `avg_daily_sales`, `status`

### errors.csv
Rejected commands.

Columns in order: `line_no`, `command`, `reason`
