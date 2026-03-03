
import streamlit as st
from pathlib import Path
import json

# =============================
# CONFIGURAÇÃO DE CAMINHOS (CORREÇÃO DEFINITIVA FILE PATH)
# =============================

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"

ZONE_FILE = DATA_DIR / "zoneamento_light.json"
STREETS_FILE = DATA_DIR / "ruas.json"

# =============================
# FUNÇÕES DE CARREGAMENTO
# =============================

@st.cache_data
def load_zones():
    with open(ZONE_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

@st.cache_data
def load_streets():
    with open(STREETS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

# =============================
# APP
# =============================

st.title("Viabilidade")

try:
    zones = load_zones()
    streets = load_streets()

    st.success("Arquivos carregados com sucesso.")
    st.write("Total de zonas:", len(zones))
    st.write("Total de ruas:", len(streets))

except FileNotFoundError as e:
    st.error("Arquivo não encontrado:")
    st.exception(e)
