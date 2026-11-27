# StockFlow — ECE-063 Inventory Management Dashboard

A local Flask + HTML/CSS/JavaScript frontend connected to a Python inventory engine, using the supplied E015 sample CSV dataset.

## Requirements
- Python 3.9+
- VS Code

## Run in VS Code
1. Extract the ZIP folder.
2. Open `inventory_dashboard` in VS Code.
3. Open Terminal → New Terminal.
4. Create and activate a virtual environment (recommended):
   - Windows PowerShell: `python -m venv .venv` then `.venv\\Scripts\\Activate.ps1`
   - macOS/Linux: `python3 -m venv .venv` then `source .venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Start the app: `python app.py`
7. Open `http://127.0.0.1:5000` in your browser.

## Main features
- Overview metrics and branch stock visualization
- Searchable/filterable stock inventory
- Stock transfer history
- Open supplier reorder list and receive-delivery action
- Post daily sales
- Run a replenishment date
- Execute the full sample command sequence
- Download transfers, reorders, stock-position and error CSV reports
- Reset in-memory state to the original sample dataset

## Notes
- The backend uses the supplied CSV schema and README rules, including the seven-day sales window, fast-mover threshold, days-of-cover priority, nearest-source ordering, pack rounding, Rs 500 transfer guard and open-reorder blocking.
- State changes are held in memory while the Flask process is running. Restarting the server restores the original sample CSV data. Generated reports are written to `output/`.
- `Run sample workflow` executes the supplied commands.txt sequence in order and recreates the reports.
- This is a local educational prototype, not a production multi-user inventory service. Authentication, database persistence and concurrent transaction locking are not included.
