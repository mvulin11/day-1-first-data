import os
import io
import datetime as dt
from typing import List

import pandas as pd
import streamlit as st

from storage import load_trades, save_trades, upsert_trade, delete_trade, import_trades_csv, export_trades_csv, TRADE_COLUMNS
from pl import compute_pl, compute_unrealized, OPTIONS_MULTIPLIER

APP_TITLE = "Options Profit Tracker"

st.set_page_config(page_title=APP_TITLE, layout="wide")


def _default_trade_datetime():
    return dt.datetime.now().replace(microsecond=0)


def trade_input_form():
    st.subheader("Add or Edit Trade")

    with st.form("trade_form", clear_on_submit=False):
        cols = st.columns(4)
        symbol = cols[0].text_input("Symbol", value=st.session_state.get("symbol", ""))
        option_type = cols[1].selectbox("Type", options=["C", "P"], index=0)
        strike = cols[2].number_input("Strike", min_value=0.0, value=float(st.session_state.get("strike", 0.0)), step=0.5, format="%.2f")
        expiry = cols[3].date_input("Expiry", value=st.session_state.get("expiry", dt.date.today()))

        cols2 = st.columns(4)
        action = cols2[0].selectbox("Action", options=["BTO", "STO", "STC", "BTC"], index=0)
        quantity = cols2[1].number_input("Quantity (contracts)", min_value=1, value=int(st.session_state.get("quantity", 1)))
        price = cols2[2].number_input("Price (per option)", min_value=0.0, value=float(st.session_state.get("price", 0.0)), step=0.01, format="%.2f")
        fees = cols2[3].number_input("Fees", min_value=0.0, value=float(st.session_state.get("fees", 0.0)), step=0.01, format="%.2f")

        cols3 = st.columns(3)
        group_id = cols3[0].text_input("Group ID (strategy)", value=st.session_state.get("group_id", ""))
        trade_dt = cols3[1].datetime_input("Trade time", value=st.session_state.get("trade_datetime", _default_trade_datetime()))
        note = cols3[2].text_input("Note", value=st.session_state.get("note", ""))

        edit_id = st.session_state.get("edit_id")
        submit_label = "Update Trade" if edit_id else "Add Trade"
        submitted = st.form_submit_button(submit_label)
        if submitted:
            row = {
                "id": edit_id,
                "group_id": int(group_id) if str(group_id).strip().isdigit() else None,
                "symbol": symbol.strip().upper(),
                "expiry": expiry,
                "strike": float(strike),
                "option_type": option_type,
                "action": action,
                "quantity": int(quantity),
                "price": float(price),
                "fees": float(fees),
                "trade_datetime": trade_dt,
                "note": note,
            }
            df = upsert_trade(row)
            st.session_state["edit_id"] = None
            st.success(f"Saved trade ID {int(row['id'])}")


def trades_table():
    st.subheader("Trades")
    df = load_trades()

    if df.empty:
        st.info("No trades yet.")
        return

    # Actions: edit/delete
    def on_edit(row):
        st.session_state["edit_id"] = int(row["id"])
        st.session_state.update({
            "symbol": row["symbol"],
            "strike": float(row["strike"]),
            "expiry": row["expiry"],
            "group_id": "" if pd.isna(row["group_id"]) else str(int(row["group_id"])),
            "quantity": int(row["quantity"]),
            "price": float(row["price"]),
            "fees": float(row["fees"]),
            "trade_datetime": row["trade_datetime"],
            "note": row["note"],
        })

    def on_delete(row):
        delete_trade(int(row["id"]))
        st.experimental_rerun()

    # Display
    styled = df.copy()
    styled["expiry"] = pd.to_datetime(styled["expiry"]).dt.strftime("%Y-%m-%d")
    styled["trade_datetime"] = pd.to_datetime(styled["trade_datetime"]).dt.strftime("%Y-%m-%d %H:%M:%S")

    st.dataframe(styled, use_container_width=True, hide_index=True)

    cols = st.columns(3)
    with cols[0]:
        trade_id_to_edit = st.number_input("Trade ID to edit", min_value=0, value=0, step=1)
        if st.button("Load for edit") and trade_id_to_edit:
            row = df[df["id"] == int(trade_id_to_edit)]
            if not row.empty:
                on_edit(row.iloc[0])
                st.experimental_rerun()
            else:
                st.warning("Trade ID not found")
    with cols[1]:
        trade_id_to_delete = st.number_input("Trade ID to delete", min_value=0, value=0, step=1, key="del")
        if st.button("Delete") and trade_id_to_delete:
            on_delete(df[df["id"] == int(trade_id_to_delete)].iloc[0]) if not df[df["id"] == int(trade_id_to_delete)].empty else st.warning("Trade ID not found")
    with cols[2]:
        # Export
        if st.button("Export CSV"):
            csv = styled.to_csv(index=False).encode("utf-8")
            st.download_button("Download trades.csv", csv, file_name="trades.csv", mime="text/csv")

        uploaded = st.file_uploader("Import CSV", type=["csv"], accept_multiple_files=False)
        if uploaded is not None:
            try:
                df_imported = pd.read_csv(uploaded)
                # Save by merging with existing
                existing = load_trades()
                start_id = 1 if existing.empty else int(existing["id"].max()) + 1
                df_imported = df_imported.copy()
                if "id" in df_imported.columns:
                    df_imported = df_imported.drop(columns=["id"])  # reassign ids
                df_imported["id"] = list(range(start_id, start_id + len(df_imported)))
                merged = pd.concat([existing, df_imported], ignore_index=True)
                save_trades(merged)
                st.success(f"Imported {len(df_imported)} rows")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Failed to import: {e}")


def portfolio_view():
    st.subheader("P/L and Positions")
    trades = load_trades()
    realized_df, open_df, total_realized = compute_pl(trades)

    cols = st.columns(3)
    cols[0].metric("Total realized P/L", f"${total_realized:,.2f}")
    open_contracts = int(open_df["open_quantity"].sum()) if not open_df.empty else 0
    cols[1].metric("Open contracts", f"{open_contracts}")
    cols[2].metric("Trades count", f"{len(trades)}")

    st.markdown("Realized events")
    if realized_df.empty:
        st.info("No realized P/L yet.")
    else:
        display = realized_df.copy()
        display["expiry"] = pd.to_datetime(display["expiry"]).dt.strftime("%Y-%m-%d")
        st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("Open positions")
    if open_df.empty:
        st.info("No open positions.")
    else:
        display_open = open_df.copy()
        display_open["expiry"] = pd.to_datetime(display_open["expiry"]).dt.strftime("%Y-%m-%d")
        st.dataframe(display_open, use_container_width=True, hide_index=True)

    st.markdown("Unrealized P/L (enter marks)")
    if not open_df.empty:
        # Build marks input grid
        mark_rows = []
        for idx, row in open_df.iterrows():
            cols = st.columns(6)
            cols[0].write(f"{row['symbol']}")
            cols[1].write(pd.to_datetime(row["expiry"]).strftime("%Y-%m-%d"))
            cols[2].write(f"{row['strike']:.2f}{row['option_type']}")
            cols[3].write(row["side"]) 
            default_mark = float(row["average_cost"])  # default to cost basis
            mark_val = cols[4].number_input(
                "Mark",
                min_value=0.0,
                value=default_mark,
                step=0.01,
                key=f"mark_{idx}",
                format="%.2f",
            )
            cols[5].write(f"Qty {int(row['open_quantity'])}")
            mark_rows.append({
                "symbol": row["symbol"],
                "expiry": row["expiry"],
                "strike": row["strike"],
                "option_type": row["option_type"],
                "side": row["side"],
                "mark": mark_val,
            })
        marks_df = pd.DataFrame(mark_rows)
        unrealized = compute_unrealized(open_df, marks_df)
        st.dataframe(unrealized[["symbol", "expiry", "strike", "option_type", "side", "open_quantity", "average_cost", "mark", "unrealized_pl"]], use_container_width=True, hide_index=True)
        total_unreal = float(unrealized["unrealized_pl"].sum()) if not unrealized.empty else 0.0
        st.metric("Total unrealized P/L", f"${total_unreal:,.2f}")


def main():
    st.title(APP_TITLE)

    tabs = st.tabs(["Add Trade", "Portfolio", "Trades"])

    with tabs[0]:
        trade_input_form()
    with tabs[1]:
        portfolio_view()
    with tabs[2]:
        trades_table()


if __name__ == "__main__":
    main()