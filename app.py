import time
import altair as alt
import pandas as pd
import streamlit as st
from eth_account import Account
from eth_account.messages import encode_defunct

from chain import (
    make_genesis,
    make_block,
    validate_chain,
    to_dicts,
    from_dicts,
    canonical_message,
)
from storage import load_chain, save_chain
from summarize import local_summary, ai_studio_summary
from utils import pretty_time, is_positive_number, fmt_money, CURRENCY_SYMBOLS, clean_ai_text


# ---------- Page setup ----------
st.set_page_config(page_title="Money Savings Pot (Simulated)", layout="wide")
st.title("Money Savings Pot — Demo App")
st.caption(
    "Transparent group saving with a hash-linked ledger. Optional wallet signing for crypto-style attestations. "
    "Not real money. Not financial advice."
)

# ---------- Load / init chain ----------
raw_rows = load_chain()
chain = from_dicts(raw_rows) if raw_rows else [make_genesis()]
if not raw_rows:
    save_chain(to_dicts(chain))

# ---------- Sidebar ----------
st.sidebar.header("Pot Settings")
pot_name = st.sidebar.text_input("Pot name", value="SpringBreakFund")
goal = st.sidebar.number_input("Savings goal", min_value=0.0, value=500.0, step=50.0)
currency = st.sidebar.selectbox("Currency", ["USD", "EUR", "GBP", "CAD", "AUD", "JPY"], index=0)
allow_withdraw = st.sidebar.checkbox("Allow withdrawals", value=True)
use_ai = st.sidebar.checkbox(
    "AI Coach (Google AI Studio)",
    value=False,
    help="Requires GOOGLE_API_KEY in .env (falls back to local summary if missing).",
)

# ---------- Transaction form (with LOCKED message to avoid drift) ----------
st.subheader("Add Transaction")
c1, c2, c3, c4 = st.columns([1.2, 1, 1, 2])
with c1:
    actor = st.text_input("Who? (name or handle)", placeholder="Alice")
with c2:
    action = st.selectbox("Action", ["DEPOSIT", "WITHDRAW"] if allow_withdraw else ["DEPOSIT"])
with c3:
    amt_str = st.text_input("Amount", placeholder="25.00")
with c4:
    note = st.text_input("Note (optional)", placeholder="Weekly contribution")

# Session state for locking the exact message to sign
if "locked_msg" not in st.session_state:
    st.session_state.locked_msg = ""
if "locked_ts" not in st.session_state:
    st.session_state.locked_ts = 0

lock_col1, lock_col2 = st.columns([2, 1])
with lock_col1:
    if st.button("1) Generate message to sign"):
        if not actor.strip():
            st.warning("Enter a name first.")
        elif not is_positive_number(amt_str):
            st.warning("Enter a valid positive amount first.")
        else:
            ts_now = int(time.time())
            st.session_state.locked_ts = ts_now
            st.session_state.locked_msg = canonical_message(
                pot_name=pot_name,
                actor=actor or "UNKNOWN",
                action=action,
                amount=float(amt_str),
                ts=ts_now,
                prev_hash=chain[-1].hash,  # freeze prev hash at generation time
            )
with lock_col2:
    if st.button("Reset message"):
        st.session_state.locked_msg = ""
        st.session_state.locked_ts = 0

wallet_address = st.text_input("Wallet address (0x…)", placeholder="0xabc...")
canonical = st.text_input(
    "Canonical message (read-only)",
    value=st.session_state.locked_msg,
    disabled=True,
)
signature = st.text_input("Signature (0x…)", placeholder="Paste from signer.html")

st.markdown(
    " Need a signature? Run a simple server and open **`signer.html`** at "
    "`http://localhost:8000/signer.html`. Paste the *Canonical message* above, **Sign**, then paste "
    "**Address** + **Signature** back here. Do **not** change any form fields between generating and signing."
)

# ---------- Add to ledger (verifies signature if provided) ----------
if st.button("2) Add to Ledger"):
    if not actor.strip():
        st.warning("Enter a name.")
        st.stop()
    if not is_positive_number(amt_str):
        st.warning("Amount must be a positive number.")
        st.stop()
    if action == "WITHDRAW" and not allow_withdraw:
        st.warning("Withdrawals disabled.")
        st.stop()

    msg_to_sign = st.session_state.locked_msg
    if not msg_to_sign:
        st.warning("Click '1) Generate message to sign' first (even if you won't sign).")
        st.stop()

    # Optional wallet signature verification
    if wallet_address.strip() and signature.strip():
        try:
            msg = encode_defunct(text=msg_to_sign)
            recovered = Account.recover_message(msg, signature=signature)
            if recovered.lower() != wallet_address.strip().lower():
                st.error(
                    "Signature does not match wallet address.\n\n"
                    f"Recovered: {recovered}\nEntered:   {wallet_address}"
                )
                st.stop()
        except Exception as e:
            st.error(f"Signature verification failed: {e}")
            st.stop()
    else:
        # store empty signature fields if none provided
        wallet_address, signature = "", ""

    new_block = make_block(
        chain[-1],
        actor=actor,
        action=action,
        amount=float(amt_str),
        note=note,
        wallet_address=wallet_address,
        signed_message=msg_to_sign,
        signature=signature,
    )
    chain.append(new_block)
    save_chain(to_dicts(chain))
    st.success(f"Added {action} of {fmt_money(float(amt_str), currency)} by {actor}")

    # clear locked message so next tx must regenerate
    st.session_state.locked_msg = ""
    st.session_state.locked_ts = 0

st.divider()

# ---------- Ledger view ----------
st.subheader("Ledger")
valid = validate_chain(chain)
st.write(f"Chain status: {'✅ Valid' if valid else '❌ INVALID'}")

df = pd.DataFrame(
    [
        {
            "index": b.index,
            "time": pretty_time(b.timestamp),
            "actor": b.actor,
            "action": b.action,
            "amount": fmt_money(b.amount, currency),
            "note": b.note,
            "prev_hash": str(b.prev_hash)[:10] + "…",
            "hash": str(b.hash)[:10] + "…",
            "wallet": (b.wallet_address[:10] + "…") if b.wallet_address else "",
            "signed?": "yes" if b.signature else "no",
        }
        for b in chain
    ]
)
st.dataframe(df, use_container_width=True, height=280)

# ---------- Stats ----------
st.subheader("Stats & Progress")
txs = [b for b in chain if b.action in ("DEPOSIT", "WITHDRAW")]
total_in = sum(b.amount for b in txs if b.action == "DEPOSIT")
total_out = sum(b.amount for b in txs if b.action == "WITHDRAW")
net = round(total_in - total_out, 2)

m1, m2, m3 = st.columns(3)
m1.metric("Total Deposited", fmt_money(total_in, currency))
m2.metric("Total Withdrawn", fmt_money(total_out, currency))
m3.metric("Current Balance", fmt_money(net, currency))

if goal > 0:
    pct = min(100, int(100 * net / goal))
    st.progress(pct, text=f"{pct}% of {fmt_money(goal, currency)} goal")

# ---------- Contributions charts ----------
# Build per-actor net (deposits minus withdrawals)
by_actor = {}
for b in txs:
    by_actor.setdefault(b.actor, 0.0)
    if b.action == "DEPOSIT":
        by_actor[b.actor] += b.amount
    elif b.action == "WITHDRAW":
        by_actor[b.actor] -= b.amount

if by_actor:
    plot_df = pd.DataFrame({
        "actor": list(by_actor.keys()),
        "net_contribution": list(by_actor.values())
    })

    # Pie = share of total **positive** deposits (ignores withdrawals)
    deposits_only = plot_df.copy()
    deposits_only["positive_deposit"] = deposits_only["net_contribution"].clip(lower=0)
    total_pos = float(deposits_only["positive_deposit"].sum())
    pie_ready = total_pos > 0
    if pie_ready:
        deposits_only["share"] = deposits_only["positive_deposit"] / total_pos  # 0..1

    sym = CURRENCY_SYMBOLS.get(currency, "$")
    chart_type = st.radio(
        "Contribution charts",
        ["Both", "Bar only", "Pie only"],
        help="Bar shows NET (deposits − withdrawals). Pie shows share of total deposits."
    )

    # --- Bar (net) ---
    bar = (
        alt.Chart(plot_df)
        .mark_bar()
        .encode(
            x=alt.X("actor:N", axis=alt.Axis(labelAngle=0, title="Contributor")),
            y=alt.Y("net_contribution:Q", axis=alt.Axis(title=f"Net Contribution ({sym})")),
            tooltip=[
                alt.Tooltip("actor:N", title="Actor"),
                alt.Tooltip("net_contribution:Q", title=f"Net ({sym})", format=",.2f"),
            ],
        )
        .properties(height=300)
    )

    # --- Pie (share of deposits) ---
    if pie_ready:
        pie_source = deposits_only[deposits_only["positive_deposit"] > 0]
        pie = (
            alt.Chart(pie_source)
            .mark_arc(outerRadius=140)
            .encode(
                theta=alt.Theta("positive_deposit:Q", stack=True),
                color=alt.Color("actor:N", legend=alt.Legend(title="Depositors")),
                tooltip=[
                    alt.Tooltip("actor:N", title="Actor"),
                    alt.Tooltip("positive_deposit:Q", title=f"Deposited ({sym})", format=",.2f"),
                    alt.Tooltip("share:Q", title="Share", format=".1%"),  # <-- precomputed percentage
                ],
            )
            .properties(height=300)
        )
    else:
        pie = alt.Chart(pd.DataFrame({"msg": ["No positive deposits yet"]})).mark_text(size=14).encode(text="msg:N")

    if chart_type == "Both":
        col_bar, col_pie = st.columns(2)
        with col_bar:
            st.altair_chart(bar, use_container_width=True)
        with col_pie:
            st.altair_chart(pie, use_container_width=True)
        st.caption("Bar: net contributions (deposits − withdrawals). Pie: share of total deposits.")
    elif chart_type == "Bar only":
        st.altair_chart(bar, use_container_width=True)
        st.caption("Net contributions (deposits − withdrawals).")
    else:  # Pie only
        st.altair_chart(pie, use_container_width=True)
        st.caption("Share of total deposits (ignores withdrawals).")
else:
    st.info("No contributors yet.")



# ---------- Coach ----------
st.subheader("Coach Summary")
rows_dict = [vars(b) for b in chain]
sym = CURRENCY_SYMBOLS.get(currency, "$")
summary_text = ai_studio_summary(rows_dict, goal, sym) if use_ai else local_summary(rows_dict, goal, sym)
# Clean and show as plain text so no accidental markdown/bold
st.text(clean_ai_text(summary_text))


# ---------- Export / Reset ----------
st.divider()
cx, cy = st.columns(2)
with cx:
    st.download_button(
        "Download ledger CSV",
        data=pd.DataFrame([vars(b) for b in chain]).to_csv(index=False),
        file_name="ledger.csv",
        mime="text/csv",
    )
with cy:
    if st.button("Reset (delete all non-genesis blocks)"):
        chain = [chain[0]]
        save_chain([vars(chain[0])])
        st.warning("Ledger reset. (Genesis kept.)")
