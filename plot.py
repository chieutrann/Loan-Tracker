import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from trans import auto_translate


def plot_payment_status_pie_chart(data, language, translations):
    # Get translated column names
    Amount_col = translations[language]["Amount"]
    Description_col = translations[language]["Description"]
    Status_col = translations[language]["Status"]

    # Clean and prepare data
    data[Amount_col] = data[Amount_col].replace(",", "", regex=True).astype(float)

    # Translate filter and label terms
    monthly_label = translations[language]["Monthly Payment"]
    yearly_label = translations[language]["Yearly Payment"]

    # Filter data
    monthly_df = data[data[Description_col] == monthly_label]
    yearly_df = data[data[Description_col] == yearly_label]

    # Group and sum amounts by status
    monthly_grouped = monthly_df.groupby(Status_col)[Amount_col].sum().reset_index()
    yearly_grouped = yearly_df.groupby(Status_col)[Amount_col].sum().reset_index()

    # Translate the actual status values (in case they're not already)
    monthly_grouped[Status_col] = monthly_grouped[Status_col].apply(lambda x: auto_translate(x, language, translations))
    yearly_grouped[Status_col] = yearly_grouped[Status_col].apply(lambda x: auto_translate(x, language, translations))

    # # Define translated color map with fallback color
    status_colors= {
        "Paid": "lightgreen",
        "Unpaid": "#FF3300"
    }


    translated_colors = {
        translations[language]["Paid"]: status_colors["Paid"],
        translations[language]["Unpaid"]: status_colors["Unpaid"]
    }
    # Translated chart titles
    monthly_title = translations[language]["Monthly Payment"]
    yearly_title = translations[language]["Yearly Payment"]
    chart_title = "Monthly vs Yearly Payments by Status"

    # Create subplots
    fig = make_subplots(
        rows=1, cols=2,
        specs=[[{"type": "domain"}, {"type": "domain"}]],
        subplot_titles=[monthly_title, yearly_title]
    )

    # Monthly pie chart
    fig.add_trace(
        go.Pie(
            labels=monthly_grouped[Status_col],
            values=monthly_grouped[Amount_col],
            name=monthly_title,
            text=monthly_grouped[Status_col],
            textinfo="percent+value",
            textposition="inside",
            insidetextorientation="radial",
            hoverinfo="label+percent+value",
            textfont=dict(family="Arial, sans-serif", size=18, color="black"),
            marker=dict(colors=[translated_colors[status] for status in monthly_grouped[Status_col]])
        ),
        row=1, col=1
    )

    # Yearly pie chart
    fig.add_trace(
        go.Pie(
            labels=yearly_grouped[Status_col],
            values=yearly_grouped[Amount_col],
            name=yearly_title,
            text=yearly_grouped[Status_col],
            textinfo="percent+value",
            textposition="inside",
            insidetextorientation="radial",
            hoverinfo="label+percent+value",
            textfont=dict(family="Arial, sans-serif", size=18, color="black"),
            marker=dict(colors=[translated_colors[status] for status in monthly_grouped[Status_col]])
        ),
        row=1, col=2
    )

    # Final layout
    fig.update_layout(
        title_text=chart_title,
        showlegend=True
    )

    # Render in Streamlit
    st.plotly_chart(fig)
