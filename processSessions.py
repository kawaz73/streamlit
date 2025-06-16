import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import openpyxl
#import math

st.set_page_config(page_title="Illigo - Analyse Rapport Wave", layout="centered")
st.title("🧮 Illigo - Analyse Sessions Console")
st.markdown("Télécharger le rapport de sessions de charge en CSV")

# Upload CSV and Excel files
csv_file = st.file_uploader("Entrer le rapport sessions en CSV", type=["csv"])
tva=0.18 # TVA 18%
frais_wave=0.01 # 1% de frais Wave
comm_operateur = 0.90 # 90% de reversement opérateur par défaut

if csv_file :
    # --- Read CSV ---
    columns =['Site','Opérateur','Connecteur','Organisation','Type util','Nom util','NomPrenom','badgeid','debut','fin','duree','energie','montant','devise','arret']
    df_sessions = pd.read_csv(csv_file, encoding='utf-8', sep = ';',dtype=str, names=columns, skiprows=1)

    # pretraitement des données
    df_sessions['debut']=pd.to_datetime(df_sessions['debut'])
    df_sessions['fin']=pd.to_datetime(df_sessions['fin'])
    df_sessions['duree']=pd.to_datetime(df_sessions['duree'], format = "%H:%M")
    df_sessions['energie']=pd.to_numeric(df_sessions['energie'],downcast='float')/1000
    df_sessions['montant']=pd.to_numeric(df_sessions['montant'],downcast='float').apply(np.ceil)

    # affichage des données lues du CSV et traitées
    st.subheader("🔍 Aperçu des sessions")
    st.dataframe(df_sessions.head())

    # saisie des paramètres de facturation
    st.sidebar.header("⚙️ Paramètres de facturation")
    liste_operateurs = df_sessions['Opérateur'].unique().tolist()
    liste_operateurs.sort()
    comm_operateurs_recettes = {}
    comm_operateurs_profits = {}
    with st.sidebar.form("param_form"):
        for operateur in liste_operateurs:
            st.write(f"Opérateur: {operateur}")
            comm_operateurs_recettes[operateur] = st.number_input(
                f"Commission recettes ({operateur}) (%)",
                min_value=0,
                max_value=100,
                value=int(comm_operateur*100) if operateur!='Illigo' else 1,  # Convert to integer percentage
                step=1,
                key=f"comm_{operateur}"
            )
            comm_operateurs_profits[operateur] = st.number_input(
                f"Commission profit ({operateur}) (%)",
                min_value=0,
                max_value=100,
                value=0,  # Default to 0%
                step=1,
                key=f"comm_{operateur}_profit"
            )  
        submitted = st.form_submit_button("Valider")
    
    if not submitted:
        st.stop()

    df_comms_operateurs = pd.DataFrame(columns=['Opérateur', 'Commission Recettes (%)', 'Commission Profits (%)'])
    
    # assignation des commissions opérateurs dans un dataframe
    for operateur in liste_operateurs:
        new_row = pd.DataFrame([{
            'Opérateur': operateur,
            'Commission Recettes (%)': comm_operateurs_recettes[operateur],
            'Commission Profits (%)': comm_operateurs_profits[operateur]
        }])
        df_comms_operateurs = pd.concat([df_comms_operateurs, new_row], ignore_index=True)
    
    st.subheader("🔍 Aperçu dataframe commissions opérateur")
    st.dataframe(df_comms_operateurs.head())
    
    invoicebyoperator = df_sessions.groupby(['Opérateur'], as_index=False).agg({
        'montant': 'sum'
    }).sort_values(by='montant', ascending=False).reset_index(drop=True)
    
    invoicebyoperator= invoicebyoperator.merge(
        df_comms_operateurs[['Opérateur', 'Commission Recettes (%)','Commission Profits (%)']],
        on='Opérateur',
        how='left'
    )

    invoicebyoperator.loc[:,'frais wave'] = (invoicebyoperator['montant'] * frais_wave).round(0).astype(int)
    invoicebyoperator.loc[:,'reversement opérateur'] = (invoicebyoperator['montant'] * invoicebyoperator['Commission Recettes (%)'] / 100).round(0).astype(int) - invoicebyoperator['frais wave']
    invoicebyoperator.loc[:,'commission illigo TTC'] = invoicebyoperator['montant'] - invoicebyoperator['reversement opérateur']
    invoicebyoperator.loc[:,'commission illigo HT'] = (invoicebyoperator['commission illigo TTC'] / (1 + tva)).round(0).astype(int)
    invoicebyoperator.loc[:,'tva'] = invoicebyoperator['commission illigo TTC'] - invoicebyoperator['commission illigo HT']
    
    # cols = ['montant', 'frais wave', 
    #        'reversement opérateur', 'commission illigo TTC', 'commission illigo HT', 'tva']
    
    # for col in cols:
    #     invoicebyoperator[col] = invoicebyoperator[col].round(0).astype(int)

    st.subheader("🔍 Résumé facturation par opérateur")
    st.dataframe(invoicebyoperator.head())

    # --- Export Excel result ---
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        invoicebyoperator.to_excel(writer, index=False, sheet_name='Synthèse')
        df_sessions.to_excel(writer, index=False, sheet_name='Sessions')
    output.seek(0)
    st.success("✅ Traitement terminé. Télechargez l'Excel:")
    st.download_button(
        label="📥 Télécharger le fichier Excel",
        data=output.getvalue(),
        file_name="rapport_bornes.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
