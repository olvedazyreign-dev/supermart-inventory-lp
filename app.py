import streamlit as st
from scipy.optimize import linprog
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="SuperMart Inventory LP",
    page_icon="📦",
    layout="wide",
)

st.title("Maximizing Profit Through Optimal Inventory Allocation")
st.caption("SuperMart Fresh & Go — Linear Programming model")

# ----------------------------------------------------------------------
# PALITAN ang mga numerong ito ng totoong data mo
# ----------------------------------------------------------------------
DRY_COST, DRY_SPACE, DRY_PROFIT = 120.0, 0.5, 45.0
BEV_COST, BEV_SPACE, BEV_PROFIT = 80.0, 0.3, 28.0

st.sidebar.header("Constraints")
budget = st.sidebar.slider("Budget (PHP)", 100_000, 2_000_000, 800_000, 10_000)
shelf = st.sidebar.slider("Shelf space (sqm)", 50, 500, 200, 5)
storage = st.sidebar.slider("Storage capacity (units)", 500, 5000, 2000, 100)

# ----------------------------------------------------------------------
# Solve
# ----------------------------------------------------------------------
res = linprog(
    c=[-DRY_PROFIT, -BEV_PROFIT],           # negated: linprog minimizes
    A_ub=[
        [DRY_COST, BEV_COST],
        [DRY_SPACE, BEV_SPACE],
        [1.0, 1.0],
    ],
    b_ub=[budget, shelf, storage],
    bounds=[(0, None), (0, None)],
    method="highs",
)

if res.success:
    dry, bev = res.x
    profit = -res.fun

    c1, c2, c3 = st.columns(3)
    c1.metric("Max monthly gross profit", f"PHP {profit:,.0f}")
    c2.metric("Dry Goods units", f"{dry:,.0f}")
    c3.metric("Beverages units", f"{bev:,.0f}")

    left, right = st.columns(2)

    with left:
        st.subheader("Optimal allocation")
        fig = go.Figure(
            go.Bar(
                x=["Dry Goods", "Beverages"],
                y=[dry, bev],
                marker_color=["#2E5AAC", "#6FA8DC"],
                text=[f"{dry:,.0f}", f"{bev:,.0f}"],
                textposition="outside",
            )
        )
        fig.update_layout(
            yaxis_title="Units",
            showlegend=False,
            height=380,
            margin=dict(t=20, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

    with right:
        st.subheader("Constraint usage")
        usage = pd.DataFrame(
            {
                "Constraint": ["Budget", "Shelf space", "Storage"],
                "Used": [
                    dry * DRY_COST + bev * BEV_COST,
                    dry * DRY_SPACE + bev * BEV_SPACE,
                    dry + bev,
                ],
                "Available": [budget, shelf, storage],
            }
        )
        usage["% used"] = (usage["Used"] / usage["Available"] * 100).round(1)
        st.dataframe(usage, hide_index=True, use_container_width=True)

        binding = usage[usage["% used"] >= 99.5]["Constraint"].tolist()
        if binding:
            st.info(f"Binding constraint(s): {', '.join(binding)}")
        else:
            st.info("Walang binding constraint — may natitirang slack sa lahat.")

else:
    st.error(
        "Walang feasible solution sa mga constraint na ito. "
        "Subukan mong taasan ang budget, shelf space, o storage."
    )

with st.expander("How this model works"):
    st.markdown(
        f"""
        **Decision variables:** units of Dry Goods and Beverages to stock.

        **Objective:** maximize monthly gross profit
        (PHP {DRY_PROFIT:.0f}/unit Dry Goods, PHP {BEV_PROFIT:.0f}/unit Beverages).

        **Constraints:**
        - Budget: PHP {DRY_COST:.0f}/unit and PHP {BEV_COST:.0f}/unit
        - Shelf space: {DRY_SPACE}/unit and {BEV_SPACE}/unit sqm
        - Storage: total units capped

        Solved with SciPy's HiGHS simplex solver. If a constraint hits 100%,
        it is binding — relaxing it would raise profit.
        """
    )
