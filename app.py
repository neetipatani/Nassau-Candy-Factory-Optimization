

import streamlit as st
import pandas as pd
from pathlib import Path

# --------------------------------------------------
# PAGE CONFIGURATION
# --------------------------------------------------

st.set_page_config(
    page_title="Nassau Candy Factory Optimization",
    page_icon="🍬",
    layout="wide"
)

# --------------------------------------------------
# CUSTOM DESIGN
# --------------------------------------------------

st.markdown("""
<style>
.main {
    background-color: #F5F7F6;
}
[data-testid="stMetric"] {
    background-color: white;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #DCE5DF;
}
h1 {
    color: #304D3C;
}
h2, h3 {
    color: #405C4A;
}
</style>
""", unsafe_allow_html=True)

# --------------------------------------------------
# TITLE
# --------------------------------------------------

st.title("🍬 NASSAU CANDY DISTRIBUTOR")
st.subheader("Factory Performance & Shipping Optimization Dashboard")

st.write(
    "An interactive business intelligence dashboard "
    "for factory performance, product sales, profitability "
    "and shipping analysis."
)

st.divider()

# --------------------------------------------------
# LOAD DATASET
# --------------------------------------------------

@st.cache_data
def load_data():

    folder = Path(__file__).parent

    csv_files = list(folder.glob("*.csv"))

    if not csv_files:
        csv_files = list((folder / "data").glob("*.csv")) \
            if (folder / "data").exists() else []

    if not csv_files:
        st.error("CSV dataset not found. Please upload your CSV to GitHub.")
        st.stop()

    # Prefer the Nassau Candy dataset
    file_path = next(
        (f for f in csv_files
         if "nassau" in f.name.lower()),
        csv_files[0]
    )

    data = pd.read_csv(file_path, encoding="utf-8-sig")

    # Clean column names
    data.columns = data.columns.astype(str).str.strip()

    # Match columns regardless of capitalization or extra spaces
    normalized = {
        str(col).strip().lower().replace("_", " ").replace("-", " "): col
        for col in data.columns
    }

    aliases = {
        "Product Name": ["product name", "product"],
        "Sales": ["sales", "total sales"],
        "Units": ["units", "quantity"],
        "Gross Profit": ["gross profit", "profit"],
        "Cost": ["cost", "total cost"],
        "Order ID": ["order id", "order number"],
        "Region": ["region"],
        "Ship Mode": ["ship mode", "shipping mode"],
        "Shipping Lead Time": [
            "shipping lead time", "lead time", "shipping days"
        ],
        "Current Factory": ["current factory", "factory"]
    }

    rename_columns = {}

    for standard_name, possible_names in aliases.items():
        for name in possible_names:
            key = name.lower().strip()
            if key in normalized:
                rename_columns[normalized[key]] = standard_name
                break

    data.rename(columns=rename_columns, inplace=True)

    # Required product column
    if "Product Name" not in data.columns:
        st.error(
            "Product Name column not found. "
            "Please check your CSV column headings."
        )
        st.stop()

    # Add missing optional columns
    defaults = {
        "Sales": 0,
        "Units": 0,
        "Gross Profit": 0,
        "Cost": 0,
        "Order ID": None,
        "Region": "Unknown",
        "Ship Mode": "Unknown",
        "Shipping Lead Time": None
    }

    for column, default in defaults.items():
        if column not in data.columns:
            data[column] = default

    # Convert numerical columns
    numeric_columns = [
        "Sales",
        "Units",
        "Gross Profit",
        "Cost",
        "Shipping Lead Time"
    ]

    for column in numeric_columns:
        data[column] = pd.to_numeric(
            data[column], errors="coerce"
        )

    data[numeric_columns] = data[numeric_columns].fillna(0)

    # --------------------------------------------------
    # FACTORY MAPPING
    # --------------------------------------------------

    factory_mapping = {
        "Nutty Crunch Surprise": "Lot's O' Nuts",
        "Fudge Mallows": "Lot's O' Nuts",
        "Scrumdiddlyumptious": "Lot's O' Nuts",

        "Milk Chocolate": "Wicked Choccy's",
        "Triple Dazzle Caramel": "Wicked Choccy's",

        "Laffy Taffy": "Sugar Shack",
        "SweeTARTS": "Sugar Shack",
        "Nerds": "Sugar Shack",
        "Fun Dip": "Sugar Shack",
        "Fizzy Lifting Drinks": "Sugar Shack",

        "Everlasting Gobstopper": "Secret Factory",
        "Lickable Wallpaper": "Secret Factory",
        "Wonka Gum": "Secret Factory",

        "Hair Toffee": "The Other Factory",
        "Kazookles": "The Other Factory"
    }

    def assign_factory(product):

        product = str(product).lower()

        for product_name, factory in factory_mapping.items():
            if product_name.lower() in product:
                return factory

        return "Unmapped"

    # Recreate factory mapping from product names
    data["Current Factory"] = data["Product Name"].apply(
        assign_factory
    )

    # Calculate lead time if it is missing or entirely zero
    if data["Shipping Lead Time"].sum() == 0:
        if "Order Date" in data.columns and "Ship Date" in data.columns:
            order_dates = pd.to_datetime(
                data["Order Date"], dayfirst=True, errors="coerce"
            )
            ship_dates = pd.to_datetime(
                data["Ship Date"], dayfirst=True, errors="coerce"
            )

            data["Shipping Lead Time"] = (
                ship_dates - order_dates
            ).dt.days.fillna(0)

    return data


df = load_data()

# --------------------------------------------------
# SIDEBAR FILTERS
# --------------------------------------------------

st.sidebar.title("Dashboard Filters")

st.sidebar.caption("Select options to filter the dashboard.")

def add_filter(column, label):

    options = sorted(
        df[column].dropna().astype(str).unique().tolist()
    )

    return st.sidebar.multiselect(
        label,
        options,
        default=options
    )

selected_factories = add_filter(
    "Current Factory", "Filter by Factory"
)

selected_regions = add_filter(
    "Region", "Filter by Region"
)

selected_shipping = add_filter(
    "Ship Mode", "Filter by Shipping Mode"
)

selected_products = add_filter(
    "Product Name", "Filter by Product"
)

# --------------------------------------------------
# APPLY FILTERS
# --------------------------------------------------

filtered_df = df[
    df["Current Factory"].astype(str).isin(selected_factories)
    & df["Region"].astype(str).isin(selected_regions)
    & df["Ship Mode"].astype(str).isin(selected_shipping)
    & df["Product Name"].astype(str).isin(selected_products)
].copy()

if filtered_df.empty:
    st.warning("No records found. Please change your filters.")
    st.stop()

# --------------------------------------------------
# KPI CALCULATIONS
# --------------------------------------------------

total_sales = filtered_df["Sales"].sum()
total_profit = filtered_df["Gross Profit"].sum()
total_units = filtered_df["Units"].sum()

if filtered_df["Order ID"].notna().any():
    total_orders = filtered_df["Order ID"].nunique()
else:
    total_orders = len(filtered_df)

avg_lead_time = filtered_df[
    "Shipping Lead Time"
].mean()

# --------------------------------------------------
# EXECUTIVE OVERVIEW
# --------------------------------------------------

st.header("Executive Overview")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Sales", f"{total_sales:,.2f}")
col2.metric("Gross Profit", f"{total_profit:,.2f}")
col3.metric("Total Units", f"{total_units:,.0f}")
col4.metric("Total Orders", f"{total_orders:,.0f}")

st.divider()

# --------------------------------------------------
# FACTORY PERFORMANCE
# --------------------------------------------------

st.header("Factory Performance")

factory_sales = (
    filtered_df.groupby("Current Factory")["Sales"]
    .sum()
    .sort_values(ascending=False)
)

factory_profit = (
    filtered_df.groupby("Current Factory")["Gross Profit"]
    .sum()
    .sort_values(ascending=False)
)

col1, col2 = st.columns(2)

with col1:
    st.subheader("Sales Contribution by Factory")
    st.bar_chart(factory_sales)

with col2:
    st.subheader("Gross Profit by Factory")
    st.bar_chart(factory_profit)

# --------------------------------------------------
# PRODUCT PERFORMANCE
# --------------------------------------------------

st.divider()
st.header("Product-wise Sales Analysis")

product_sales = (
    filtered_df.groupby("Product Name")["Sales"]
    .sum()
    .sort_values(ascending=False)
    .head(10)
)

st.bar_chart(product_sales)

# --------------------------------------------------
# SHIPPING ANALYSIS
# --------------------------------------------------

st.divider()
st.header("Shipping & Logistics Analysis")

col1, col2 = st.columns(2)

shipping_sales = (
    filtered_df.groupby("Ship Mode")["Sales"]
    .sum()
    .sort_values(ascending=False)
)

shipping_lead = (
    filtered_df.groupby("Ship Mode")["Shipping Lead Time"]
    .mean()
    .sort_values(ascending=False)
)

with col1:
    st.subheader("Sales by Shipping Mode")
    st.bar_chart(shipping_sales)

with col2:
    st.subheader("Average Shipping Lead Time")
    st.bar_chart(shipping_lead)

st.metric(
    "Overall Average Shipping Lead Time",
    f"{avg_lead_time:,.2f} days"
)

# --------------------------------------------------
# REGIONAL ANALYSIS
# --------------------------------------------------

st.divider()
st.header("Regional Sales Analysis")

region_sales = (
    filtered_df.groupby("Region")["Sales"]
    .sum()
    .sort_values(ascending=False)
)

st.bar_chart(region_sales)

# --------------------------------------------------
# FACTORY COMPARISON TABLE
# --------------------------------------------------

st.divider()
st.header("Factory Comparison")

factory_summary = (
    filtered_df.groupby("Current Factory")
    .agg(
        Total_Sales=("Sales", "sum"),
        Gross_Profit=("Gross Profit", "sum"),
        Total_Units=("Units", "sum"),
        Average_Lead_Time=("Shipping Lead Time", "mean")
    )
    .reset_index()
)

st.dataframe(
    factory_summary,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# DATA PREVIEW
# --------------------------------------------------

st.divider()
st.header("Dataset Preview")

st.caption(
    f"Showing {len(filtered_df):,} records after applying filters."
)

st.dataframe(
    filtered_df,
    use_container_width=True,
    hide_index=True
)

# --------------------------------------------------
# FOOTER
# --------------------------------------------------

st.divider()

st.markdown("""
<div style="text-align:center; color:gray;">
    Nassau Candy – Factory Reallocation & Shipping Optimization
    <br>
    Developed by Neeti Patani | Microsoft Power BI & Streamlit
</div>
""", unsafe_allow_html=True)

