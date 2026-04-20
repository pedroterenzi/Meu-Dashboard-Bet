import streamlit as st
import pandas as pd
import calendar
import plotly.express as px
import plotly.graph_objects as go
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Betting Analytics Pro", page_icon="💎")

# --- ESTILIZAÇÃO CSS PREMIUM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0f172a; }

    /* Cartões de Métricas */
    .metric-card {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        padding: 20px 10px;
        border-radius: 20px;
        color: white;
        font-weight: 800;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.1);
        height: 110px;
        width: 100%;
        margin-bottom: 10px;
    }
    .metric-title { font-size: 0.75rem; text-transform: uppercase; letter-spacing: 1px; opacity: 0.7; margin-bottom: 5px; }
    .metric-value { font-size: 1.5rem; margin: 0; line-height: 1; }

    /* Grid do Calendário */
    .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 8px; margin-top: 20px; }
    .day-name { text-align: center; color: #64748b; font-weight: 800; font-size: 0.7rem; text-transform: uppercase; padding-bottom: 5px; }
    .day-card { 
        background: #1e293b; border-radius: 10px; padding: 10px; min-height: 75px; 
        display: flex; flex-direction: column; justify-content: space-between;
        border: 1px solid rgba(255, 255, 255, 0.03); 
    }
    .day-number { font-size: 0.85rem; font-weight: 800; color: #94a3b8; }
    .day-value { font-size: 0.75rem; font-weight: 700; }
    .green-card { background: linear-gradient(135deg, #059669 0%, #064e3b 100%); border: none; color: white; }
    .red-card { background: linear-gradient(135deg, #dc2626 0%, #7f1d1d 100%); border: none; color: white; }
    .green-card .day-number, .red-card .day-number { color: rgba(255,255,255,0.7); }
    </style>
    """, unsafe_allow_html=True)

# TÍTULO EXECUTIVE
st.markdown("<h1 style='text-align: center; color: white; font-size: 2rem; font-weight: 800; letter-spacing: -1.5px; margin-bottom: 20px;'> <span style='color: #10b981;'>BETTING</span> ANALYTICS <span style='font-weight: 100; opacity: 0.3;'>|</span> EXECUTIVE</h1>", unsafe_allow_html=True)

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

    df_f = df.copy()
    def extract_id(row):
        match = re.search(r'Ref: (\d+)', str(row['Evento']))
        return match.group(1) if match else row.name
    df_f['ID_Ref'] = df_f.apply(extract_id, axis=1)
    df_clean = df_f.groupby(['ID_Ref', 'Data_Apenas', 'Evento']).agg({'Valor (R$)': 'sum'}).reset_index()

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

    # --- 4. GRÁFICOS REESTILIZADOS ---
    col_graf1, col_graf2 = st.columns([2, 1])
    
    with col_graf1:
        st.markdown("<p style='color:#94a3b8; font-weight:800; margin-bottom:0;'>📈 EVOLUÇÃO PATRIMONIAL</p>", unsafe_allow_html=True)
        fig_evol = go.Figure()
        fig_evol.add_trace(go.Scatter(
            x=df_clean['Data_Apenas'], y=df_clean['Lucro_Acumulado'],
            mode='lines', line=dict(color='#10b981', width=4, shape='spline'), # Linha curva e grossa
            fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.1)' # Preenchimento suave abaixo da linha
        ))
        fig_evol.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0), height=300,
            xaxis=dict(showgrid=False, color='#64748b'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#64748b')
        )
        st.plotly_chart(fig_evol, use_container_width=True, config={'displayModeBar': False})

    with col_graf2:
        st.markdown("<p style='color:#94a3b8; font-weight:800; margin-bottom:0;'>📊 PROFIT POR RANGE</p>", unsafe_allow_html=True)
        bins = [0, 1.30, 1.60, 2.0, 3.0, 100]; labels = ['1.0-1.3', '1.3-1.6', '1.6-2.0', '2.0-3.0', '3.0+']
        df_clean['Range'] = pd.cut(df_clean['Odd'], bins=bins, labels=labels)
        range_df = df_clean[df_clean['Odd'] > 0].groupby('Range', observed=False)['Valor (R$)'].sum().reset_index()
        
        fig_bar = go.Figure(go.Bar(
            x=range_df['Range'], y=range_df['Valor (R$)'],
            marker_color='#10b981', marker_line_width=0, opacity=0.8
        ))
        fig_bar.update_layout(
            paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(l=0, r=0, t=30, b=0), height=300,
            xaxis=dict(showgrid=False, color='#64748b'),
            yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', color='#64748b')
        )
        st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

    # --- 5. CALENDÁRIO ---
    st.markdown("<p style='color:#94a3b8; font-weight:800; margin-top:20px; margin-bottom:0;'>📅 DIÁRIO DE OPERAÇÕES</p>", unsafe_allow_html=True)
    cal = calendar.Calendar(firstweekday=0)
    dias_mes = list(cal.itermonthdays(datetime.now().year, datetime.now().month))
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
