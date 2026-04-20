import streamlit as st
import pandas as pd
import calendar
import plotly.express as px
import re

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Betting Analytics Pro", page_icon="💎")

# --- ESTILIZAÇÃO CSS PREMIUM (FOCO NO ALINHAMENTO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #0f172a; }

    /* Forçar container das métricas a não quebrar */
    [data-testid="stHorizontalBlock"] {
        align-items: stretch;
    }

    /* Cartões de Métricas - ALTURA FIXA E ALINHAMENTO */
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
        height: 120px; /* Altura fixa para todos serem iguais */
        width: 100%;
        margin-bottom: 10px;
    }

    .metric-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
        opacity: 0.8;
        margin-bottom: 8px;
    }

    .metric-value {
        font-size: 1.6rem;
        margin: 0;
        line-height: 1;
    }

    /* Grid do Calendário */
    .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; margin-top: 20px; }
    .day-name { text-align: center; color: #94a3b8; font-weight: 800; font-size: 0.75rem; text-transform: uppercase; }
    
    .day-card { 
        background: #1e293b; 
        border-radius: 12px; 
        padding: 10px; 
        min-height: 80px; 
        display: flex; 
        flex-direction: column; 
        justify-content: space-between;
        border: 1px solid rgba(255, 255, 255, 0.05); 
    }
    .day-number { font-size: 0.9rem; font-weight: 800; color: #f8fafc; }
    .day-value { font-size: 0.8rem; font-weight: 700; }
    
    .green-card { background: linear-gradient(135deg, #059669 0%, #064e3b 100%); border: none; }
    .red-card { background: linear-gradient(135deg, #dc2626 0%, #7f1d1d 100%); border: none; }

    /* Performance Cards */
    .perf-card { 
        background: #1e293b; 
        border-radius: 12px; 
        padding: 15px 20px; 
        display: flex; 
        align-items: center; 
        justify-content: space-between; 
        border: 1px solid rgba(255, 255, 255, 0.05);
        margin-bottom: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

# TÍTULO EXECUTIVE
st.markdown("<h1 style='text-align: center; color: white; font-size: 2.2rem; font-weight: 800; letter-spacing: -2px; margin-bottom: 30px;'> <span style='color: #10b981;'>BETTING</span> ANALYTICS <span style='font-weight: 100; opacity: 0.5;'>|</span> EXECUTIVE</h1>", unsafe_allow_html=True)

# --- 2. BARRA LATERAL ---
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

        # Cálculos
        df_clean['Lucro_Acumulado'] = df_clean['Valor (R$)'].cumsum()
        df_clean['Odd'] = df_clean['Valor (R$)'].apply(lambda x: (x / stake_padrao) + 1 if x > 0 else 0)

        # --- 3. MÉTRICAS TOPO (REMODELADAS PARA ALINHAMENTO) ---
        total_l = df_clean['Valor (R$)'].sum()
        odd_m = df_clean[df_clean['Odd'] > 0]['Odd'].mean()
        
        c1, c2, c3, c4 = st.columns(4)
        
        with c1:
            st.markdown(f'''<div class="metric-card" style="background: linear-gradient(135deg, #10b981 0%, #064e3b 100%);">
                <div class="metric-title">Lucro Líquido</div>
                <div class="metric-value">R$ {total_l:,.2f}</div>
            </div>''', unsafe_allow_html=True)
        with c2:
            st.markdown(f'''<div class="metric-card" style="background: #1e293b;">
                <div class="metric-title">Odd Média</div>
                <div class="metric-value">{odd_m:.2f}</div>
            </div>''', unsafe_allow_html=True)
        with c3:
            st.markdown(f'''<div class="metric-card" style="background: #1e293b;">
                <div class="metric-title">Saldo Stakes</div>
                <div class="metric-value">{total_l/stake_padrao:,.2f}</div>
            </div>''', unsafe_allow_html=True)
        with c4:
            st.markdown(f'''<div class="metric-card" style="background: #1e293b;">
                <div class="metric-title">Entradas</div>
                <div class="metric-value">{len(df_clean)}</div>
            </div>''', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # --- 4. GRÁFICOS ---
        col_graf1, col_graf2 = st.columns([2, 1])
        
        with col_graf1:
            st.subheader("📈 Curva de Crescimento")
            fig_evol = px.line(df_clean, x='Data_Apenas', y='Lucro_Acumulado', template="plotly_dark", color_discrete_sequence=['#10b981'])
            fig_evol.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0))
            st.plotly_chart(fig_evol, use_container_width=True)

        with col_graf2:
            st.subheader("📊 Profit por Range de Odd")
            bins = [0, 1.30, 1.60, 2.0, 3.0, 100]
            labels = ['1.01-1.30', '1.31-1.60', '1.61-2.0', '2.01-3.0', '3.0+']
            df_clean['Range'] = pd.cut(df_clean['Odd'], bins=bins, labels=labels)
            range_df = df_clean[df_clean['Odd'] > 0].groupby('Range', observed=False)['Valor (R$)'].sum().reset_index()
            fig_bar = px.bar(range_df, x='Range', y='Valor (R$)', template="plotly_dark", color_discrete_sequence=['#10b981'])
            fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)')
            st.plotly_chart(fig_bar, use_container_width=True)

        # --- 5. CALENDÁRIO ---
        st.subheader("📅 Diário Operacional")
        ano, mes = start.year, start.month
        cal = calendar.Calendar(firstweekday=0)
        dias_mes = list(cal.itermonthdays(ano, mes))
        lucro_dia = df_clean.groupby(pd.to_datetime(df_clean['Data_Apenas']).dt.day)['Valor (R$)'].sum()

        html_cal = '<div class="calendar-grid">'
        for n in ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM']: html_cal += f'<div class="day-name">{n}</div>'
        for dia in dias_mes:
            if dia == 0: html_cal += '<div style="opacity:0"></div>'
            else:
                val = lucro_dia.get(dia, 0)
                classe = "day-card green-card" if val > 0.05 else "day-card red-card" if val < -0.05 else "day-card"
                txt_val = f"R$ {val:,.2f}" if val != 0 else "OFF"
                html_cal += f'<div class="{classe}"><span class="day-number">{dia}</span><span class="day-value">{txt_val}</span></div>'
        html_cal += '</div>'
        st.markdown(html_cal, unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro no processamento: {e}")
