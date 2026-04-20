import streamlit as st
import pandas as pd
import calendar
import plotly.graph_objects as go
from datetime import datetime # CORREÇÃO DO ERRO DO CALENDÁRIO
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Betting Analytics Pro", page_icon="💎")

# --- ESTILIZAÇÃO CSS PREMIUM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0f172a; }

    /* Cartões de Métricas Topo */
    .metric-card {
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        padding: 20px 10px; border-radius: 20px; color: white; font-weight: 800;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.1);
        height: 110px; width: 100%; margin-bottom: 10px;
    }
    .metric-title { font-size: 0.75rem; text-transform: uppercase; opacity: 0.7; margin-bottom: 5px; }
    .metric-value { font-size: 1.5rem; margin: 0; }

    /* Grid do Calendário */
    .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-top: 20px; }
    .day-name { text-align: center; color: #64748b; font-weight: 800; font-size: 0.7rem; text-transform: uppercase; }
    .day-card { 
        background: #1e293b; border-radius: 10px; padding: 10px; min-height: 75px; 
        display: flex; flex-direction: column; justify-content: space-between;
        border: 1px solid rgba(255, 255, 255, 0.03); 
    }
    .green-card { background: linear-gradient(135deg, #059669 0%, #064e3b 100%); border: none; }
    .red-card { background: linear-gradient(135deg, #dc2626 0%, #7f1d1d 100%); border: none; }

    /* Performance Cards (O visual que você gostou) */
    .perf-card { 
        background: #1e293b; border-radius: 12px; padding: 15px 20px; 
        display: flex; align-items: center; justify-content: space-between; 
        border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 8px;
    }
    .val-pos { color: #10b981; font-weight: 800; }
    .val-neg { color: #ef4444; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# TÍTULO
st.markdown("<h1 style='text-align: center; color: white; font-size: 2rem; font-weight: 800;'> <span style='color: #10b981;'>BETTING</span> ANALYTICS <span style='font-weight: 100; opacity: 0.3;'>|</span> EXECUTIVE</h1>", unsafe_allow_html=True)

# --- CONFIGURAÇÃO DE DADOS ---
arquivo_path = "Betfair.csv"
stake_padrao = st.sidebar.number_input("Stake Padrão (R$)", value=600.0)

def clean_money(val):
    if val == '--' or pd.isna(val): return 0.0
    return float(str(val).replace(',', ''))

try:
    df_raw = pd.read_csv(arquivo_path)
    if 'Descrição' in df_raw.columns:
        df_raw = df_raw.rename(columns={'Descrição': 'Evento'})
        df_raw['Valor (R$)'] = df_raw['Entrada de Dinheiro (R$)'].apply(clean_money) + df_raw['Saída de Dinheiro (R$)'].apply(clean_money)
    
    df = df_raw[~df_raw['Evento'].str.contains('Depósito|Deposit|Withdraw|Saque|Transferência', case=False, na=False)].copy()
    meses_pt = {'jan': 'Jan', 'fev': 'Feb', 'mar': 'Mar', 'abr': 'Apr', 'mai': 'May', 'jun': 'Jun', 'jul': 'Jul', 'ago': 'Aug', 'set': 'Sep', 'out': 'Oct', 'nov': 'Nov', 'dez': 'Dec'}
    for pt, en in meses_pt.items(): df['Data'] = df['Data'].str.replace(pt, en, case=False)
    df['Data'] = pd.to_datetime(df['Data'])
    df['Data_Apenas'] = df['Data'].dt.date
    df = df.sort_values('Data')

    def extract_id(row):
        match = re.search(r'Ref: (\d+)', str(row['Evento']))
        return match.group(1) if match else row.name
    df['ID_Ref'] = df.apply(extract_id, axis=1)
    df_clean = df.groupby(['ID_Ref', 'Data_Apenas', 'Evento']).agg({'Valor (R$)': 'sum'}).reset_index()

    # Cálculos
    df_clean['Lucro_Acumulado'] = df_clean['Valor (R$)'].cumsum()
    df_clean['Odd'] = df_clean['Valor (R$)'].apply(lambda x: (x / stake_padrao) + 1 if x > 0 else 0)

    # --- 3. MÉTRICAS TOPO ---
    total_l = df_clean['Valor (R$)'].sum()
    odd_m = df_clean[df_clean['Odd'] > 0]['Odd'].mean()
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(f'<div class="metric-card" style="background: linear-gradient(135deg, #10b981 0%, #064e3b 100%);"><div class="metric-title">Lucro Líquido</div><div class="metric-value">R$ {total_l:,.2f}</div></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card" style="background: #1e293b;"><div class="metric-title">Odd Média</div><div class="metric-value">{odd_m:.2f}</div></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card" style="background: #1e293b;"><div class="metric-title">Saldo Stakes</div><div class="metric-value">{total_l/stake_padrao:,.2f}</div></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card" style="background: #1e293b;"><div class="metric-title">Entradas</div><div class="metric-value">{len(df_clean)}</div></div>', unsafe_allow_html=True)

    # --- 4. GRÁFICO ACUMULADO COM CORES DINÂMICAS ---
    st.markdown("<p style='color:#94a3b8; font-weight:800; margin-top:20px;'>📈 EVOLUÇÃO PATRIMONIAL</p>", unsafe_allow_html=True)
    
    # Lógica para mudar cor da linha (Verde se > 0, Vermelho se < 0)
    cor_linha = '#10b981' if total_l >= 0 else '#ef4444'
    
    fig_evol = go.Figure()
    fig_evol.add_trace(go.Scatter(
        x=df_clean['Data_Apenas'], y=df_clean['Lucro_Acumulado'],
        mode='lines', line=dict(color=cor_linha, width=4, shape='spline'),
        fill='tozeroy', fillcolor=f'rgba({16 if total_l >=0 else 239}, {185 if total_l >=0 else 68}, {129 if total_l >=0 else 68}, 0.1)'
    ))
    fig_evol.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=10, b=0), height=300,
        xaxis=dict(showgrid=False, color='#64748b'),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#64748b')
    )
    st.plotly_chart(fig_evol, use_container_width=True, config={'displayModeBar': False})

    # --- 5. PERFORMANCE POR ESTRATÉGIA E POR ODD (O VISUAL QUE VOCÊ PEDIU) ---
    col_est, col_odd = st.columns(2)

    with col_est:
        st.subheader("🎯 Performance por Estratégia")
        def ext_est(txt): return str(txt).split('Ref:')[0].split('/')[-1].strip() if '/' in str(txt) else "Match Odds"
        df_clean['Est'] = df_clean['Evento'].apply(ext_est)
        res_est = df_clean.groupby('Est').agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor (R$)': 'Lucro'}).sort_values('Lucro', ascending=False)
        
        for est, row in res_est.iterrows():
            roi = (row['Lucro'] / (row['Qtd'] * stake_padrao)) * 100
            cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
            st.markdown(f'''<div class="perf-card">
                <div style="flex:2"><b style="color:white">{est}</b><br><small style="color:#94a3b8">{int(row['Qtd'])} entr. | {row['Lucro']/stake_padrao:,.2f} stk</small></div>
                <div style="flex:1; text-align:right;"><span class="{cor}">R$ {row['Lucro']:,.2f}</span><br><small style="color:#64748b">{roi:.1f}% ROI</small></div>
            </div>''', unsafe_allow_html=True)

    with col_odd:
        st.subheader("📊 Performance por Range de Odd")
        bins = [0, 1.30, 1.60, 2.0, 3.0, 100]; labels = ['1.0-1.3', '1.3-1.6', '1.6-2.0', '2.0-3.0', '3.0+']
        df_clean['Range'] = pd.cut(df_clean['Odd'], bins=bins, labels=labels)
        res_odd = df_clean[df_clean['Odd'] > 0].groupby('Range', observed=False).agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor (R$)': 'Lucro'})
        
        for range_val, row in res_odd.iterrows():
            roi = (row['Lucro'] / (row['Qtd'] * stake_padrao)) * 100 if row['Qtd'] > 0 else 0
            cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
            st.markdown(f'''<div class="perf-card">
                <div style="flex:2"><b style="color:white">Odd: {range_val}</b><br><small style="color:#94a3b8">{int(row['Qtd'])} entr. | {row['Lucro']/stake_padrao:,.2f} stk</small></div>
                <div style="flex:1; text-align:right;"><span class="{cor}">R$ {row['Lucro']:,.2f}</span><br><small style="color:#64748b">{roi:.1f}% ROI</small></div>
            </div>''', unsafe_allow_html=True)

    # --- 6. CALENDÁRIO (FIXED) ---
    st.markdown("<p style='color:#94a3b8; font-weight:800; margin-top:25px;'>📅 DIÁRIO DE OPERAÇÕES</p>", unsafe_allow_html=True)
    cal_obj = calendar.Calendar(firstweekday=0)
    # Pegando o mês do período selecionado
    dias_mes = list(cal_obj.itermonthdays(df_clean['Data'].iloc[-1].year, df_clean['Data'].iloc[-1].month))
    lucro_dia = df_clean.groupby(pd.to_datetime(df_clean['Data_Apenas']).dt.day)['Valor (R$)'].sum()

    html_cal = '<div class="calendar-grid">'
    for n in ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM']: html_cal += f'<div class="day-name">{n}</div>'
    for dia in dias_mes:
        if dia == 0: html_cal += '<div style="opacity:0"></div>'
        else:
            val = lucro_dia.get(dia, 0)
            classe = "day-card green-card" if val > 0.05 else "day-card red-card" if val < -0.05 else "day-card"
            txt_val = f"R$ {val:,.0f}" if val != 0 else "OFF"
            html_cal += f'<div class="{classe}"><span class="day-number">{dia}</span><span class="day-value">{txt_val}</span></div>'
    html_cal += '</div>'
    st.markdown(html_cal, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro: {e}")
