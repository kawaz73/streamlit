import pandas as pd
import numpy as np
from datetime import datetime
import sys
import matplotlib.pyplot as plt
import streamlit as st

def filterbyweek(df_sessions, start, end):
    # Filter sessions for week between start and end date
    if not end in df_sessions['week'].values:
        end = df_sessions['week'].max()
        print("End week not found in sessions data, using max week:", end)
    if not start in df_sessions['week'].values:
        start = df_sessions['week'].min()
        print("Start week not found in sessions data, using min week:", start)
    mask = (df_sessions['week'] >= start) & (df_sessions['week'] <= end)
    return df_sessions[mask]

def filterbymonth(df_sessions, start, end):
    # Filter sessions for month between start and end date
    if not end in df_sessions['mm'].values:
        end = df_sessions['mm'].max()
        print("End month not found in sessions data, using max month:", end)
    if not start in df_sessions['mm'].values:
        start = df_sessions['mm'].min()
        print("Start month not found in sessions data, using min month:", start)
    mask = (df_sessions['mm'] >= start) & (df_sessions['mm'] <= end)
    return df_sessions[mask]

def filterbyday(df_sessions, start, end):
    # Filter sessions between start and end date
    if not pd.to_datetime(end).date() in df_sessions['date'].values:
        end = df_sessions['date'].max()
        print("End date not found in sessions data, using max date:", end)
    
    if not pd.to_datetime(start).date() in df_sessions['date'].values:
        start = df_sessions['date'].min()
        print("Start date not found in sessions data, using min date:", start)
    
    mask = (df_sessions['date'] >= pd.to_datetime(start).date()) & (df_sessions['date'] <= pd.to_datetime(end).date())
    return df_sessions[mask]

def loadSessions(filename):

    columns =['Site','Opérateur','Connecteur','Type util','Nom util','NomPrenom','badgeid','debut','fin','duree','energie','montant','devise','arret']
    df_sessions = pd.read_csv(filename, encoding='utf-8', sep = ';',dtype=str, names=columns, skiprows=1)
    df_sessions['debut']=pd.to_datetime(df_sessions['debut'])
    df_sessions['fin']=pd.to_datetime(df_sessions['fin'])
    df_sessions['duree']=pd.to_datetime(df_sessions['duree'], format = "%H:%M")
    df_sessions['energie']=pd.to_numeric(df_sessions['energie'],downcast='float')/1000  # Convert to kWh
    df_sessions['montant']=pd.to_numeric(df_sessions['montant'],downcast='float')
    df_sessions['date'] = df_sessions['debut'].dt.date
    df_sessions['hour'] = df_sessions['debut'].dt.hour
    df_sessions['mm-dd'] = df_sessions['debut'].dt.strftime('%m-%d')
    df_sessions['mm-dd-hh'] = df_sessions['debut'].dt.strftime('%m-%d-%h')
    df_sessions['mm'] = df_sessions['debut'].dt.month
    df_sessions['week'] = df_sessions['debut'].dt.isocalendar().week
    # print(df_sessions.dtypes)
    # print("Charge sessions data loaded from console:")
    # print(df_sessions.head)
    return df_sessions

def plotSessionsbyDay(df_sessions,start,end):
    # Count the number of sessions by day
    print("Plotting sessions by day from ", start, " to ", end)
    sessions_by_day = filterbyday(df_sessions, start, end).groupby('date').size().reset_index(name='sessions_count')
    fig, ax = plt.subplots(figsize=(12, 6))
    sites = df_sessions['Site'].unique()
    bar_width = 0.8 / len(sites)
    x = np.arange(len(sessions_by_day['date'].unique()))
    dates = sorted(sessions_by_day['date'].unique())

    for i, site in enumerate(sites):
        site_sessions = df_sessions[df_sessions['Site'] == site].groupby('date').size().reindex(dates, fill_value=0)
        ax.bar(x + i * bar_width, site_sessions.values, width=bar_width, label=site)

    ax.set_xlabel('Date')
    ax.set_ylabel('Nombre de sessions')
    ax.set_title('Nombre de sessions par jour et par site')
    ax.set_xticks(x + bar_width * (len(sites) - 1) / 2)
    ax.set_xticklabels(dates, rotation=90)
    ax.legend(title='Site')
    fig.tight_layout()
    st.pyplot(fig)
    return sessions_by_day

def plotSessionsbyWeek(df_sessions,start,end):

    # statistiques par semaine
    # filter sessions for week between start and end date
    # if not end in df_sessions['week'].values:
    #     end = df_sessions['week'].max()
    #     print("End week not found in sessions data, using max week:", end)
    # if not start in df_sessions['week'].values:
    #     start = df_sessions['week'].min()
    #     print("Start week not found in sessions data, using min week:", start)
    # mask = (df_sessions['week'] >= start) & (df_sessions['week'] <= end)
    # df_sessions = df_sessions[mask]

    # sessionsbyweek = df_sessions.groupby(['Site', 'week'])['Type util'].count().reset_index().sort_values(by=['week', 'Site'])
    sessionsbyweek = filterbyweek(df_sessions,start,end).groupby(['Site', 'week'])['Type util'].count().reset_index().sort_values(by=['week', 'Site'])
    sessionsbyweek['sessionscount'] = sessionsbyweek['Type util']
    weeks = sorted(sessionsbyweek['week'].unique())

    # sessions by week for all sites combined

    sessionsbyweek_all = sessionsbyweek.groupby('week')['sessionscount'].sum().reset_index()
    # print(sessionsbyweek_all)   
    plt.figure(figsize=(10, 6))
    bar_width = 0.8
    x = np.arange(len(weeks))

    plt.bar(x , sessionsbyweek_all['sessionscount'], width=bar_width, label="Sessions par semaine", color='blue')
    plt.xlabel('Semaine')
    plt.ylabel('nombre de sessions')
    plt.title('Nb de sessions par semaine')
    plt.xticks(x , weeks, rotation=90)
    plt.legend(title='Site')
    plt.tight_layout()
    plt.show()

def plotEnergybyMonth(df_sessions,start,end):
        # Plotting energy by month for each site

    # Filter sessions for month between start and end date
    # if not end in df_sessions['mm'].values:
    #     end = df_sessions['mm'].max()
    #     print("End month not found in sessions data, using max month:", end)
    # if not start in df_sessions['mm'].values:
    #     start = df_sessions['mm'].min()
    #     print("Start month not found in sessions data, using min month:", start)
    # mask = (df_sessions['mm'] >= start) & (df_sessions['mm'] <= end)
    # df_sessions = df_sessions[mask]
    # energy_by_month = df_sessions.groupby(['Site', 'mm'])['energie'].sum().reset_index().sort_values(by=['Site','mm'])

    energy_by_month = filterbymonth(df_sessions,start,end).groupby(['Site', 'mm'])['energie'].sum().reset_index().sort_values(by=['Site','mm'])
    months = sorted(energy_by_month['mm'].unique())
    # print(energy_by_month)
    sites = energy_by_month['Site'].unique()
    bar_width = 0.8 / len(sites)
    x = np.arange(len(months))
    plt.figure(figsize=(10, 6))
    for i, site in enumerate(sites):
        site_data = energy_by_month[energy_by_month['Site'] == site]
        energies = [site_data[site_data['mm'] == m]['energie'].sum() if m in site_data['mm'].values else 0 for m in months]
        plt.bar(x + i * bar_width, energies, width=bar_width, label=site)

    plt.xlabel('Mois')
    plt.ylabel('Energie (kWh)')
    plt.title('Energie par Mois et Site')
    plt.xticks(x + bar_width * (len(sites) - 1) / 2, months, rotation=90)
    plt.legend(title='Site')
    plt.tight_layout()
    plt.show()

def plotEnergybyDay(df_sessions,start,end):
    # Filter sessions between start and end date
    # check if start date and end date are present in the sessions data
    # if they are not,
    # if not pd.to_datetime(end).date() in df_sessions['date'].values:
    #     end = df_sessions['date'].max()
    #     print("End date not found in sessions data, using max date:", end)
    
    # if not pd.to_datetime(start).date() in df_sessions['date'].values:
    #     start = df_sessions['date'].min()
    #     print("Start date not found in sessions data, using min date:", start)
    
    # mask = (df_sessions['date'] >= pd.to_datetime(start).date()) & (df_sessions['date'] <= pd.to_datetime(end).date())
    # df_sessions = df_sessions[mask]
    # print(df_sessions['date'].min(), df_sessions['date'].max())
    energy_by_day_site = filterbyday(df_sessions, start, end).groupby(['Site', 'date'])['energie'].sum().reset_index().sort_values(by=['Site','date'])
    print(energy_by_day_site)
    print(df_sessions['energie'].mean())
    
    plt.figure(figsize=(10, 6))
    for site in energy_by_day_site['Site'].unique():
        site_data = energy_by_day_site[energy_by_day_site['Site'] == site]
        plt.plot(site_data['date'], site_data['energie'], marker='o', label=site)

    plt.xlabel('Date')
    plt.ylabel('Energie (kWh)')
    plt.title('Energy par jour et site')
    plt.legend(title='Site')
    plt.xticks(rotation=90)
    plt.gca().xaxis.set_major_locator(plt.MultipleLocator(1))
    plt.tight_layout()
    plt.show()

def plotEnergybyHour(df_sessions,start,end):
    # Plotting energy by hour for each site between start and end date
    
    energy_by_hour_site = filterbyday(df_sessions,start,end).groupby(['Site', 'hour'])['energie'].sum().reset_index().sort_values(by=['Site','hour'])

    plt.figure(figsize=(10, 6))
    for site in energy_by_hour_site['Site'].unique():
        site_data = energy_by_hour_site[energy_by_hour_site['Site'] == site]
        plt.plot(site_data['hour'], site_data['energie'], marker='o', label=site)

    plt.xlabel('Heure du jour')
    plt.ylabel('Energie (kWh)')
    plt.title('Energie par heure et site')
    plt.legend(title='Site')
    plt.xticks(rotation=90)
    plt.gca().xaxis.set_major_locator(plt.MultipleLocator(1))
    plt.tight_layout()
    plt.show()

def plotSessionsbyWeekbySite(df_sessions,start,end):
    # Plotting  sessions by week and by site
    # statistiques par semaine
    # filter sessions for week between start and end date
    
    sessionsbyweek = filterbyweek(df_sessions,start,end).groupby(['Site', 'week'])['Type util'].count().reset_index().sort_values(by=['week', 'Site'])
    sessionsbyweek['sessionscount'] = sessionsbyweek['Type util']
    weeks = sorted(sessionsbyweek['week'].unique())
    sites = df_sessions['Site'].unique()

    plt.figure(figsize=(10, 6))
    bar_width = 0.8 / len(sites)
    x = np.arange(len(weeks))

    for i, site in enumerate(sites):
        site_data = sessionsbyweek[sessionsbyweek['Site'] == site]
        sessionscount = [site_data[site_data['week'] == w]['sessionscount'].values[0] if w in site_data['week'].values else 0 for w in weeks]
        #print(sessionscount)
        plt.bar(x + i * bar_width, sessionscount, width=bar_width, label=site)

    plt.xlabel('Semaine')
    plt.ylabel('nombre de sessions')
    plt.title('Nb de sessions par semaine et site')
    plt.xticks(x + bar_width * (len(sites) - 1) / 2, weeks, rotation=90)
    plt.legend(title='Site')
    plt.tight_layout()
    plt.show()


# plotSessionsbyDay(df_sessions, '2025-05-02', '2025-05-11')
#plotSessionsbyWeek(df_sessions,1, 26)
# plotEnergybyMonth(df_sessions,1,6)
# plotEnergybyDay(df_sessions, '2025-05-02', '2025-05-11')
# plotEnergybyHour(df_sessions,'2025-05-02', '2025-05-11')
# plotSessionsbyWeekbySite(df_sessions,15, 17)






