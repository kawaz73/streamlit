import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime

st.set_page_config(page_title="Illigo - Driver Payment Processor", layout="centered")
st.title("🚗 Driver Payment Processor")
st.markdown("Upload your monthly transaction report and driver list to generate a processed Excel file.")

# Upload CSV and Excel files
csv_file = st.file_uploader("Upload Wave CSV report", type=["csv"])
xlsx_file = st.file_uploader("Upload Excel driver list", type=["xlsx"])

if csv_file and xlsx_file:
    # --- Read CSV ---
    columns = ['timestamp','id','type','amount','fee','balance','currency','name',
               'mobile','busName','busMobile','clientReference','apiSessId']
    df_transac = pd.read_csv(csv_file, encoding='utf-8', sep=',', dtype=str,
                             names=columns, skiprows=1).fillna('')
    df_transac['mobile'] = df_transac['mobile'].str.lstrip('+')
    for col in ['amount', 'fee', 'balance']:
        df_transac[col] = pd.to_numeric(df_transac[col], errors='coerce')
    

    # --- Read Excel ---
    drivers = pd.read_excel(xlsx_file, sheet_name='liste')  # Change if needed
    drivers=drivers.fillna('')
    drivers['tel'] = drivers['tel'].to_string()
    drivers['tel'] = drivers['tel'].str.lstrip('+')

    # TODO: Insert your real processing logic here
    merchPayments = df_transac[df_transac['type']=='merchant_payment']
    driverPayments = merchPayments[merchPayments['mobile'].isin(drivers['tel'])]
    driverPayments['timestamp'] = pd.to_datetime(driverPayments['timestamp']).dt.date


    # For now, just show head of both
    st.subheader("🔍 Transactions Preview")
    st.dataframe(df_transac.head())

    st.subheader("👤 Drivers Preview")
    st.dataframe(drivers.head())

    st.subheader("👤 Driver Payments Preview")
    st.dataframe(driverPayments.head())

    # --- Export Excel result ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_transac.to_excel(writer, index=False, sheet_name='Transactions')
        drivers.to_excel(writer, index=False, sheet_name='Drivers')

    st.success("✅ Processing complete. Download your file below:")
    st.download_button(
        label="📥 Download Excel File",
        data=output.getvalue(),
        file_name="processed_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
