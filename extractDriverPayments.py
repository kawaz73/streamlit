import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import openpyxl

st.set_page_config(page_title="Illigo - Driver Payment Processor", layout="centered")
st.title("🚗 Extraction paiements chauffeurs illigo")
st.markdown("Entrer les transactions Wave et la liste des chauffeurs pour générer un Excel avec les paiements chauffeurs.")

# Upload CSV and Excel files
csv_file = st.file_uploader("Entrer le rapport Wave en CSV", type=["csv"])
xlsx_file = st.file_uploader("Entrer le fichier Excel avec la liste des chauffeurs", type=["xlsx"])

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
    #drivers = pd.read_excel(xlsx_file, sheet_name='liste')  # Change if needed
    drivers = pd.read_excel(xlsx_file, sheet_name='liste', dtype={'nom' : str, 'prénom' : str, 'tel' : str, 'statut' : str,'début' : str, 'fin' : str}
                            ,parse_dates=['début', 'fin'])
    drivers=drivers.fillna('')
    #drivers['tel'] = drivers['tel'].to_string()
    #drivers['tel'] = drivers['tel'].str.lstrip('+')

    # TODO: Insert your real processing logic here
    merchPayments = df_transac[df_transac['type']=='merchant_payment']
    driverPayments = merchPayments[merchPayments['mobile'].isin(drivers['tel'])]
    driverPayments['timestamp'] = pd.to_datetime(driverPayments['timestamp']).dt.date
    driverPayments['recette'] = driverPayments['amount'] + driverPayments['fee']
    driverPayments = driverPayments.iloc[:,[0,7,13,3,4,8,1]]

    
    # Calculer les totaux par chauffeur
    driverTotals = driverPayments.groupby(['name','mobile'], as_index=False).agg({
        'recette': 'sum',
        'amount': 'sum',
        'fee': 'sum'
    })

    driverTotals['recette TTC'] = driverTotals['recette']
    driverTotals['recette HT'] = (driverTotals['recette TTC'] / 1.18).round(0).astype(int)
    driverTotals['tva'] = driverTotals['recette TTC'] - driverTotals['recette HT']

    st.subheader("🔍 Aperçu des transactions")
    st.dataframe(df_transac.head())

    st.subheader("👤 Aperçu des chauffeurs")
    st.dataframe(drivers.head())

    st.subheader("👤 Aperçu des paiements chauffeurs")
    st.dataframe(driverPayments.head())

    st.subheader("👤 Aperçu des totaux chauffeurs")
    st.dataframe(driverTotals.head(20))

    # --- Export Excel result ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        driverTotals.to_excel(writer, index=False, sheet_name='Totaux chauffeurs')
        driverPayments.to_excel(writer, index=False, sheet_name='Transactions chauffeurs')

    st.success("✅ Traitement terminé. Télechargez l'Excel:")
    st.download_button(
        label="📥 Télécharger le fichier Excel",
        data=output.getvalue(),
        file_name="driverpayments.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
