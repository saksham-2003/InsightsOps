import plotly.express as px
import plotly.graph_objects as go


def create_monthly_revenue_chart(monthly_data):
    fig = px.line(
        monthly_data,
        x="Order_Date",
        y="Revenue",
        markers=True,
        title="Monthly Revenue Trend"
    )

    fig.update_layout(
        xaxis_title="Month",
        yaxis_title="Revenue",
        hovermode="x unified"
    )

    return fig


def create_category_revenue_chart(category_data):
    fig = px.bar(
        category_data,
        x="Category",
        y="Revenue",
        title="Revenue by Category",
        text_auto=".2s"
    )

    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Revenue"
    )

    return fig


def create_category_profit_chart(category_data):
    fig = px.bar(
        category_data,
        x="Category",
        y="Profit",
        title="Profit by Category",
        text_auto=".2s"
    )

    fig.update_layout(
        xaxis_title="Category",
        yaxis_title="Profit"
    )

    return fig


def create_regional_chart(regional_data):
    fig = px.bar(
        regional_data,
        x="Region",
        y=["Revenue", "Profit"],
        barmode="group",
        title="Regional Revenue vs Profit"
    )

    fig.update_layout(
        xaxis_title="Region",
        yaxis_title="Amount"
    )

    return fig


def create_top_products_chart(product_data):
    sorted_data = product_data.sort_values(
        "Revenue",
        ascending=True
    )

    fig = px.bar(
        sorted_data,
        x="Revenue",
        y="Product_Name",
        orientation="h",
        title="Top 10 Products by Revenue"
    )

    fig.update_layout(
        xaxis_title="Revenue",
        yaxis_title="Product"
    )

    return fig


def create_profitability_chart(profitability_data):
    top_margin_products = (
        profitability_data
        .head(10)
        .sort_values("Profit_Margin")
    )

    fig = px.bar(
        top_margin_products,
        x="Profit_Margin",
        y="Product_Name",
        orientation="h",
        title="Top Products by Profit Margin"
    )

    fig.update_layout(
        xaxis_title="Profit Margin (%)",
        yaxis_title="Product"
    )

    return fig