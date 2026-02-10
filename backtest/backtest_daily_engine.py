# ============================================================
# BACKTEST ENGINE – DAILY POSITION (CAPITAL BASED)
# FIXED VERSION • NO STREAMLIT • PURE PYTHON
# ============================================================

import pandas as pd


def backtest_daily_capital(
    df,
    ai_score_map,
    initial_capital=100_000_000,
    risk_per_trade=0.01,
    tp_pct=0.06,
    sl_pct=0.04,
    max_holding_days=5,
    min_ai_score=60,
    min_ml_conf=0.55,
    cooldown_days=3,
    min_equity_pct=0.3
):
    """
    Daily position backtest with:
    - Capital based sizing
    - ML filter
    - Cooldown
    - Equity protection
    """

    trades = []
    equity = initial_capital

    symbols = df["Symbol"].unique()

    # track last exit index per symbol
    last_exit_index = {s: -999 for s in symbols}

    for symbol in symbols:
        d = (
            df[df["Symbol"] == symbol]
            .sort_values("Tanggal Perdagangan Terakhir")
            .reset_index(drop=True)
        )

        for i in range(len(d) - max_holding_days - 1):

            # =====================
            # GLOBAL STOP (ACCOUNT BLOW PROTECTION)
            # =====================
            if equity < initial_capital * min_equity_pct:
                break

            # =====================
            # COOLDOWN CHECK
            # =====================
            if i - last_exit_index[symbol] < cooldown_days:
                continue

            row = d.loc[i]

            # =====================
            # AI FILTER
            # =====================
            ai_score = ai_score_map.get(symbol, 0)
            if ai_score < min_ai_score:
                continue

            # =====================
            # BANDAR FILTER
            # =====================
            if row["Bandar"] == "DISTRIBUSI":
                continue

            # =====================
            # ML FILTER
            # =====================
            ml_conf = row.get("ml_confidence_label_daily")
            if pd.isna(ml_conf) or ml_conf < min_ml_conf:
                continue

            # =====================
            # ENTRY
            # =====================
            entry_price = row["Close"]
            entry_date = row["Tanggal Perdagangan Terakhir"]

            # =====================
            # POSITION SIZING
            # =====================
            risk_amount = equity * risk_per_trade
            sl_price = entry_price * (1 - sl_pct)
            risk_per_share = entry_price - sl_price

            if risk_per_share <= 0:
                continue

            qty = int(risk_amount / risk_per_share)
            if qty <= 0:
                continue

            if qty * entry_price > equity:
                continue

            # =====================
            # EXIT CHECK
            # =====================
            future = d.loc[i + 1 : i + max_holding_days]

            exit_price = None
            exit_date = None
            result = "TIMEOUT"

            for _, f in future.iterrows():
                if f["Low"] <= sl_price:
                    exit_price = sl_price
                    exit_date = f["Tanggal Perdagangan Terakhir"]
                    result = "SL"
                    break

                if f["High"] >= entry_price * (1 + tp_pct):
                    exit_price = entry_price * (1 + tp_pct)
                    exit_date = f["Tanggal Perdagangan Terakhir"]
                    result = "TP"
                    break

            if exit_price is None:
                last = future.iloc[-1]
                exit_price = last["Close"]
                exit_date = last["Tanggal Perdagangan Terakhir"]

            # =====================
            # PNL & EQUITY UPDATE
            # =====================
            pnl = (exit_price - entry_price) * qty
            equity += pnl

            last_exit_index[symbol] = i

            trades.append({
                "Symbol": symbol,
                "Entry Date": entry_date,
                "Exit Date": exit_date,
                "Entry": round(entry_price, 0),
                "Exit": round(exit_price, 0),
                "Qty": qty,
                "PNL": round(pnl, 0),
                "Result": result,
                "ML Conf": round(float(ml_conf), 3),
                "AI Score": ai_score,
                "Equity": round(equity, 0)
            })

    if not trades:
        return None, None

    trades_df = pd.DataFrame(trades)

    # =====================
    # METRICS
    # =====================
    trades_df["Peak"] = trades_df["Equity"].cummax()
    trades_df["Drawdown (%)"] = (
        (trades_df["Equity"] - trades_df["Peak"])
        / trades_df["Peak"] * 100
    )

    summary = {
        "Initial Capital": initial_capital,
        "Final Equity": round(equity, 0),
        "Total Trades": len(trades_df),
        "Winrate (%)": round((trades_df["PNL"] > 0).mean() * 100, 2),
        "Total PNL": round(trades_df["PNL"].sum(), 0),
        "Max Drawdown (%)": round(trades_df["Drawdown (%)"].min(), 2),
        "Avg ML Conf": round(trades_df["ML Conf"].mean(), 3)
    }

    return trades_df, summary
