import streamlit as st
import pandas as pd
import numpy as np
import io
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import openpyxl
import base64
#import math

@st.cache_data
def load_sessions(file):
    """Load sessions from a CSV file."""
    print("Loading sessions from file:", file.name)
    columns = ['Site', 'Borne', 'Opérateur', 'Connecteur', 'Organisation', 'Type util', 'Nom util', 'NomPrenom', 'badgeid', 'debut', 'fin', 'duree', 'energie', 'montant', 'devise', 'arret']
    df = pd.read_csv(file, encoding='utf-8', sep=';', dtype=str, names=columns, skiprows=1)
    # pretraitement des données
    df['debut']=pd.to_datetime(df['debut'])
    df['fin']=pd.to_datetime(df['fin'])
    df['duree']=pd.to_datetime(df['duree'], format = "%H:%M")
    df['energie']=pd.to_numeric(df['energie'],downcast='float')/1000
    df['montant']=pd.to_numeric(df['montant'],downcast='float').apply(np.ceil)

    # affichage des données lues du CSV et traitées
    st.subheader("🔍 Aperçu des sessions")
    st.dataframe(df.head())
    return df

@st.cache_data
def calculateInvoice(df_sessions, tva, frais_wave, df_comms_operateurs):
    """Calculate the invoice based on the sessions data."""
    print("Calculating invoice...")
    invoicebyoperator = df_sessions.groupby(['Opérateur','Site'], as_index=False).agg({
        'montant': 'sum', 'energie': 'sum','badgeid': 'size'
    }).sort_values(by=['Opérateur', 'Site'], ascending=[True,True]).reset_index(drop=True)

    invoicebyoperator.rename(columns={'badgeid': 'nb sessions', 'energie': 'energie (kWh)'}, inplace=True)
    
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
    # displayInvoice(invoicebyoperator)
    # plotInvoice(invoicebyoperator)

    return invoicebyoperator

@st.fragment
def displayInvoice(invoicebyoperator):
    """Display the invoice data."""
    print("Displaying invoice data...")
    st.subheader("🔍 Résumé facturation par opérateur")
    st.dataframe(invoicebyoperator)
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

@st.fragment
def plotInvoice(invoicebyoperator):
    """Plot the invoice data."""
    print("Plotting invoice data...")
    fig, ax = plt.subplots(figsize=(10, 6))
    invoicebyoperator.plot(kind='bar', x='Site', y='commission illigo HT', ax=ax, color='skyblue', legend=False)
    ax.set_title('Commission Illigo HT par Site et Opérateur')
    ax.set_ylabel('Commission Illigo HT (CFA)')
    ax.set_xlabel('Site')
    ax.grid(axis='y', linestyle='--', alpha=0.7)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{int(x):,}'))  # Use ',' for thousands separator
    plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    st.pyplot(fig)
    img_bytes = io.BytesIO()
    fig.savefig(img_bytes, format='png', bbox_inches='tight')
    img_bytes.seek(0)
    b64 = base64.b64encode(img_bytes.read()).decode()
    href = f'<a href="data:image/png;base64,{b64}" download="commission_illigo_ht_par_operateur.png">📥 Télécharger le graphique (PNG)</a>'
    st.markdown(href, unsafe_allow_html=True)

st.set_page_config(page_title="Illigo - Analyse Sessions Console", layout="centered")
# To replace the icon in the title, simply change the emoji at the start of the string.
# For an EV charger, use the charging station emoji:
st.title("🔌 Illigo - Analyse Sessions Console")
st.markdown("Télécharger le rapport de sessions de charge en CSV")


# Upload CSV and Excel files
csv_file = st.file_uploader("Entrer le rapport sessions en CSV", type=["csv"])
tva=0.18 # TVA 18%
frais_wave=0.01 # 1% de frais Wave
comm_operateur = 0.90 # 90% de reversement opérateur par défaut

if csv_file :
    # --- Read CSV ---
    # columns =['Site','Borne','Opérateur','Connecteur','Organisation','Type util','Nom util','NomPrenom','badgeid','debut','fin','duree','energie','montant','devise','arret']
    # df_sessions = pd.read_csv(csv_file, encoding='utf-8', sep = ';',dtype=str, names=columns, skiprows=1)
    df_sessions = load_sessions(csv_file)

    # saisie des paramètres de facturation
    st.sidebar.header("⚙️ Paramètres de facturation")
    liste_operateurs = df_sessions['Opérateur'].unique().tolist()
    liste_operateurs.sort()
    comm_operateurs_recettes = {}
    comm_operateurs_profits = {}

    # Use session state to track form submissions
    if 'date_form_submitted' not in st.session_state:
        st.session_state['date_form_submitted'] = False
    if 'param_form_submitted' not in st.session_state:
        st.session_state['param_form_submitted'] = False

    # First form: select date range
    with st.sidebar.form("param_date"):
        st.write("Sélectionnez la période de facturation")
        date_debut = st.date_input("Date de début", value=df_sessions['debut'].min().date())
        date_fin = st.date_input("Date de fin", value=df_sessions['debut'].max().date())
        submitted_date = st.form_submit_button("Valider")
    if submitted_date:
        st.session_state['date_form_submitted'] = True

    if not st.session_state['date_form_submitted']:
        st.stop()

    # Second form: operator commissions
    with st.sidebar.form("param_form"):
        for operateur in liste_operateurs:
            st.write(f"Opérateur: {operateur}")
            comm_operateurs_recettes[operateur] = st.number_input(
                f"Commission recettes ({operateur}) (%)",
                min_value=0,
                max_value=100,
                value=int(comm_operateur*100) if operateur!='Illigo' else 1,
                step=1,
                key=f"comm_{operateur}"
            )
            comm_operateurs_profits[operateur] = st.number_input(
                f"Commission profit ({operateur}) (%)",
                min_value=0,
                max_value=100,
                value=0,
                step=1,
                key=f"comm_{operateur}_profit"
            )
        submitted_param = st.form_submit_button("Valider")
    if submitted_param:
        st.session_state['param_form_submitted'] = True

    if not st.session_state['param_form_submitted']:
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
    
    # --- Filter sessions by date range ---
    df_sessions = df_sessions[(df_sessions['debut'].dt.date >= date_debut) & (df_sessions['fin'].dt.date <= date_fin)]

    invoicebyoperator = calculateInvoice(df_sessions, tva, frais_wave, df_comms_operateurs)
    displayInvoice(invoicebyoperator)
    plotInvoice(invoicebyoperator)
    