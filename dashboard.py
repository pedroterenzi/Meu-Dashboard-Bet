import streamlit as st
import pandas as pd
import calendar
import plotly.graph_objects as go
from datetime import datetime, date
import re
import numpy as np

# 1. CONFIGURAÇÃO DA PÁGINA (Ajustado para Mobile)
st.set_page_config(
    layout="wide", 
    page_title="Betting Analytics Pro", 
    page_icon="💎",
    initial_sidebar_state="collapsed" # Pode mudar para "expanded" se quiser que comece aberto
)

# --- ESTILIZAÇÃO CSS PREMIUM ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #020617; }
    .main .block-container { max-width: 1200px; padding-top: 1rem; margin: auto; }

    /* Ajuste para Mobile - Tira paddings excessivos */
    @media (max-width: 768px) {
        .main .block-container { padding-left: 10px; padding-right: 10px; }
        .metric-value { font-size: 1.3rem !important; }
    }

    /* Navegação Lateral */
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid rgba(255,255,255,0.05); }

    /* Cartões de Métricas */
    .metric-card {
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        padding: 15px 10px; border-radius: 20px; color: white; font-weight: 800;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.05);
        height: 100px; width: 100%; margin-bottom: 10px;
    }
    .metric-title { font-size: 0.65rem; text-transform: uppercase; opacity: 0.6; letter-spacing: 1px; margin-bottom: 3px; }
    .metric-value { font-size: 1.5rem; margin: 0; letter-spacing: -1px; }

    /* Cartão de Lucro Mensal */
    .monthly-profit-card {
        padding: 15px; border-radius: 15px; text-align: center; color: white; font-weight: 800;
        margin-bottom: 15px; border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Calendário Responsivo */
    .calendar-grid { 
        display: grid; 
        grid-template-columns: repeat(7, 1fr); 
        gap: 5px; 
        margin-top: 10px; 
    }
    .day-name { text-align: center; color: #475569; font-weight: 800; font-size: 0.6rem; text-transform: uppercase; }
    .day-card { 
        background: #0f172a; border-radius: 8px; padding: 8px; min-height: 70px; 
        display: flex; flex-direction: column; justify-content: space-between;
        border: 1px solid rgba(255, 255, 255, 0.03); 
    }
    @media (max-width: 600px) {
        .day-card { min-height: 60px; padding: 5px; }
        .day-value { font-size: 0.7rem !important; }
        .day-stakes { font-size: 0.55rem !important; }
    }

    .green-card { background: linear-gradient(135deg, #059669 0%, #064e3b 100%); border: none; }
    .red-card { background: linear-gradient(135deg, #dc2626 0%, #7f1d1d 100%); border: none; }
    .day-number { font-size: 0.7rem; font-weight: 800; color: #64748b; }
    .day-value { font-size: 0.8rem; font-weight: 800; color: white; }
    .day-stakes { font-size: 0.6rem; font-weight: 600; color: rgba(255,255,255,0.8); }

    /* Performance Cards */
    .perf-card { 
        background: #0f172a; border-radius: 12px; padding: 12px 15px; 
        display: flex; align-items: center; justify-content: space-between; 
        border: 1px solid rgba(255, 255, 255, 0.05); margin-bottom: 8px;
    }
    .val-pos { color: #10b981; font-weight: 800; }
    .val-neg { color: #f43f5e; font-weight: 800; }
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

# Sidebar principal
with st.sidebar:
    st.title("💎 Pro Trader")
    stake_padrao = st.number_input("Stake Padrão (R$)", value=600.0)
    st.markdown("---")
    menu = st.radio("Selecione a Visão:", ["📈 Performance Geral", "📅 Diário de Operações", "📊 Evolução Patrimonial", "⏰ Análise de Janelas"])

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

    # Lógica de Filtros Baseado no Menu
    if menu == "📅 Diário de Operações":
        with st.sidebar:
            st.markdown("---")
            anos_disponiveis = sorted(df['Data'].dt.year.unique(), reverse=True)
            ano_cal = st.selectbox("Ano", anos_disponiveis)
            meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
            mes_nome_cal = st.selectbox("Mês", meses_nomes, index=datetime.now().month - 1)
            mes_num_cal = meses_nomes.index(mes_nome_cal) + 1
        df_final = df[(df['Data'].dt.year == ano_cal) & (df['Data'].dt.month == mes_num_cal)].copy()
    else:
        with st.sidebar:
            st.markdown("---")
            periodo_global = st.date_input("Intervalo de Datas", [df['Data_Apenas'].min(), df['Data_Apenas'].max()])
        
        if len(periodo_global) == 2:
            df_final = df[(df['Data_Apenas'] >= periodo_global[0]) & (df['Data_Apenas'] <= periodo_global[1])].copy()
        else:
            df_final = pd.DataFrame()

    # Processamento Comum
    if not df_final.empty:
        def extract_id(row):
            match = re.search(r'Ref: (\d+)', str(row['Evento']))
            return match.group(1) if match else row.name
        
        df_final['ID_Ref'] = df_final.apply(extract_id, axis=1)
        df_clean = df_final.groupby(['ID_Ref', 'Data', 'Evento', 'Hora', 'Dia_Semana_Num']).agg({'Valor (R$)': 'sum'}).reset_index()
        df_clean['Data_Apenas'] = df_clean['Data'].dt.date

        df_clean['Est'] = df_clean['Evento'].apply(lambda x: str(x).split('Ref:')[0].split('/')[-1].strip() if '/' in str(x) else "Match Odds")
        df_clean['Odd'] = df_clean['Valor (R$)'].apply(lambda x: (x / stake_padrao) + 1 if x > 0 else 0)
        avg_odds = df_clean[df_clean['Odd'] > 0].groupby('Est')['Odd'].mean().to_dict()
        df_clean.loc[df_clean['Odd'] == 0, 'Odd'] = df_clean['Est'].map(avg_odds).fillna(1.50)

        total_l = df_clean['Valor (R$)'].sum()
        odd_m = df_clean[df_clean['Valor (R$)'] > 0]['Odd'].mean()

        # RENDERIZAÇÃO DAS PÁGINAS
        if menu == "📈 Performance Geral":
            bg_lucro = "linear-gradient(135deg, #10b981 0%, #064e3b 100%)" if total_l >= 0 else "linear-gradient(135deg, #ef4444 0%, #7f1d1d 100%)"
            st.markdown(f'<div class="metric-card" style="background: {bg_lucro}; margin-bottom: 20px;"><div class="metric-title">Lucro Líquido Total</div><div class="metric-value" style="font-size: 2rem;">{format_br(total_l)}</div></div>', unsafe_allow_html=True)
            
            c1, c2, c3 = st.columns(3)
            with c1: st.markdown(f'<div class="metric-card"><div class="metric-title">Odd Média</div><div class="metric-value">{odd_m:.2f}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><div class="metric-title">Stakes</div><div class="metric-value">{total_l/stake_padrao:,.2f}</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="metric-card"><div class="metric-title">Entradas</div><div class="metric-value">{len(df_clean)}</div></div>', unsafe_allow_html=True)

            col_est, col_odd = st.columns(2)
            with col_est:
                st.subheader("🎯 Estratégias")
                res_est = df_clean.groupby('Est').agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor (R$)': 'Lucro'}).sort_values('Lucro', ascending=False)
                for est, row in res_est.iterrows():
                    roi = (row['Lucro'] / (row['Qtd'] * stake_padrao)) * 100
                    cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
                    st.markdown(f'''<div class="perf-card"><div><b>{est}</b><br><small>{int(row['Qtd'])} entr.</small></div><div style="text-align:right"><span class="{cor}">{format_br(row['Lucro'])}</span><br><small>{roi:.1f}% ROI</small></div></div>''', unsafe_allow_html=True)
            with col_odd:
                st.subheader("📊 Ranges de Odd")
                bins = [0, 1.30, 1.59, 1.79, 2.09, 3.0, 1000]
                labels = ['1.00-1.30', '1.31-1.59', '1.60-1.79', '1.80-2.09', '2.10-3.00', '3.00+']
                df_clean['Range'] = pd.cut(df_clean['Odd'], bins=bins, labels=labels)
                res_odd = df_clean.groupby('Range', observed=False).agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor (R$)': 'Lucro'})
                for r, row in res_odd.iterrows():
                    roi = (row['Lucro'] / (row['Qtd'] * stake_padrao)) * 100 if row['Qtd'] > 0 else 0
                    cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
                    st.markdown(f'''<div class="perf-card"><div><b>Odd {r}</b><br><small>{int(row['Qtd'])} entr.</small></div><div style="text-align:right"><span class="{cor}">{format_br(row['Lucro'])}</span><br><small>{roi:.1f}% ROI</small></div></div>''', unsafe_allow_html=True)

        elif menu == "📅 Diário de Operações":
            bg_mensal = "rgba(16, 185, 129, 0.2)" if total_l >= 0 else "rgba(244, 63, 94, 0.2)"
            border_mensal = "#10b981" if total_l >= 0 else "#f43f5e"
            st.markdown(f'<div class="monthly-profit-card" style="background-color: {bg_mensal}; border: 2px solid {border_mensal};"> <span style="font-size: 0.7rem; opacity: 0.8;">LUCRO EM {mes_nome_cal.upper()}</span><br><span style="font-size: 1.8rem;">{format_br(total_l)}</span><br><span style="font-size: 0.8rem; opacity: 0.8;">{(total_l/stake_padrao):,.2f} STAKES</span></div>', unsafe_allow_html=True)
            
            cal_obj = calendar.Calendar(firstweekday=0)
            dias_mes = list(cal_obj.itermonthdays(ano_cal, mes_num_cal))
            lucro_dia = df_clean.groupby(df_clean['Data'].dt.day)['Valor (R$)'].sum()
            html_cal = '<div class="calendar-grid">'
            for n in ['S', 'T', 'Q', 'Q', 'S', 'S', 'D']: html_cal += f'<div class="day-name">{n}</div>'
            for dia in dias_mes:
                if dia == 0: html_cal += '<div style="opacity:0"></div>'
                else:
                    val = lucro_dia.get(dia, 0)
                    stks = val / stake_padrao
                    classe = "day-card green-card" if val > 0.05 else "day-card red-card" if val < -0.05 else "day-card"
                    txt_val = format_br(val) if abs(val) > 0.05 else ""
                    txt_stk = f"{stks:,.1f} STK" if abs(val) > 0.05 else ""
                    html_cal += f'<div class="{classe}"><span class="day-number">{dia}</span><span class="day-value">{txt_val}</span><span class="day-stakes">{txt_stk}</span></div>'
            html_cal += '</div>'
            st.markdown(html_cal, unsafe_allow_html=True)

        elif menu == "📊 Evolução Patrimonial":
            df_diario = df_clean.groupby('Data_Apenas')['Valor (R$)'].sum().reset_index()
            df_diario['Acumulado'] = df_diario['Valor (R$)'].cumsum()
            y, x = df_diario['Acumulado'].tolist(), df_diario['Data_Apenas'].tolist()
            fig_evol = go.Figure()
            for i in range(len(y)-1):
                cor = '#10b981' if y[i+1] >= 0 else '#f43f5e'
                fig_evol.add_trace(go.Scatter(x=x[i:i+2], y=y[i:i+2], mode='lines', line=dict(color=cor, width=3, shape='spline', smoothing=1.3), hoverinfo='skip', showlegend=False))
            fig_evol.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=10, b=0), height=450, xaxis=dict(showgrid=False, color='#475569'), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.03)', color='#475569'))
            st.plotly_chart(fig_evol, use_container_width=True, config={'displayModeBar': False})

        elif menu == "⏰ Análise de Janelas":
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📅 Dias da Semana")
                dias_semana = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
                res_dia = df_clean.groupby('Dia_Semana_Num').agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor (R$)': 'Lucro'})
                for i in range(7):
                    if i not in res_dia.index: res_dia.loc[i] = [0, 0]
                for idx, row in res_dia.sort_index().iterrows():
                    roi = (row['Lucro'] / (row['Qtd'] * stake_padrao)) * 100 if row['Qtd'] > 0 else 0
                    cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
                    st.markdown(f'''<div class="perf-card"><div><b>{dias_semana[idx]}</b></div><div style="text-align:right"><span class="{cor}">{format_br(row['Lucro'])}</span><br><small>{roi:.1f}% ROI</small></div></div>''', unsafe_allow_html=True)
            with c2:
                st.subheader("⌚ Horários")
                bins_h = [0, 6, 12, 18, 24]; labels_h = ['Madrugada', 'Manhã', 'Tarde', 'Noite']
                df_clean['Faixa_Hora'] = pd.cut(df_clean['Hora'], bins=bins_h, labels=labels_h, include_lowest=True)
                res_hora = df_clean.groupby('Faixa_Hora', observed=False).agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor (R$)': 'Lucro'})
                for faixa, row in res_hora.iterrows():
                    roi = (row['Lucro'] / (row['Qtd'] * stake_padrao)) * 100 if row['Qtd'] > 0 else 0
                    cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
                    st.markdown(f'''<div class="perf-card"><div><b>{faixa}</b></div><div style="text-align:right"><span class="{cor}">{format_br(row['Lucro'])}</span><br><small>{roi:.1f}% ROI</small></div></div>''', unsafe_allow_html=True)

    else:
        st.info("ℹ️ Abra o menu lateral para selecionar os filtros.")

except Exception as e:
    st.error(f"⚠️ Erro: {e}")
