import streamlit as st
import pandas as pd
import calendar
import plotly.graph_objects as go
from datetime import datetime
import re
import numpy as np

# 1. CONFIGURAÇÃO DA PÁGINA
st.set_page_config(layout="wide", page_title="Betting Analytics Pro", page_icon="💎")

# --- ESTILIZAÇÃO CSS PREMIUM (COM FOCO NOS BOTÕES DE NAVEGAÇÃO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    * { font-family: 'Inter', sans-serif; }
    .stApp { background-color: #020617; }
    .main .block-container { max-width: 1200px; padding-top: 1.5rem; margin: auto; }

    /* --- NAVEGAÇÃO POR BOTÕES LARGOS (SIDEBAR) --- */
    /* Remove as bolinhas originais */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }
    
    /* Transforma o label em um botão sólido */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label {
        background-color: #1e293b;
        border: 1px solid rgba(255, 255, 255, 0.05);
        padding: 12px 20px !important;
        border-radius: 12px !important;
        margin-bottom: 8px !important;
        width: 100% !important;
        display: block !important;
        transition: all 0.3s ease;
        cursor: pointer;
    }

    /* Efeito quando o botão está selecionado */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(135deg, #10b981 0%, #064e3b 100%) !important;
        border: none !important;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);
    }
    
    /* Texto dentro do botão de navegação */
    [data-testid="stSidebar"] .stRadio div[role="radiogroup"] > label div[data-testid="stMarkdownContainer"] p {
        color: white !important;
        font-weight: 700 !important;
        font-size: 0.9rem !important;
        margin: 0 !important;
        text-align: center;
    }

    /* --- RESTANTE DOS VISUAIS MANTIDOS --- */
    .metric-card {
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        padding: 20px 10px; border-radius: 20px; color: white; font-weight: 800;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); border: 1px solid rgba(255, 255, 255, 0.05);
        height: 110px; width: 100%; margin-bottom: 15px;
    }
    .metric-title { font-size: 0.7rem; text-transform: uppercase; opacity: 0.6; letter-spacing: 1.2px; margin-bottom: 5px; }
    .metric-value { font-size: 1.6rem; margin: 0; letter-spacing: -1px; }

    .monthly-profit-card {
        padding: 15px; border-radius: 15px; text-align: center; color: white; font-weight: 800;
        margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .calendar-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 10px; margin-top: 15px; }
    .day-name { text-align: center; color: #475569; font-weight: 800; font-size: 0.7rem; text-transform: uppercase; }
    .day-card { 
        background: #0f172a; border-radius: 12px; padding: 12px; min-height: 95px; 
        display: flex; flex-direction: column; justify-content: space-between;
        border: 1px solid rgba(255, 255, 255, 0.03); 
    }
    .green-card { background: linear-gradient(135deg, #059669 0%, #064e3b 100%); border: none; }
    .red-card { background: linear-gradient(135deg, #dc2626 0%, #7f1d1d 100%); border: none; }

    .perf-card { 
        background: #0f172a; border-radius: 12px; padding: 15px 20px; 
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
stake_padrao = st.sidebar.number_input("Stake Padrão (R$)", value=600.0)

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

    # --- MENU DE NAVEGAÇÃO COM BOTÕES ---
    st.sidebar.markdown("---")
    menu = st.sidebar.radio(
        "Navegação", 
        ["📈 Performance Geral", "📅 Diário de Operações", "📊 Evolução Patrimonial", "⏰ Análise de Janelas"],
        label_visibility="collapsed"
    )

    # Lógica de Filtros por Aba
    if menu == "📅 Diário de Operações":
        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 Filtro do Mês")
        anos_disponiveis = sorted(df['Data'].dt.year.unique(), reverse=True)
        ano_cal = st.sidebar.selectbox("Ano", anos_disponiveis)
        meses_nomes = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        mes_nome_cal = st.sidebar.selectbox("Mês", meses_nomes, index=datetime.now().month - 1)
        mes_num_cal = meses_nomes.index(mes_nome_cal) + 1
        df_final = df[(df['Data'].dt.year == ano_cal) & (df['Data'].dt.month == mes_num_cal)].copy()
    else:
        st.sidebar.markdown("---")
        st.sidebar.subheader("📅 Filtro de Datas Global")
        periodo_global = st.sidebar.date_input("Intervalo das Análises", [df['Data_Apenas'].min(), df['Data_Apenas'].max()])
        if len(periodo_global) == 2:
            df_final = df[(df['Data_Apenas'] >= periodo_global[0]) & (df['Data_Apenas'] <= periodo_global[1])].copy()
        else:
            df_final = pd.DataFrame()

    if not df_final.empty:
        # Processamento de Dados (ID, Estratégia, Odds)
        df_final['ID_Ref'] = df_final['Evento'].apply(lambda x: re.search(r'Ref: (\d+)', str(x)).group(1) if re.search(r'Ref: (\d+)', str(x)) else "0")
        df_clean = df_final.groupby(['ID_Ref', 'Data', 'Evento', 'Hora', 'Dia_Semana_Num']).agg({'Valor (R$)': 'sum'}).reset_index()
        df_clean['Data_Apenas'] = df_clean['Data'].dt.date
        df_clean['Est'] = df_clean['Evento'].apply(lambda x: str(x).split('Ref:')[0].split('/')[-1].strip() if '/' in str(x) else "Match Odds")
        df_clean['Odd'] = df_clean['Valor (R$)'].apply(lambda x: (x / stake_padrao) + 1 if x > 0 else 0)
        avg_odds = df_clean[df_clean['Odd'] > 0].groupby('Est')['Odd'].mean().to_dict()
        df_clean.loc[df_clean['Odd'] == 0, 'Odd'] = df_clean['Est'].map(avg_odds).fillna(1.50)

        total_l = df_clean['Valor (R$)'].sum()
        odd_m = df_clean[df_clean['Valor (R$)'] > 0]['Odd'].mean()

        # ---------------------------------------------------------
        # PÁGINAS (VISUAIS MANTIDOS)
        # ---------------------------------------------------------
        if menu == "📈 Performance Geral":
            st.markdown(f"<h2 style='color: white;'>Resumo Geral</h2>", unsafe_allow_html=True)
            bg_lucro = "linear-gradient(135deg, #10b981 0%, #064e3b 100%)" if total_l >= 0 else "linear-gradient(135deg, #ef4444 0%, #7f1d1d 100%)"
            c1, c2, c3, c4 = st.columns(4)
            with c1: st.markdown(f'<div class="metric-card" style="background: {bg_lucro};"><div class="metric-title">Lucro Líquido</div><div class="metric-value">{format_br(total_l)}</div></div>', unsafe_allow_html=True)
            with c2: st.markdown(f'<div class="metric-card"><div class="metric-title">Odd Média</div><div class="metric-value">{odd_m:.2f}</div></div>', unsafe_allow_html=True)
            with c3: st.markdown(f'<div class="metric-card"><div class="metric-title">Saldo Stakes</div><div class="metric-value">{total_l/stake_padrao:,.2f}</div></div>', unsafe_allow_html=True)
            with c4: st.markdown(f'<div class="metric-card"><div class="metric-title">Entradas</div><div class="metric-value">{len(df_clean)}</div></div>', unsafe_allow_html=True)

            col_est, col_odd = st.columns(2)
            with col_est:
                st.subheader("🎯 Por Estratégia")
                res_est = df_clean.groupby('Est').agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor (R$)': 'Lucro'}).sort_values('Lucro', ascending=False)
                for est, row in res_est.iterrows():
                    cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
                    st.markdown(f'''<div class="perf-card"><div style="flex:2"><b style="color:white">{est}</b><br><small style="color:#64748b">{int(row['Qtd'])} entr.</small></div><div style="text-align:right;"><span class="{cor}">{format_br(row['Lucro'])}</span><br><small style="color:#475569">{(row['Lucro']/(row['Qtd']*stake_padrao))*100:.1f}% ROI</small></div></div>''', unsafe_allow_html=True)
            with col_odd:
                st.subheader("📊 Por Range de Odd")
                bins = [0, 1.30, 1.59, 1.79, 2.09, 3.0, 1000]
                labels = ['1.00-1.30', '1.31-1.59', '1.60-1.79', '1.80-2.09', '2.10-3.00', '3.00+']
                df_clean['Range'] = pd.cut(df_clean['Odd'], bins=bins, labels=labels)
                res_odd = df_clean.groupby('Range', observed=False).agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor (R$)': 'Lucro'})
                for r, row in res_odd.iterrows():
                    cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
                    st.markdown(f'''<div class="perf-card"><div style="flex:2"><b style="color:white">Odd: {r}</b></div><div style="text-align:right;"><span class="{cor}">{format_br(row['Lucro'])}</span><br><small style="color:#475569">{int(row['Qtd'])} entr.</small></div></div>''', unsafe_allow_html=True)

        elif menu == "📅 Diário de Operações":
            st.subheader(f"Diário: {mes_nome_cal} {ano_cal}")
            bg_m = "rgba(16, 185, 129, 0.2)" if total_l >= 0 else "rgba(244, 63, 94, 0.2)"
            st.markdown(f'<div class="monthly-profit-card" style="background-color: {bg_m}; border: 2px solid {"#10b981" if total_l >= 0 else "#f43f5e"};"><small>LUCRO EM {mes_nome_cal.upper()}</small><br><span style="font-size: 1.8rem;">{format_br(total_l)}</span></div>', unsafe_allow_html=True)
            cal_obj = calendar.Calendar(firstweekday=0)
            dias_mes = list(cal_obj.itermonthdays(ano_cal, mes_num_cal))
            lucro_dia = df_clean.groupby(df_clean['Data'].dt.day)['Valor (R$)'].sum()
            html_cal = '<div class="calendar-grid">'
            for n in ['SEG', 'TER', 'QUA', 'QUI', 'SEX', 'SAB', 'DOM']: html_cal += f'<div class="day-name">{n}</div>'
            for dia in dias_mes:
                if dia == 0: html_cal += '<div style="opacity:0"></div>'
                else:
                    val = lucro_dia.get(dia, 0)
                    cl = "day-card green-card" if val > 0.05 else "day-card red-card" if val < -0.05 else "day-card"
                    html_cal += f'<div class="{cl}"><span class="day-number">{dia}</span><span class="day-value">{format_br(val) if abs(val)>0.05 else ""}</span><span class="day-stakes">{(val/stake_padrao):,.1f} STK</span></div>'
            html_cal += '</div>'
            st.markdown(html_cal, unsafe_allow_html=True)

        elif menu == "📊 Evolução Patrimonial":
            df_diario = df_clean.groupby('Data_Apenas')['Valor (R$)'].sum().reset_index()
            df_diario['Acumulado'] = df_diario['Valor (R$)'].cumsum()
            y, x = df_diario['Acumulado'].tolist(), df_diario['Data_Apenas'].tolist()
            fig_evol = go.Figure()
            for i in range(len(y)-1):
                cor = '#10b981' if y[i+1] >= 0 else '#f43f5e'
                fig_evol.add_trace(go.Scatter(x=x[i:i+2], y=y[i:i+2], mode='lines', line=dict(color=cor, width=2.5, shape='spline', smoothing=1.3), hoverinfo='skip', showlegend=False))
            fig_evol.add_trace(go.Scatter(x=x, y=y, mode='lines', line=dict(color='rgba(0,0,0,0)'), fill='tozeroy', fillcolor='rgba(16, 185, 129, 0.03)' if total_l >= 0 else 'rgba(244, 63, 94, 0.03)', showlegend=False))
            fig_evol.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', margin=dict(l=0, r=0, t=20, b=0), height=500, xaxis=dict(showgrid=False, color='#475569'), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.03)', color='#475569'))
            st.plotly_chart(fig_evol, use_container_width=True, config={'displayModeBar': False})

        elif menu == "⏰ Análise de Janelas":
            st.markdown("<h2 style='color: white;'>Análise Temporal</h2>", unsafe_allow_html=True)
            col_dia, col_hora = st.columns(2)
            with col_dia:
                st.subheader("📅 Por Dia")
                dias_s = {0: 'Segunda', 1: 'Terça', 2: 'Quarta', 3: 'Quinta', 4: 'Sexta', 5: 'Sábado', 6: 'Domingo'}
                res_dia = df_clean.groupby('Dia_Semana_Num').agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor (R$)': 'Lucro'}).sort_index()
                for idx, row in res_dia.iterrows():
                    cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
                    st.markdown(f'''<div class="perf-card"><div style="flex:2"><b style="color:white">{dias_s[idx]}</b></div><div style="text-align:right;"><span class="{cor}">{format_br(row['Lucro'])}</span></div></div>''', unsafe_allow_html=True)
            with col_hora:
                st.subheader("⌚ Por Horário")
                df_clean['FH'] = pd.cut(df_clean['Hora'], bins=[0, 6, 12, 18, 24], labels=['Madrugada', 'Manhã', 'Tarde', 'Noite'], include_lowest=True)
                res_hora = df_clean.groupby('FH', observed=False).agg({'Valor (R$)': 'sum', 'ID_Ref': 'count'}).rename(columns={'ID_Ref': 'Qtd', 'Valor (R$)': 'Lucro'})
                for f, row in res_hora.iterrows():
                    cor = "val-pos" if row['Lucro'] >= 0 else "val-neg"
                    st.markdown(f'''<div class="perf-card"><div style="flex:2"><b style="color:white">{f}</b></div><div style="text-align:right;"><span class="{cor}">{format_br(row['Lucro'])}</span></div></div>''', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Erro: {e}")
