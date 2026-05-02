import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt


st.set_page_config(
    page_title="Retirement Dashboard",
    page_icon="💰",
    layout="wide",
)


def money(value):
    return f"${value:,.0f}"


def project_retirement(
    current_age,
    retirement_age,
    current_savings,
    yearly_contribution,
    stock_percent,
    bond_percent,
    cash_percent,
    stock_return,
    bond_return,
    cash_return,
    inflation_rate,
):
    years = retirement_age - current_age
    rows = []
    balance = current_savings

    weighted_return = (
        stock_percent * stock_return
        + bond_percent * bond_return
        + cash_percent * cash_return
    ) / 10000

    for year in range(years + 1):
        age = current_age + year
        real_balance = balance / ((1 + inflation_rate / 100) ** year)

        rows.append(
            {
                "Age": age,
                "Year": year,
                "Balance": balance,
                "Inflation Adjusted Balance": real_balance,
            }
        )

        if year < years:
            balance = (balance + yearly_contribution) * (1 + weighted_return)

    return pd.DataFrame(rows), weighted_return


def project_allocation_scenario(
    current_age,
    retirement_age,
    current_savings,
    yearly_contribution,
    stock_percent,
    bond_percent,
    cash_percent,
    stock_return,
    bond_return,
    cash_return,
    inflation_rate,
    label,
):
    df, weighted_return = project_retirement(
        current_age,
        retirement_age,
        current_savings,
        yearly_contribution,
        stock_percent,
        bond_percent,
        cash_percent,
        stock_return,
        bond_return,
        cash_return,
        inflation_rate,
    )
    df["Scenario"] = label
    df["Expected Return"] = weighted_return
    return df


st.title("Retirement Dashboard")
st.write(
    "Use this dashboard to estimate how much money could be available at retirement "
    "and compare how different investment allocations may affect the outcome."
)

with st.sidebar:
    st.header("Personal Details")
    current_age = st.number_input("Current age", min_value=18, max_value=90, value=55)
    retirement_age = st.number_input("Retirement age", min_value=current_age + 1, max_value=100, value=67
    )

    st.header("Current Money")
    current_savings = st.number_input(
        "Current retirement savings",
        min_value=0,
        value=250000,
        step=5000,
    )
    yearly_contribution = st.number_input(
        "Yearly contribution",
        min_value=0,
        value=12000,
        step=1000,
    )

    st.header("Main Allocation")
    stock_percent = st.slider("Stocks %", 0, 100, 60)
    bond_percent = st.slider("Bonds %", 0, 100, 30)
    cash_percent = 100 - stock_percent - bond_percent

    if cash_percent < 0:
        st.error("Stocks plus bonds cannot be more than 100%.")
        st.stop()

    st.write(f"Cash %: **{cash_percent}%**")

    st.header("Assumptions")
    stock_return = st.slider("Expected stock return %", 0.0, 15.0, 7.0, 0.1)
    bond_return = st.slider("Expected bond return %", 0.0, 10.0, 4.0, 0.1)
    cash_return = st.slider("Expected cash return %", 0.0, 8.0, 2.0, 0.1)
    inflation_rate = st.slider("Inflation %", 0.0, 8.0, 2.5, 0.1)

    st.header("Retirement Goal")
    yearly_spending_goal = st.number_input(
        "Desired yearly retirement income",
        min_value=0,
        value=60000,
        step=5000,
    )
    withdrawal_rate = st.slider("Withdrawal rate %", 2.0, 6.0, 4.0, 0.1)


main_df, expected_return = project_retirement(
    current_age,
    retirement_age,
    current_savings,
    yearly_contribution,
    stock_percent,
    bond_percent,
    cash_percent,
    stock_return,
    bond_return,
    cash_return,
    inflation_rate,
)

final_balance = main_df.iloc[-1]["Balance"]
final_real_balance = main_df.iloc[-1]["Inflation Adjusted Balance"]
needed_balance = yearly_spending_goal / (withdrawal_rate / 100)
income_from_balance = final_balance * (withdrawal_rate / 100)
gap = final_balance - needed_balance

col1, col2, col3, col4 = st.columns(4)
col1.metric("Projected retirement savings", money(final_balance))
col2.metric("Today's dollars", money(final_real_balance))
col3.metric("Estimated yearly income", money(income_from_balance))
col4.metric("Goal gap", money(gap))

st.subheader("Main Projection")

fig, ax = plt.subplots()
ax.plot(main_df["Age"], main_df["Balance"], label="Projected balance")
ax.plot(
    main_df["Age"],
    main_df["Inflation Adjusted Balance"],
    label="Today's dollars",
    linestyle="--",
)
ax.set_xlabel("Age")
ax.set_ylabel("Balance")
ax.legend()
ax.grid(True, alpha=0.3)
st.pyplot(fig)

st.subheader("Compare Allocation Strategies")

scenario_rows = []
scenarios = [
    ("Conservative", 30, 55, 15),
    ("Balanced", 60, 30, 10),
    ("Growth", 80, 15, 5),
    ("Custom", stock_percent, bond_percent, cash_percent),
]

for label, stocks, bonds, cash in scenarios:
    scenario_rows.append(
        project_allocation_scenario(
            current_age,
            retirement_age,
            current_savings,
            yearly_contribution,
            stocks,
            bonds,
            cash,
            stock_return,
            bond_return,
            cash_return,
            inflation_rate,
            label,
        )
    )

scenario_df = pd.concat(scenario_rows, ignore_index=True)

fig2, ax2 = plt.subplots()
for scenario_name in scenario_df["Scenario"].unique():
    plot_df = scenario_df[scenario_df["Scenario"] == scenario_name]
    ax2.plot(plot_df["Age"], plot_df["Balance"], label=scenario_name)

ax2.set_xlabel("Age")
ax2.set_ylabel("Balance")
ax2.legend()
ax2.grid(True, alpha=0.3)
st.pyplot(fig2)

summary = (
    scenario_df.groupby("Scenario")
    .tail(1)[["Scenario", "Balance", "Inflation Adjusted Balance", "Expected Return"]]
    .copy()
)
summary["Expected Return"] = summary["Expected Return"] * 100

st.dataframe(
    summary,
    column_config={
        "Balance": st.column_config.NumberColumn("Retirement Balance", format="$%.0f"),
        "Inflation Adjusted Balance": st.column_config.NumberColumn(
            "Today's Dollars", format="$%.0f"
        ),
        "Expected Return": st.column_config.NumberColumn(
            "Expected Annual Return", format="%.2f%%"
        ),
    },
    hide_index=True,
    use_container_width=True,
)

st.subheader("Year-by-Year Details")
st.dataframe(
    main_df,
    column_config={
        "Balance": st.column_config.NumberColumn("Balance", format="$%.0f"),
        "Inflation Adjusted Balance": st.column_config.NumberColumn(
            "Today's Dollars", format="$%.0f"
        ),
    },
    hide_index=True,
    use_container_width=True,
)

st.caption(
    "This is an educational estimate, not financial advice. Real investment returns, "
    "taxes, Social Security, pensions, healthcare costs, and market timing can change the result."
)