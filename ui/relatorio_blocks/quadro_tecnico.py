from __future__ import annotations

from typing import Dict, List

import pandas as pd
import streamlit as st


def render_quadro_tecnico() -> None:
    # IMPORTANT: Do not render the table as an indented markdown block.
    # Streamlit can interpret it as code and show raw pipes.
    # Using st.table keeps a clean, stable layout (like the previous version).
    st.markdown("---\n### 🧾 QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES\n(Lei Complementar nº 90/2023 – Anexo II)")

    rows: List[Dict[str, str]] = [
        {"AMBIENTE": "Sala de estar", "CÍRCULO INSCRITO": "2,00 m", "ÁREA MÍNIMA": "8,00 m²", "ILUMINAÇÃO": "1/8", "VENTILAÇÃO": "1/12", "PÉ-DIREITO": "2,50 m", "OBS.": "7"},
        {"AMBIENTE": "Sala de jantar", "CÍRCULO INSCRITO": "2,00 m", "ÁREA MÍNIMA": "6,00 m²", "ILUMINAÇÃO": "1/8", "VENTILAÇÃO": "1/12", "PÉ-DIREITO": "2,50 m", "OBS.": "7"},
        {"AMBIENTE": "Cozinha", "CÍRCULO INSCRITO": "1,80 m", "ÁREA MÍNIMA": "5,00 m²", "ILUMINAÇÃO": "1/8", "VENTILAÇÃO": "1/12", "PÉ-DIREITO": "2,50 m", "OBS.": "1-7"},
        {"AMBIENTE": "1º e 2º quartos", "CÍRCULO INSCRITO": "2,00 m", "ÁREA MÍNIMA": "8,00 m²", "ILUMINAÇÃO": "1/8", "VENTILAÇÃO": "1/12", "PÉ-DIREITO": "2,50 m", "OBS.": "–"},
        {"AMBIENTE": "Demais quartos", "CÍRCULO INSCRITO": "2,00 m", "ÁREA MÍNIMA": "5,00 m²", "ILUMINAÇÃO": "1/8", "VENTILAÇÃO": "1/12", "PÉ-DIREITO": "2,50 m", "OBS.": "–"},
        {"AMBIENTE": "Banheiro", "CÍRCULO INSCRITO": "1,00 m", "ÁREA MÍNIMA": "1,50 m²", "ILUMINAÇÃO": "1/10", "VENTILAÇÃO": "1/16", "PÉ-DIREITO": "2,20 m", "OBS.": "1-2-3"},
        {"AMBIENTE": "Área de serviço", "CÍRCULO INSCRITO": "1,20 m", "ÁREA MÍNIMA": "1,80 m²", "ILUMINAÇÃO": "1/10", "VENTILAÇÃO": "1/16", "PÉ-DIREITO": "2,20 m", "OBS.": "1-2-7"},
        {"AMBIENTE": "Garagem", "CÍRCULO INSCRITO": "2,20 m", "ÁREA MÍNIMA": "9,00 m²", "ILUMINAÇÃO": "1/14", "VENTILAÇÃO": "1/24", "PÉ-DIREITO": "2,20 m", "OBS.": "7"},
        {"AMBIENTE": "Escada", "CÍRCULO INSCRITO": "0,80 m", "ÁREA MÍNIMA": "–", "ILUMINAÇÃO": "–", "VENTILAÇÃO": "–", "PÉ-DIREITO": "2,10 m", "OBS.": "8-11-12-13"},
    ]

    df = pd.DataFrame(rows)
    st.table(df)
    st.markdown(
        """**Observações aplicáveis (Anexo II – LC 90/2023)**
    
    - Tolera-se iluminação e ventilação zenital.  
    - Admite-se ventilação mecânica ou indireta nos casos permitidos.  
    - Banheiro não pode comunicar-se diretamente com cozinha ou sala de jantar.  
    - Corredores com mais de 5,00m devem ter largura mínima de 1,00m.  
    - Corredores com mais de 10,00m exigem ventilação mínima proporcional.  
    - Área de porta com veneziana pode ser computada como ventilação.  
    - Escadas devem ser de material incombustível ou tratado.  
    - Patamar obrigatório quando houver mudança de direção ou altura superior a 2,90m.  
    - Largura mínima do degrau: 0,25m.  
    - Altura máxima do degrau: 0,19m.  
    """
    )

