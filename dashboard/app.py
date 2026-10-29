"""Live dashboard. Run from the repo root:  streamlit run dashboard/app.py --server.port 8502"""
import json
import os
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st

DB = os.getenv("DB_PATH", "localroute.db")

st.set_page_config(page_title="LocalRoute + PromptShield", layout="wide")
st.title("LocalRoute + PromptShield")
st.caption("Local Gemma 4 gateway · live view of every request")


def load() -> pd.DataFrame:
    if not os.path.exists(DB):
        return pd.DataFrame()
    with sqlite3.connect(DB) as con:
        try:
            df = pd.read_sql("SELECT * FROM requests ORDER BY ts DESC", con)
        except Exception:
            return pd.DataFrame()
    if not df.empty:
        df["time"] = df["ts"].apply(lambda t: datetime.fromtimestamp(t).strftime("%H:%M:%S"))
        df["pii_count"] = df["pii"].apply(lambda p: len(json.loads(p or "[]")))
    return df


@st.fragment(run_every="2s")
def live():
    df = load()
    if df.empty:
        st.info("No requests yet. Send one through http://localhost:8000/v1")
        return

    total = len(df)
    hits = int((df["cache"] == "hit").sum())
    blocked = int((df["verdict"] == "block").sum())
    model_calls = df[df["model"].notna() & (df["cache"] != "hit")]
    c = st.columns(5)
    c[0].metric("Requests", total)
    c[1].metric("Cache hits", hits, f"{hits / total:.0%} of requests", delta_color="off")
    c[2].metric("Attacks blocked", blocked)
    c[3].metric("PII items masked", int(df["pii_count"].sum()))
    c[4].metric("Model calls", len(model_calls))

    left, right = st.columns(2)
    with left:
        st.subheader("Who answered")
        who = df.apply(lambda r: "blocked" if r["verdict"] == "block" and pd.isna(r["model"])
                       else ("cache" if r["cache"] == "hit" else (r["model"] or "error")), axis=1)
        st.bar_chart(who.value_counts())
    with right:
        st.subheader("Average latency (ms)")
        path = df.apply(lambda r: "blocked" if r["verdict"] == "block" and pd.isna(r["model"])
                        else ("cache hit" if r["cache"] == "hit" else "model call"), axis=1)
        st.bar_chart(df.groupby(path)["latency_ms"].mean().round())

    left, right = st.columns(2)
    with left:
        st.subheader("OWASP LLM Top 10 findings")
        ow = df["owasp"].dropna() if "owasp" in df else pd.Series(dtype=str)
        if ow.empty:
            st.caption("No findings yet")
        else:
            st.bar_chart(ow.value_counts())
    with right:
        st.subheader("Which layer stopped attacks")
        layers = df[df["verdict"] == "block"]["layer"].dropna()
        if layers.empty:
            st.caption("No attacks yet")
        else:
            st.bar_chart(layers.value_counts())

    st.subheader("Blocked attacks")
    cols = [c for c in ["time", "layer", "owasp", "risk", "reason", "prompt", "image_text"] if c in df]
    att = df[df["verdict"] == "block"][cols]
    st.dataframe(att, use_container_width=True, hide_index=True)

    st.subheader("Recent requests")
    cols = [c for c in ["time", "session", "verdict", "risk", "cache", "model", "route_reason", "fallback",
                        "latency_ms", "pii", "prompt"] if c in df]
    st.dataframe(df[cols].head(30), use_container_width=True, hide_index=True)

    report = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "redteam", "report.md")
    if os.path.exists(report):
        with st.expander("Latest auto red-team report"):
            st.markdown(open(report, encoding="utf-8").read())


live()
