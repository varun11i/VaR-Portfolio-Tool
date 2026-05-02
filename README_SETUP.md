# Python_Portfolio__VaR_Tool — Setup Guide (macOS)

This guide explains how to set up a clean, reproducible virtual environment and run the app locally after unzipping the project.

---

## Prerequisites
- macOS 12+
- Python **3.11** installed (Homebrew Python works well)
- Optional: VS Code

If Python 3.11 is not installed:
```bash
brew install python@3.11
```

---

## 1) Unzip and open the project
Unzip the provided ZIP anywhere (e.g., Desktop), then open a terminal in the project folder:
```bash
cd "/path/to/Python_Portfolio__VaR_Tool"
```

---

## 2) Install **uv** (fast venv + pip) — one-time
If you already have `uv`, you can skip these two lines.
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.local/bin:$PATH"
uv --version
```

> If you see a permissions warning about updating your shell config, it’s okay. The `export PATH=...` line above is enough for this terminal session.

---

## 3) Create and activate the virtual environment
```bash
uv venv .venv -p python3.11
source .venv/bin/activate
python -V   # should print Python 3.11.x
```

---

## 4) Install dependencies (pinned & stable)
```bash
uv pip install --upgrade pip
uv pip install   wxPython==4.2.1   pandas==2.2.2   numpy==1.26.4   scipy==1.11.4   matplotlib==3.8.4   yfinance==0.2.40   pandas-datareader==0.10.0
```

> The project includes a compatibility shim (`fix_yahoo_finance.py`) that fetches data from **Stooq** and exposes the expected **`Adj close`** column. This avoids Yahoo rate limits/JSON issues while keeping the legacy code paths unchanged.

---

## 5) (Optional) Sanity check the data path
```bash
python - <<'PY'
import fix_yahoo_finance as yf
d = yf.download(["AAPL","MSFT"], start="2023-01-01")
print("OK, shape:", d.shape, "sample columns:", list(d.columns)[:2])
PY
```
You should see a non-empty shape and columns like `('Adj close', 'AAPL')`.

---

## 6) Run the app
```bash
python Portfolio_VaR_Toolv5.py
```

### Suggested test inputs
- **Tickers:** `AAPL, MSFT, AMZN, GOOG`
- **Weights:** `0.30, 0.30, 0.20, 0.20` (decimals; must sum to 1)
- **Start date:** `01/01/2023` (format **dd/mm/yyyy**)
- **End date (optional):** e.g., `01/01/2024`
- **Benchmark:** `SPY`

---

## 7) (Optional) VS Code interpreter
In VS Code: `Cmd+Shift+P` → **Python: Select Interpreter** → choose:
```
…/Python_Portfolio__VaR_Tool/.venv/bin/python
```

---

## 8) Troubleshooting
- **“uv: command not found”** → `export PATH="$HOME/.local/bin:$PATH"` and retry.
- **wx import errors** → ensure Step 4 succeeded (especially `wxPython==4.2.1`).
- **Blank VAR/Correlation tabs** → broaden the date range or use fewer tickers. The app shows friendly messages when returns are empty.
- **Date parsing** → must be **dd/mm/yyyy**; End date must be on/after Start date.
- **Weights** → must be decimals that sum to **1.0**.
- **Yahoo rate limits/JSON errors** → avoided by the included Stooq shim.

---

## 9) Reproducibility (optional)
Freeze your working environment:
```bash
pip freeze > requirements.lock.txt
```
Re-install later with:
```bash
uv pip install -r requirements.lock.txt
```

---

## Notes
- Data source uses **Stooq** via `pandas-datareader` for reliability but maintains the legacy **`Adj close`** column expected by the app.
- The UI supports **Start** and **End** dates (both in **dd/mm/yyyy** format).
