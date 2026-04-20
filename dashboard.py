import streamlit as st
import pandas as pd
import calendar
import plotly.graph_objects as go
from datetime import datetime, date
import re
import numpy as np

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    layout="wide", 
    page_title="Betting Analytics Pro", 
    page_icon="💎",
    initial_sidebar_state="expanded"
)

# --- ESTILIZAÇÃO CSS PREMIUM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #020617; }
    .main .block-container { max-width: 1200px; padding-top: 1rem; margin: auto; }

    /* Estilização da Navegação para parecer botões */
    div[data-testid="stSidebarNav"] { padding-top: 0rem; }
    
    /* Cartões de Métricas */
    .metric-card {
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        padding: 15px 10px; border-radius: 20px; color: white; font-weight: 800;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.05);
        height: 100px; width: 100%; margin-bottom: 10px;
    }
    .metric-title { font-size: 0.65rem; text-transform: uppercase; opacity: 0.6; letter-spacing: 1px; margin-bottom: 3px; }
    .metric-value { font-size: 1.5rem; margin: 0; letter-spacing: -1px; }

    /* Performance Cards */
    .perf-card { 
        background: #0f172a; border-radius: 12px; padding: 12px 15px; 
        display: flex; align-items: center; justify-content: space-between; 
        border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 8px;
    }
    .val-pos { color: #10b981; font-weight: 800; }
    .val-neg { color: #f43f5e; font-weight: 800; }

    /* Calendário */
    .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 5px; margin-top: 10px; }
    .day-name { text-align: center; color: #475569; font-weight: 800; font-size: 0.6rem; text-transform: uppercase; }
    .day-card { 
        background: #0f172a; border-radius: 8px; padding: 8px; min-height: 70px; 
        display: flex; flex-direction: column; justify-content: space-between;
        border: 1px solid rgba(255, 255, 255, 0.03); 
    }
    .green-card { background: linear-gradient(135deg, #059669 0%, #064e3b 100%); border: none; }
    .red-card { background: linear-gradient(135deg, #dc2626 0%, #7f1d1d 100%); border: none; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNÇÕES DE APOIO ---
def format_br(val):
    prefix = "-" if val < 0 else ""
    return f"{prefix}R$ {abs(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def clean_money(val):
    if val == '--' or pd.isna(val): return 0.0
    return float(str(val).replace(',', ''))

# --- CARREGAMENTO DE DADOS ---
arquivo_path = "Betfair.csv"

with st.sidebar:
    st.markdown("<h2 style='color: #10b981; margin-bottom: 0;'>💎 EXECUTIVE</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 0.8rem; opacity: 0.5;'>Pro Trader Analytics</p>", unsafe_allow_html=True)
    
    stake_padrao = st.number_input("Stake Padrão (R$)", value=600.0)
    st.markdown("---")
    
    # MUDANÇA AQUI: Selectbox ao invés de Radio para facilitar o clique no mobile e remover bolinhas
    menu = st.selectbox(
        "Navegar para:",
        ["Performance Geral", "Diário de Operações", "Evolução Patrimonial", "Análise de Janelas"]
    )

try:
    df_raw = pd.read_csv(arquivo_path)
    if 'Descrição' in df_raw.columns:
        df_raw = df_raw.rename(columns={'Descrição': 'Evento'})
        df_raw['Valor (R$)'] = df_raw['Entrada de Dinheiro (R$)'].apply(clean_money) + df_raw['Saída de Dinheiro (R$)'].apply(clean_money)
    
    df = df_raw[~df_raw['Evento'].str.contains('Depósito|Deposit|Withdraw|Saque|Transferência', case=False, na=False)].copy()
    meses_pt_map = {'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'mai': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'}
    for pt, en in meses_pt_map.items(): df['Data'] = df['Data'].str.replace(pt, en, case=False)
    
    df['Data'] = pd.to_datetime(df['Data'])
    df['Data_Apenas'] = df['Data'].dt.date
    df['Hora'] = df['Data'].dt.hour
    df['Dia_Semana_Num'] = df['Data'].dt.dayofweek
    df = df.sort_values('Data')

    # Filtros Dinâmicos
    if menu == "Diário de Operações":
        with st.sidebar:
            st.markdown("---")
            anos_disp = sorted(df['Data'].dt.year.unique(), reverse=True)
            ano_cal = st.selectbox("Ano", anos_disp)
            meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_nome_cal = st.selectbox("Mês", meses_nomes, index=datetime.now().month - 1)
            mes_num_cal = meses_nomes.index(mes_nome_cal) + 1
        df_final = df[(df['Data'].dt.year == ano_cal) & (df['Data'].dt.month == mes_num_cal)].copy()
    else:
        with st.sidebar:
            st.markdown("---")
            periodo_global = st.date_input("Filtrar Período", [df['Data_Apenas'].min(), df['Data_Apenas'].max()])
        if len(periodo_global) == 2:
            df_final = df[(df['Data_Apenas'] >= periodo_global[0]) & (df['Data_Apenas'] <= periodo_global[1])].copy()
        else:
            df_final = pd.DataFrame()

    if not df_final.empty:
        # Processamento
        df_final['ID_Ref'] = df_final['Evento'].apply(lambda x: re.search(r'Ref: (\d+)', str(x)).group(1) if re.search(r'Ref: (\d+)', str(x)) else "0")
        df_clean = df_final.groupby(['ID_Ref', 'Data', 'Evento', 'Hora', 'Dia_Semana_Num']).agg({'Valor (R$)': 'sum'}).reset_index()
        df_clean['Data_Apenas'] = df_clean['Data'].dt.date
        df_clean['Est'] = df_clean['Evento'].apply(lambda x: str(x).split('Ref:')[0].split('/')[-1].strip() if '/' in str(x) else "Match Odds")
        df_clean['Odd'] = df_clean['Valor (R$)'].apply(lambda x: (x / stake_padrao) + 1 if x > 0 else 0)
        avg_odds = df_clean[df_clean['Odd'] > 0].groupby('Est')['Odd'].mean().to_dict()
        df_clean.loc[df_clean['Odd'] == 0, 'Odd'] = df_clean['Est'].map(avg_odds).fillna(1.50)

        total_l = df_clean['Valor (R$)'].sum()
        odd_m = df_clean[df_clean['Valor (R$)'] > 0]['Odd'].mean()

        # VIEWS
        if menu == "Performance Geral":
            bg_lucro = "linear-gradient(135deg, #10b981 0%, #064e3b 100%)" if total_l >= 0 else "linear-gradient(135deg, #ef4444 0%, #7f1d1d 100%)"
            st.markdown(f'<div class="metric-card" style="background: {bg_lucro}; height: 120px;"><div class="metric-title">Lucro Líquido</div><div class="metric-value" style="font-size: 2rem;">{format_br(total_l)}</div></div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f'<div class="metric-card"><div class="metric-title">Odd Média</div><div class="metric-value">{odd_m:.2f}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><div class="metric-title">Stakes</div><div class="metric-value">{total_l/stake_padrao:,.2f}</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="metric-card"><div class="metric-title">Entradas</div><div class="metric-value">{len(df_clean)}</div></div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🎯 Estratégias")
                res = df_clean.groupby('Est').agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor (R$)': 'Lucro'}).sort_values('Lucro', ascending=False)
                for est, row in res.iterrows():
                    cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
                    st.markdown(f'<div class="perf-card"><div><b>{est}</b></div><div style="text-align:right"><span class="{cor}">{format_br(row['Lucro'])}</span><br><small>{(row["Lucro"]/(row["Qtd"]*stake_padrao))*100:.1f}% ROI</small></div></div>', unsafe_allow_html=True)
            with col2:
                st.subheader("📊 Ranges de Odd")
                bins = [0, 1.30, 1.59, 1.79, 2.09, 3.0, 1000]
                labels = ['1.00-1.30', '1.31-1.59', '1.60-1.79', '1.80-2.09', '2.10-3.00', '3.00+']
                df_clean['Range'] = pd.cut(df_clean['Odd'], bins=bins, labels=labels)
                res_odd = df_clean.groupby('Range', observed=False).agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor (R$)': 'Lucro'})
                for r, row in res_odd.iterrows():
                    cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
                    st.markdown(f'<div class="perf-card"><div><b>{r}</b></div><div style="text-align:right"><span class="{cor}">{format_br(row['Lucro'])}</span><br><small>{int(row["Qtd"])} entr.</small></div></div>', unsafe_allow_html=True)

        elif menu == "Diário de Operações":
            bg_m = "rgba(16, 185, 129, 0.2)" if total_l >= 0 else "rgba(244, 63, 94, 0.2)"
            st.markdown(f'<div class="monthly-profit-card" style="background: {bg_m}; border: 1px solid {"#10b981" if total_l >= 0 else "#f43f5e"};"><small>LUCRO {mes_nome_cal.upper()}</small><br><span style="font-size: 2rem;">{format_br(total_l)}</span></div>', unsafe_allow_html=True)
            cal_obj = calendar.Calendar(firstweekday=0)
            dias = list(cal_obj.itermonthdays(ano_cal, mes_num_cal))
            lucro_dia = df_clean.groupby(df_clean['Data'].dt.day)['Valor (R$)'].sum()
            html = '<div class="calendar-grid">'
            for n in ['S','T','Q','Q','S','S','D']: html += f'<div class="day-name">{n
