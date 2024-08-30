import os
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from process_data import process_pdfs  # We only import process_pdfs

# Streamlit configuration
st.set_page_config(
    page_title="Monthly Expenses",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSV file and logo path
csv_path = "data/mercadata.csv"
logo_path = "images/logo_santander.png"  # Change this to the location of your logo file

# Display the logo as a banner at the top of the page
if os.path.exists(logo_path):
    st.image(logo_path, width=200, use_column_width=True)  # Adjust the width of the logo to your preference
else:
    st.warning(f"Logo not found in {logo_path}")

# Upload Excel files
uploaded_files = st.file_uploader("Load your Excel files", type="pdf", accept_multiple_files=True)

if uploaded_files:
    st.success(f"You have uploaded {len(uploaded_files)} Excel file(s).")

    #  Process PDF files when the button is pressed
    if st.button("Process Excel"):
        try:
            # Passing PDF files to the processing function
            process_pdfs(uploaded_files)  # Make sure that this function is well defined in process_data.py
            st.success("Excel files processed correctly.")
        except Exception as e:
            st.error(f"Error processing Excel files: {e}")
else:
    st.warning("Please, upload at least one Excel file to continue.")

# Sidebar info
with st.sidebar:
    st.title('📈 Monthly Expenses')
    

    # Filter by month
    if os.path.exists(csv_path):
        try:
            data = pd.read_csv(csv_path)
            data["fecha"] = pd.to_datetime(data["fecha"], format="%d/%m/%Y %H:%M", dayfirst=True)
            data.set_index("fecha", inplace=True)
            
            month_start_dates = data.index.to_period("M").to_timestamp().drop_duplicates().sort_values()
            selected_month_start = st.selectbox("Select the month", month_start_dates.strftime('%Y-%m'), index=0)
            selected_month_start = pd.Timestamp(selected_month_start)
            filtered_data_by_month = data[data.index.to_period("M").start_time == selected_month_start]
            
            # Filter by category
            selected_category = st.selectbox("Select the category", data["categoría"].unique())
            filtered_data_by_categories = data[data["categoría"] == selected_category]
        except Exception as e:
            st.error(f"Error reading CSV file: {e}")
    else:
        st.error(f"File {csv_path} not found. Make sure  `process_data.py` has been executed correctly.")

    st.subheader("About the App")
    st.write('''
        - This application aims to analyze personal spending patterns in different categories and over time.
        - Beta testing based on: https://mercadata.streamlit.app/
    ''')

# Verify if the CSV file exists and is not empty
if os.path.exists(csv_path):
    try:
        data = pd.read_csv(csv_path)
        if not data.empty:
            data["fecha"] = pd.to_datetime(data["fecha"], format="%d/%m/%Y %H:%M", dayfirst=True)
            data.set_index("fecha", inplace=True)

            # Relevant metrics
            total_spent = data["precio"].sum()
            total_purchases = data["identificativo de ticket"].nunique()
            avg_spent_per_purchase = data.groupby("identificativo de ticket")["precio"].sum().mean()
            category_with_highest_spent = data.groupby("categoría")["precio"].sum().idxmax()
            total_items_sold = data['item'].nunique()
            avg_spent_per_month = data["precio"].resample('M').sum().mean()
            total_tickets_per_month = data.groupby(data.index.to_period('M')).size().mean()

            # Create columns for metrics
            col1, col2, col3 = st.columns(3)

            # Display metrics in columns
            with col1:
                st.metric(label="Total Expense", value=f"€{total_spent:.2f}")
                st.metric(label="Average Spending per Purchase", value=f"€{avg_spent_per_purchase:.2f}")
                st.metric(label="Total Number of Purchases", value=total_purchases)
                st.metric(label="Items Sold", value=total_items_sold)

            with col2:
                st.metric(label="Highest Spending Category", value=category_with_highest_spent)
                st.metric(label="Average Monthly Expense", value=f"€{avg_spent_per_month:.2f}")
                st.metric(label="Tickets per Month", value=f"{total_tickets_per_month:.2f}")

            with col3:
                st.metric(label="Total Spent in Selected Month", value=f"€{filtered_data_by_month['precio'].sum():.2f}")
                st.metric(label="Number of Purchases in Selected Month", value=filtered_data_by_month['identificativo de ticket'].nunique())
                st.metric(label="Category with the Highest Expenditure in the Selected Month", value=filtered_data_by_month.groupby("categoría")["precio"].sum().idxmax())

            # Create a single row with the main graphics
            col1, col2, col3 = st.columns(3)

            with col1:
                # Distribution of Spending by Category
                total_price_per_category = data.groupby("categoría")["precio"].sum().reset_index()
                fig_pie = px.pie(total_price_per_category, values='precio', names='categoría', title='Distribution of Spending by Category')
                st.plotly_chart(fig_pie)

            with col2:
                # Total Expense per Month
                monthly_expense = data["precio"].resample('M').sum().reset_index()
                fig_bar = px.bar(monthly_expense, x='fecha', y='precio', labels={'fecha': 'Mes', 'precio': 'Gasto (€)'})
                st.plotly_chart(fig_bar)

            with col3:
                # Average Price per Category
                avg_price_per_category = data.groupby("categoría")["precio"].mean().reset_index().sort_values(by="precio", ascending=False)
                fig_bar_avg = px.bar(avg_price_per_category, x='categoría', y='precio', labels={'precio': 'Precio Medio (€)'})
                st.plotly_chart(fig_bar_avg)

            # Time Spending Analysis and Top 10 Items
            col1, col2 = st.columns(2)

            with col1:
                # Time Spending Analysis
                daily_expense = data["precio"].resample('D').sum().reset_index()
                fig_line = px.line(daily_expense, x='fecha', y='precio', labels={'fecha': 'Fecha', 'precio': 'Gasto (€)'})
                st.plotly_chart(fig_line)

            with col2:
                # Top 10 Highest Spending Items
                top_items = data.groupby('item')['precio'].sum().nlargest(10).reset_index()
                fig_top_items = px.bar(top_items, x='item', y='precio', labels={'item': 'Item', 'precio': 'Gasto (€)'})
                st.plotly_chart(fig_top_items)

            # Filtered Data
            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Filtered Data by Category")
                st.dataframe(filtered_data_by_categories)

            with col2:
                st.subheader("Filtered Data by Month")
                st.dataframe(filtered_data_by_month)

            # Heatmap of daily and hourly expenditure
            st.subheader("Heatmap of Spending per Day and Hour")
            data['day_of_week'] = data.index.dayofweek
            data['hour_of_day'] = data.index.hour
            heatmap_data = data.pivot_table(values='precio', index='hour_of_day', columns='day_of_week', aggfunc='sum', fill_value=0)
            fig_heatmap = go.Figure(data=go.Heatmap(z=heatmap_data.values, x=['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'], y=list(range(24)), colorscale='Viridis'))
            fig_heatmap.update_layout(xaxis_title='Day of the Week', yaxis_title='Time of Day')
            st.plotly_chart(fig_heatmap)

        else:
            st.warning("The CSV file is empty. Please make sure that `process_data.py` has generated data correctly.")
    
    except Exception as e:
        st.error(f"Error reading CSV file: {e}")
else:
    st.error(f"File {csv_path} not found. Make sure `process_data.py` has been executed correctly.")