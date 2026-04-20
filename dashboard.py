import streamlit as st
import pandas as pd
import calendar
import plotly.express as plotly_ex # Adicionado para gráficos mais bonitos
from datetime import datetime
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Betting Analytics Pro", page_icon="💎")

# --- ESTILIZAÇÃO CSS PREMIUM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0f172a; }

    /* Grid do Calendário */
    .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; margin-top: 20px; }
    @media (max-width: 768px) { .calendar-grid { grid-template-columns: repeat(1, 1fr); } }

    .day-card { background: #1e293b; border-radius: 12px; padding: 12px; min-height: 80px; border: 1px solid rgba(255, 255, 255, 0.05); }
    .green-card { background: linear-gradient(135deg, #059669 0%, #064e3b 100%); border: none; }
    .red-card { background: linear-gradient(135deg, #dc2626 0%, #7f1d1d 100%); border: none; }
    
    /* Cartões de Métricas */
    .metric-card { padding: 20px; border-radius: 20px; text-align: center; color: white; font-weight: 800; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }
    
    /* Performance Cards */
    .perf-container { display: flex; flex-direction: column; gap: 10px; }
    .perf-card { background: #1e293b; border-radius: 12px; padding: 15px 25px; display: flex; align-items: center; justify-content: space-between; border: 1px solid rgba(255, 255, 255, 0.05); }
    </style>
    """, unsafe_allow_html=True)

# TÍTULO EXECUTIVE
st.markdown("<h1 style='text-align: center; color: white; font-size: 2.5rem; font-weight: 800; letter-spacing: -2px;'> <span style='color: #10b981;'>BETTING</span> ANALYTICS <span style='font-weight: 100; opacity: 0.5;'>|</span> EXECUTIVE</h1>", unsafe_allow_html=True)

# --- 2. PAINEL LATERAL ---
st.sidebar.header("🕹️ Painel de Controle")
arquivo_path = st.sidebar.text_input("Arquivo CSV", "Betfair.csv")
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

    data_sel = st.sidebar.date_input("Período", [df['Data_Apenas'].min(), df['Data_Apenas'].max()])

    if len(data_sel) == 2:
        start, end = data_sel
        df_f = df[(df['Data_Apenas'] >= start) & (df['Data_Apenas'] <= end)].copy()
        
        def extract_id(row):
            match = re.search(r'Ref: (\d+)', str(row['Evento']))
            return match.group(1) if match else row.name
            
        df_f['ID_Ref'] = df_f.apply(extract_id, axis=1)
        df_clean = df_f.groupby(['ID_Ref', 'Data_Apenas', 'Evento']).agg({'Valor (R$)': 'sum'}).reset_index()

        # --- CÁLCULOS DE ODDS E ACUMULADO ---
        # Odd aproximada: (Lucro / Stake) + 1 se for positivo. Se for negativo, consideramos que perdeu a stake.
        def calc_odd(val):
            if val > 0: return (val / stake_padrao) + 1
            return 0 # Reds não entram no cálculo de odd média de acerto

        df_clean['Odd'] = df_clean['Valor (R$)'].apply(calc_odd)
        df_clean['Lucro_Acumulado'] = df_clean['Valor (R$)'].cumsum()

        # --- 3. MÉTRICAS TOPO ---
        total_l = df_clean['Valor (R$)'].sum()
        odd_media = df_clean[df_clean['Odd'] > 0]['Odd'].mean()
        
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.markdown(f'<div class="metric-card" style="background:#10b981">Lucro Total<br><span style="font-size:24px">R$ {total_l:,.2f}</span></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card" style="background:#1e293b; border:1px solid #334155">Odd Média (Greens)<br><span style="font-size:24px">{odd_media:.2f}</span></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card" style="background:#1e293b; border:1px solid #334155">Stakes Totais<br><span style="font-size:24px">{total_l/stake_padrao:,.2f}</span></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="metric-card" style="background:#1e293b; border:1px solid #334155">Entradas<br><span style="font-size:24px">{len(df_clean)}</span></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- 4. GRÁFICO ACUMULADO ---
        st.subheader("📈 Curva de Crescimento (Profit Curve)")
        fig_evol = plotly_ex.line(df_clean, x='Data_Apenas', y='Lucro_Acumulado', template="plotly_dark", color_discrete_sequence=['#10b981'])
        fig_evol.update_layout(yaxis_title="Lucro Acumulado (R$)", xaxis_title="Data")
        st.plotly_chart(fig_evol, use_container_width=True)

        # --- 5. CALENDÁRIO ---
        st.subheader("📅 Calendário Operacional")
        # (Código do calendário simplificado por espaço, mas mantendo a lógica de cores)
        ano, mes = start.year, start.month
        cal = calendar.Calendar(firstweekday=0)
        dias_mes = list(cal.itermonthdays(ano, mes))
        lucro_dia = df_clean.groupby(pd.to_datetime(df_clean['Data_Apenas']).dt.day)['Valor (R$)'].sum()
        
        cols_names = ['Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb', 'Dom']
        html_cal = '<div class="calendar-grid">'
        for name in cols_names: html_cal += f'<div class="day-name">{name}</div>'
        for dia in dias_mes:
            if dia == 0: html_cal += '<div class="empty-card"></div>'
            else:
                valor = lucro_dia.get(dia, 0)
                card_class = "day-card green-card" if valor > 0.05 else "day-card red-card" if valor < -0.05 else "day-card"
                html_cal += f'<div class="{card_class}"><span class="day-number">{dia}</span><br><span class="day-value">{"R$ "+f"{valor:,.2f}" if valor != 0 else "OFF"}</span></div>'
        html_cal += '</div>'
        st.markdown(html_cal, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- 6. LUCRO POR RANGE DE ODD ---
        st.subheader("📊 Lucro por Faixa de Odd")
        bins = [0, 1.20, 1.50, 1.80, 2.20, 3.0, 5.0, 100]
        labels = ['1.01-1.20', '1.21-1.50', '1.51-1.80', '1.81-2.20', '2.21-3.00', '3.01-5.00', '5.00+']
        df_clean['Faixa_Odd'] = pd.cut(df_clean['Odd'], bins=bins, labels=labels)
        
        range_lucro = df_clean[df_clean['Odd'] > 0].groupby('Faixa_Odd')['Valor (R$)'].sum().reset_index()
        fig_range = plotly_ex.bar(range_lucro, x='Faixa_Odd', y='Valor (R$)', template="plotly_dark", color='Valor (R$)', color_continuous_scale='Greens')
        st.plotly_chart(fig_range, use_container_width=True)

        # --- 7. PERFORMANCE POR ESTRATÉGIA ---
        st.subheader("🎯 Performance por Estratégia")
        def extrair_est(txt): return str(txt).split('Ref:')[0].split('/')[-1].strip() if '/' in str(txt) else "Match Odds"
        df_clean['Estrategia'] = df_clean['Evento'].apply(extrair_est)
        resumo = df_clean.groupby('Estrategia').agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Entradas', 'Valor (R$)': 'Lucro'}).sort_values('Lucro', ascending=False)
        
        for est, row in resumo.iterrows():
            roi = (row['Lucro'] / (row['Entradas'] * stake_padrao)) * 100
            color = "#10b981" if row['Lucro'] >= 0 else "#ef4444"
            st.markdown(f'''
                <div class="perf-card">
                    <div style="flex:2"><b>{est}</b><br><small style="color:#94a3b8">{int(row['Entradas'])} Entr. | ROI: {roi:.1f}%</small></div>
                    <div style="flex:1; text-align:right; color:{color}; font-weight:800">R$ {row['Lucro']:,.2f}</div>
                </div>''', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro: {e}")
