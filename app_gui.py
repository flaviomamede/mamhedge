import streamlit as st
import sys
import os
from pathlib import Path
import pandas as pd
from datetime import datetime

# Add src to path
current_dir = Path(__file__).parent
src_path = current_dir / 'src'
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

try:
    from src.data.parsers.trava_parser import TravaParser, TravaOperation
    from src.data.parsers.everhedge_parser import EverHedgeParser, TERFOperation
    from src.analysis.esperanca_estatistica import calcular_alocacao_travas, AlocacaoTrava
except ImportError as e:
    st.error(f"Erro ao importar módulos do projeto: {e}")
    st.stop()

# Page Config
st.set_page_config(
    page_title="MamHedge",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS to mimic a dark, financial app (EverHedge-like vibe)
st.markdown("""
    <style>
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    .stSidebar {
        background-color: #262730;
    }
    h1, h2, h3 {
        color: #00ff7f !important; /* SpringGreen or similar 'growth' color */
        font-family: 'Roboto', sans-serif;
    }
    .stMetricValue {
        color: #00ff7f !important;
    }
    /* Custom Card Style */
    .css-card {
        background-color: #1e1e1e;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #333;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.title("MamHedge 🚀")
    st.markdown("---")
    menu_option = st.radio(
        "Navegação",
        ["Dashboard", "Radar de Oportunidades", "Análise Bayesiana", "Configurações"]
    )
    st.markdown("---")
    st.info("Status: Conta Simulada (Ambiente de Teste)")

# Main Content
if menu_option == "Dashboard":
    st.title("Visão Geral da Carteira")
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Capital Disponível", "R$ 500.000,00", "0%")
    with col2:
        st.metric("Em Renda Fixa", "R$ 375.000,00", "75%")
    with col3:
        st.metric("Alocado em Opções", "R$ 125.000,00", "25%")
    with col4:
        st.metric("Resultado Mensal", "R$ 5.500,00", "+1.1%")

    st.markdown("### 📢 Alertas de Radar")
    st.warning("⚠️ PETR4: Divergência entre Consenso (Queda) e Robô (Alta). Recomendação: Conta Simulada.")
    st.success("✅ ITUB4: Consenso e Robô alinhados. Recomendação: Conta Real.")

elif menu_option == "Radar de Oportunidades":
    st.title("📡 Radar de Oportunidades")
    st.markdown("Cole abaixo os dados do Robô EverHedge para análise:")
    
    input_text = st.text_area("Input de Dados (Texto Bruto)", height=200, placeholder="Cole aqui o texto do relatório...")
    
    if st.button("Processar Dados"):
        if input_text:
            try:
                # Travas
                trava_parser = TravaParser()
                travas = trava_parser.parse_all_operations(input_text)
                
                # TERFs
                terf_parser = EverHedgeParser()
                terfs = terf_parser.parse_all_operations(input_text)
                
                st.markdown(f"**Encontradas:** {len(travas)} Travas | {len(terfs)} TERFs")
                
                if travas:
                    st.markdown("### 🏹 Travas Identificadas")
                    data_travas = []
                    for t in travas:
                        data_travas.append({
                            "Ativo": t.acao,
                            "Tipo": f"Trava de {t.tipo_trava}",
                            "Strike Comp": t.strike_comprada,
                            "Strike Vend": t.strike_vendida,
                            "Payoff (%)": t.payoff,
                            "Custo": t.custo_total,
                            "Distância (%)": t.distancia_ativo
                        })
                    df_travas = pd.DataFrame(data_travas)
                    st.dataframe(df_travas, use_container_width=True)
                    
                    # Alocação for Travas
                    st.markdown("#### 💰 Sugestão de Alocação (Travas)")
                    capital_input = st.number_input("Capital para Riscos (R$)", value=25000.00, step=1000.00)
                    
                    if st.button("Calcular Alocação"):
                         alocacoes = calcular_alocacao_travas(travas, capital_total=capital_input)
                         
                         data_aloc = []
                         for a in alocacoes:
                             if a.alocacao_valor > 0:
                                 data_aloc.append({
                                     "Ativo": a.trava.acao,
                                     "Prob. Estimada": f"{a.probabilidade_estimada:.1f}%",
                                     "EV": f"{a.esperanca_estatistica:.2f}",
                                     "Alocação (R$)": f"R$ {a.alocacao_valor:,.2f}",
                                     "Alocação (%)": f"{a.alocacao_pct:.1f}%"
                                 })
                         
                         if data_aloc:
                             st.dataframe(pd.DataFrame(data_aloc), use_container_width=True)
                         else:
                             st.warning("Nenhuma alocação sugerida com os parâmetros atuais (EV negativo).")

                if terfs:
                    st.markdown("### 🛡️ TERFs Identificadas")
                    data_terfs = []
                    for t in terfs:
                        data_terfs.append({
                            "Ativo": t.acao,
                            "Rating": t.rating,
                            "Coeficiente": t.coeficiente,
                            "Rent. Miolo": f"{t.rentabilidade_miolo:.2f}%",
                            "CDI Período": f"{t.cdi_periodo:.2f}%",
                            "Venc. Put": t.vencimento_put.strftime('%d/%m/%Y')
                        })
                    df_terfs = pd.DataFrame(data_terfs)
                    st.dataframe(df_terfs, use_container_width=True)
                
            except Exception as e:
                st.error(f"Erro ao processar dados: {e}")
        else:
            st.warning("Por favor, insira os dados primeiro.")

elif menu_option == "Análise Bayesiana":
    st.title("🎲 Laboratório Bayesiano")
    st.write("Calibração de probabilidades baseada no histórico.")
    
    col1, col2 = st.columns(2)
    with col1:
        st.slider("Probabilidade A Priori (Histórico)", 0, 100, 50)
    with col2:
        st.slider("Força da Evidência (Consenso)", 0, 100, 70)
    
    st.button("Calcular Probabilidade A Posteriori")

elif menu_option == "Configurações":
    st.title("⚙️ Configurações")
    st.text_input("Chave API (Opcional)")
    st.toggle("Modo Dark (Forçado)", value=True)
