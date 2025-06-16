import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import openpyxl

st.set_page_config(page_title="Illigo - Analyse Rapport Wave", layout="centered")
st.title("🧮 Illigo - Analyse Rapport Wave")
st.markdown("Télécharger le rapport Wave en CSV")

# Upload CSV and Excel files
csv_file = st.file_uploader("Entrer le rapport Wave en CSV", type=["csv"])

if csv_file :
    # --- Read CSV ---
    columns = ['timestamp','id','type','amount','fee','balance','currency','name',
               'mobile','busName','busMobile','clientReference','apiSessId']
    # df_transac = pd.read_csv(csv_file, encoding='utf-8', sep=',', dtype=str,
    #                          names=columns, skiprows=1, index_col=None).fillna('')
    
    df_transac = pd.read_csv(csv_file, encoding='utf-8', sep=',', dtype=str,
                              skiprows=1, index_col=None).fillna('')
    num_columns = df_transac.shape[1]
    if num_columns == 13:
        columns = ['timestamp','id','type','amount','fee','balance','currency','name',
               'mobile','busName','busMobile','clientReference','apiSessId']
        df_transac.columns = columns
    elif num_columns == 14:
        columns = ['timestamp','id','type','amount','fee','balance','currency','name',
               'mobile','busName','busMobile','counterpartyId','clientReference','apiSessId']
        df_transac.columns = columns
 
    st.subheader("🔍 Aperçu des transactions")
    st.dataframe(df_transac.head())

    # df_transac = pd.read_csv(csv_file, encoding='utf-8', sep=',', 
    #                          names=columns, skiprows=1, index_col=None).fillna('')
    df_transac['mobile'] = df_transac['mobile'].str.lstrip('+')
    for col in ['amount', 'fee', 'balance']:
        df_transac[col] = pd.to_numeric(df_transac[col], errors='coerce')
    
    # df_transac['timestamp'] = pd.to_datetime(df_transac['timestamp']).dt.date
    df_transac['timestamp'] = pd.to_datetime(df_transac['timestamp'],format='%Y-%m-%d %H:%M:%S%z', errors='coerce').dt.date
    
    # TODO: Insert your real processing logic here
    cashWithdrawals = df_transac[df_transac['type'].isin(['merchant_sweep'])]

    merchPayments = df_transac[df_transac['type'].isin(['merchant_payment', 'merchant_payment_refund'])]
    merchPaymentsbyUser = merchPayments.groupby(['mobile','name'], as_index=False).agg({
        'amount': 'sum',
        'fee': 'sum'
    }).sort_values(by='amount', ascending=False).reset_index(drop=True)
    merchPaymentsbyUser.loc[:,'amount TTC'] = merchPaymentsbyUser['amount'] - merchPaymentsbyUser['fee']
    merchPaymentsbyUser.loc[:,'amount HT'] = (merchPaymentsbyUser['amount TTC'] / 1.18).round(0).astype(int)
    merchPaymentsbyUser.loc[:,'tva'] = merchPaymentsbyUser['amount TTC'] - merchPaymentsbyUser['amount HT']

    walletPayments = df_transac[df_transac['type'].isin(['api_checkout', 'api_checkout_refund'])]
    walletPaymentsbyUser = walletPayments.groupby(['mobile','name'], as_index=False).agg({
        'amount': 'sum',
        'fee': 'sum'
    }).sort_values(by='amount', ascending=False).reset_index(drop=True)
    walletPaymentsbyUser.loc[:,'amount TTC'] = walletPaymentsbyUser['amount'] - walletPaymentsbyUser['fee']
    walletPaymentsbyUser.loc[:,'amount HT'] = (walletPaymentsbyUser['amount TTC']/ 1.18).round(0).astype(int)
    walletPaymentsbyUser.loc[:,'tva'] = walletPaymentsbyUser['amount TTC'] - walletPaymentsbyUser['amount HT']

    supplierPayments = df_transac[df_transac['type']=='single_payment']
    supplierPaymentsbyUser = supplierPayments.groupby(['mobile','name'], as_index=False).agg({
        'amount': 'sum',
        'fee': 'sum'
    }).sort_values(by='amount', ascending=False).reset_index(drop=True)
    supplierPaymentsbyUser['net supplier TTC'] = supplierPaymentsbyUser['amount'] + supplierPaymentsbyUser['fee']
    
    
    columns=['Poste','Montant TTC','Montant HT','TVA','Frais']
    synthese = pd.DataFrame(columns=columns)
    synthese.loc[0] = ['Retraits Espèces', cashWithdrawals['amount'].sum(), 0, 0, cashWithdrawals['fee'].sum()]
    synthese.loc[1] = ['Encaissements Marchands', merchPaymentsbyUser['amount TTC'].sum(), 
                       merchPaymentsbyUser['amount HT'].sum(), merchPaymentsbyUser['tva'].sum(), 
                       merchPaymentsbyUser['fee'].sum()]
    synthese.loc[2] = ['Encaissements Wallet', walletPaymentsbyUser['amount TTC'].sum(),
                       walletPaymentsbyUser['amount HT'].sum(), walletPaymentsbyUser['tva'].sum(), 
                       walletPaymentsbyUser['fee'].sum()]
    synthese.loc[3] = ['Paiements Fournisseurs', supplierPaymentsbyUser['net supplier TTC'].sum(),0,0,
                       supplierPaymentsbyUser['fee'].sum()]


    st.subheader("Synthèse")
    st.dataframe(synthese.head())

    # --- Export Excel result ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        synthese.to_excel(writer, index=False, sheet_name='Synthèse')
        cashWithdrawals.to_excel(writer, index=False, sheet_name='Retraits-Espèces')
        merchPaymentsbyUser.to_excel(writer, index=False, sheet_name='Pmt-Marchand-Util')
        walletPaymentsbyUser.to_excel(writer, index=False, sheet_name='Pmt-Wallet-Util')
        supplierPaymentsbyUser.to_excel(writer, index=False, sheet_name='Pmt-Four-Util')        
        merchPayments.to_excel(writer, index=False, sheet_name='Pmt-Marchand')
        walletPayments.to_excel(writer, index=False, sheet_name='Pmt-Wallet')
        supplierPayments.to_excel(writer, index=False, sheet_name='Pmt-Four')
        df_transac.to_excel(writer, index=False, sheet_name='Transactions')
    output.seek(0)
    st.markdown("### 📊 Résultats de l'analyse")

    st.success("✅ Traitement terminé. Télechargez l'Excel:")
    st.download_button(
        label="📥 Télécharger le fichier Excel",
        data=output.getvalue(),
        file_name="analyseWave.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
