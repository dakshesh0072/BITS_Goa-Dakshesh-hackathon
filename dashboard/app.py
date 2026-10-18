import pandas as pd
import plotly.express as px
import requests
import streamlit as st


API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="AI/NLP Risk Engine",
    page_icon="??",
    layout="wide",
)

st.title("AI/NLP Financial Risk Engine")
st.caption("Real-time text analysis and sentiment-driven index rebalancing")


def call_api(endpoint: str, timeout: int = 180):
    response = requests.post(f"{API_URL}{endpoint}", timeout=timeout)
    response.raise_for_status()
    return response.json()


try:
    health = requests.get(f"{API_URL}/health", timeout=5).json()
    st.success(f"API status: {health['status']}")
except requests.RequestException:
    st.error("API is not running. Start it with: uvicorn src.main:app --reload")
    st.stop()

run_column, reset_column = st.columns(2)

with run_column:
    if st.button("Run Risk Analysis and Rebalance Index", type="primary"):
        try:
            with st.spinner(
                "Loading AI models and analyzing news and social-media data..."
            ):
                run_result = call_api("/run")

            st.session_state["signals"] = run_result["signals"]
            st.session_state["rebalance_result"] = run_result["rebalance_result"]
        except requests.RequestException:
            st.error(
                "The analysis took too long or the API stopped. Check the API terminal "
                "for model-download or model-loading progress, then try again."
            )

with reset_column:
    if st.button("Reset Portfolio to 10%"):
        call_api("/reset")
        st.session_state.pop("signals", None)
        st.session_state.pop("rebalance_result", None)
        st.rerun()


if "signals" in st.session_state:
    signals_df = pd.DataFrame(st.session_state["signals"])
    stocks_df = pd.DataFrame(st.session_state["rebalance_result"]["stocks"])

    st.subheader("Incoming Risk Signals")

    metric_one, metric_two, metric_three = st.columns(3)
    metric_one.metric("Items Processed", len(signals_df))
    metric_two.metric(
        "Average Sentiment",
        round(signals_df["sentiment_score"].mean(), 2),
    )
    metric_three.metric(
        "High-Impact Events",
        len(signals_df[signals_df["impact_score"] >= 7]),
    )

    st.dataframe(
        signals_df[
            [
                "source",
                "company",
                "sentiment_label",
                "sentiment_confidence",
                "sentiment_score",
                "event_classification",
                "event_confidence",
                "impact_score",
                "text",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Mock Index: Previous vs Rebalanced Weights")

    weights_chart = px.bar(
        stocks_df,
        x="ticker",
        y=["previous_weight", "new_weight"],
        barmode="group",
        labels={"value": "Weight (%)", "ticker": "Stock"},
        color_discrete_map={
            "previous_weight": "#94a3b8",
            "new_weight": "#2563eb",
        },
    )
    st.plotly_chart(weights_chart, use_container_width=True)

    st.subheader("Stock Sentiment Used for Rebalancing")
    st.dataframe(
        stocks_df[
            [
                "ticker",
                "initial_weight",
                "previous_weight",
                "sentiment_score",
                "new_weight",
            ]
        ],
        use_container_width=True,
        hide_index=True,
    )


history_response = requests.get(f"{API_URL}/history", timeout=10).json()
history_rows = []

for snapshot in history_response:
    for stock in snapshot["stocks"]:
        history_rows.append(
            {
                "rebalanced_at": snapshot["rebalanced_at"],
                "ticker": stock["ticker"],
                "weight": stock["new_weight"],
            }
        )

if history_rows:
    history_df = pd.DataFrame(history_rows)
    history_df["rebalanced_at"] = pd.to_datetime(history_df["rebalanced_at"])

    st.subheader("Index Weight History")
    history_chart = px.line(
        history_df,
        x="rebalanced_at",
        y="weight",
        color="ticker",
        markers=True,
        labels={
            "rebalanced_at": "Rebalance Time",
            "weight": "Weight (%)",
            "ticker": "Stock",
        },
    )
    st.plotly_chart(history_chart, use_container_width=True)
