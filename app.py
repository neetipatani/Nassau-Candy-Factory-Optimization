
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Nassau Candy Distributor",
    page_icon="🍬",
    layout="wide"
)

# Load dataset
@st.cache_data
def load_data():
    return pd.read_csv("Nassau Candy Distributor.csv")

df = load_data()

# Prepare data
df["Sales"] = pd.to_numeric(df["Sales"], errors="coerce")
df["Gross Profit"] = pd.to_numeric(df["Gross Profit"], errors="coerce")
df["Units"] = pd.to_numeric(df["Units"], errors="coerce")

st.title("🍬 Nassau Candy Distributor")
st.subheader("Factory Performance & Shipping Optimization Dashboard")

st.markdown("---")

# Sidebar filters
st.sidebar.header("Dashboard Filters")

factories = ["All"] + sorted(df["Current Factory"].dropna().unique().tolist())
selected_factory = st.sidebar.selectbox("Filter by Factory", factories)

regions = ["All"] + sorted(df["Region"].dropna().unique().tolist())
selected_region = st.sidebar.selectbox("Filter by Region", regions)

shipping_modes = ["All"] + sorted(df["Ship Mode"].dropna().unique().tolist())
selected_mode = st.sidebar.selectbox("Filter by Shipping Mode", shipping_modes)

products = ["All"] + sorted(df["Product Name"].dropna().unique().tolist())
selected_product = st.sidebar.selectbox("Filter by Product", products)

# Apply filters
filtered = df.copy()

if selected_factory != "All":
    filtered = filtered[filtered["Current Factory"] == selected_factory]

if selected_region != "All":
    filtered = filtered[filtered["Region"] == selected_region]

if selected_mode != "All":
    filtered = filtered[filtered["Ship Mode"] == selected_mode]

if selected_product != "All":
    filtered = filtered[filtered["Product Name"] == selected_product]

# KPI metrics
st.subheader("Business Performance Overview")

c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Sales", f"${filtered['Sales'].sum():,.2f}")
c2.metric("Gross Profit", f"${filtered['Gross Profit'].sum():,.2f}")
c3.metric("Total Units", f"{filtered['Units'].sum():,.0f}")
c4.metric("Total Orders", f"{filtered['Order ID'].nunique():,}")

st.markdown("---")

# Factory analysis
st.subheader("Factory Performance")

factory_data = (
    filtered.groupby("Current Factory", as_index=False)
    .agg(Sales=("Sales", "sum"),
         Gross_Profit=("Gross Profit", "sum"),
         Units=("Units", "sum"))
)

col1, col2 = st.columns(2)

with col1:
    fig = px.bar(
        factory_data,
        x="Current Factory",
        y="Sales",
        color="Current Factory",
        title="Sales Contribution by Factory"
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    fig = px.bar(
        factory_data,
        x="Current Factory",
        y="Gross_Profit",
        color="Current Factory",
        title="Gross Profit by Factory"
    )
    st.plotly_chart(fig, use_container_width=True)

# Product analysis
st.subheader("Product-wise Sales Performance")

product_data = (
    filtered.groupby("Product Name", as_index=False)
    .agg(Sales=("Sales", "sum"))
    .sort_values("Sales", ascending=False)
)

fig = px.bar(
    product_data.head(10),
    x="Sales",
    y="Product Name",
    orientation="h",
    title="Top 10 Products by Sales"
)
st.plotly_chart(fig, use_container_width=True)

# Shipping analysis
st.subheader("Shipping Performance")

shipping_data = (
    filtered.groupby("Ship Mode", as_index=False)
    .agg(Sales=("Sales", "sum"),
         Units=("Units", "sum"))
)

fig = px.bar(
    shipping_data,
    x="Ship Mode",
    y="Sales",
    title="Sales by Shipping Mode",
    color="Ship Mode"
)
st.plotly_chart(fig, use_container_width=True)

# Regional analysis
st.subheader("Regional Sales Analysis")

region_data = (
    filtered.groupby("Region", as_index=False)
    .agg(Sales=("Sales", "sum"))
)

fig = px.pie(
    region_data,
    names="Region",
    values="Sales",
    title="Sales Distribution by Region"
)
st.plotly_chart(fig, use_container_width=True)

# Dataset preview
with st.expander("View Dataset"):
    st.dataframe(filtered, use_container_width=True)

st.markdown("---")
st.caption("Nassau Candy Distributor | Factory Reallocation & Shipping Optimization Project")
