# Stooq-only compatibility shim for legacy "fix_yahoo_finance"
# - Always fetches from Stooq via pandas_datareader
# - Exposes 'Adj close' column name the old app expects
# - Normalizes tickers like BRK.B -> BRK-B

import pandas as pd

try:
    from pandas_datareader import data as pdr
except Exception as e:
    raise RuntimeError("pandas-datareader is required for this shim") from e

SYMBOL_ALIASES = {"UN":"UL","BRK.B":"BRK-B","BF.B":"BF-B"}

def _normalize_tickers(tickers):
    if isinstance(tickers, str):
        parts = [t.strip() for t in tickers.replace(",", " ").split() if t.strip()]
    else:
        parts = list(tickers)
    out = []
    for t in parts:
        t = SYMBOL_ALIASES.get(t, t)
        if "." in t:
            t = t.replace(".", "-")
        out.append(t)
    return out if len(out) > 1 else (out[0] if out else tickers)

def download(*args, **kwargs):
    # Accepts same signature as yfinance.download(tickers, start=..., end=...)
    if args:
        tickers = _normalize_tickers(args[0])
        args = args[1:]
    else:
        tickers = _normalize_tickers(kwargs.pop("tickers", []))
    if not isinstance(tickers, (list, tuple)):
        tickers = [tickers] if tickers else []
    start = kwargs.get("start", None)
    end   = kwargs.get("end", None)

    frames = []
    for t in tickers:
        try:
            df = pdr.DataReader(t, "stooq", start=start, end=end)
            # Stooq columns: ['Open','High','Low','Close','Volume']
            df = df.rename(columns={"Close": "Adj close"})
            # MultiIndex like yfinance: (field, ticker)
            df.columns = pd.MultiIndex.from_product([df.columns, [t]])
            # Keep only 'Adj close' to match the app
            frames.append(df[["Adj close"]])
        except Exception:
            # Skip bad tickers silently (matches yfinance behavior)
            pass

    if not frames:
        return pd.DataFrame()
    out = pd.concat(frames, axis=1).sort_index()
    # Drop all-empty columns (if any ticker failed)
    out = out.dropna(axis=1, how="all")
    return out
