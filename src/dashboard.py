import pandas as pd
from sqlalchemy import create_engine
import streamlit as st
import plotly.express as px

# --- Configuração da página ---
st.set_page_config(page_title="Dashboard IoT de Temperatura", layout="wide")
st.title("🌡️ Dashboard de Temperaturas IoT")

# --- Conexão com PostgreSQL ---
@st.cache_resource
def get_database_connection():
    engine = create_engine(
        'postgresql://postgres:senha123@localhost:5432/iotdb',
        pool_pre_ping=True,
        pool_recycle=300
    )
    return engine

engine = get_database_connection()

# --- Função para carregar dados ---
def load_data(query):
    try:
        return pd.read_sql(query, engine)
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return pd.DataFrame()

st.divider()

# --- Gráfico 1: TOP 20 Dispositivos por Temperatura Média ---
st.header("📊 TOP 20 Temperatura Média por Dispositivo")

df_avg_temp = load_data("SELECT * FROM avg_temp_por_dispositivo LIMIT 20")

if not df_avg_temp.empty:
    fig1 = px.bar(
        df_avg_temp,
        x="device_id",
        y="avg_temp",
        color="avg_temp",
        color_continuous_scale="RdYlBu_r",
        labels={"device_id": "ID do Dispositivo", "avg_temp": "Temperatura Média (°C)"},
        height=400
    )
    fig1.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig1, use_container_width=True)

st.divider()

# --- Gráfico 2: Distribuição por Hora ---
st.header("⏰ Distribuição de Leituras por Hora do Dia")

df_por_hora = load_data("SELECT * FROM leituras_por_hora ORDER BY hora")

if not df_por_hora.empty:
    fig2 = px.line(
        df_por_hora,
        x="hora",
        y="contagem",
        markers=True,
        labels={"hora": "Hora do Dia (0-23)", "contagem": "Quantidade de Leituras"},
        height=400
    )
    fig2.update_traces(line=dict(width=3), marker=dict(size=8))
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- Gráfico 3: Temperaturas Máximas e Mínimas por Dia ---
st.header("📈 Evolução das Temperaturas - Últimos 30 Dias")

df_extremas = load_data(
    """SELECT * FROM temp_max_min_por_dia 
       ORDER BY data DESC 
       LIMIT 30"""
)

if not df_extremas.empty:
    df_extremas = df_extremas.sort_values('data')
    
    fig3 = px.line(
        df_extremas,
        x="data",
        y=["temp_max", "temp_min"],
        markers=True,
        labels={"data": "Data", "value": "Temperatura (°C)", "variable": "Tipo"},
        height=400
    )
    fig3.for_each_trace(lambda t: t.update(
        line=dict(width=3),
        marker=dict(size=6),
        name="🔥 Máxima" if "temp_max" in t.name else "❄️ Mínima"
    ))
    st.plotly_chart(fig3, use_container_width=True)
