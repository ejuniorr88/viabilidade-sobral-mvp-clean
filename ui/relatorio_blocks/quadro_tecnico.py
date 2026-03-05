from __future__ import annotations

import streamlit as st


def render_quadro_tecnico() -> None:
    st.markdown("---\n### 🧾 QUADRO TÉCNICO – PARÂMETROS DOS AMBIENTES\n(Lei Complementar nº 90/2023 – Anexo II)")
    st.markdown(
        """| AMBIENTE | CÍRCULO INSCRITO | ÁREA MÍNIMA | ILUMINAÇÃO | VENTILAÇÃO | PÉ-DIREITO | OBS. |
    |---|---:|---:|---:|---:|---:|---|
    | Sala de estar | 2,00 m | 8,00 m² | 1/8 | 1/12 | 2,50 m | 7 |
    | Sala de jantar | 2,00 m | 6,00 m² | 1/8 | 1/12 | 2,50 m | 7 |
    | Cozinha | 1,80 m | 5,00 m² | 1/8 | 1/12 | 2,50 m | 1-7 |
    | 1º e 2º quartos | 2,00 m | 8,00 m² | 1/8 | 1/12 | 2,50 m | – |
    | Demais quartos | 2,00 m | 5,00 m² | 1/8 | 1/12 | 2,50 m | – |
    | Banheiro | 1,00 m | 1,50 m² | 1/10 | 1/16 | 2,20 m | 1-2-3 |
    | Área de serviço | 1,20 m | 1,80 m² | 1/10 | 1/16 | 2,20 m | 1-2-7 |
    | Garagem | 2,20 m | 9,00 m² | 1/14 | 1/24 | 2,20 m | 7 |
    | Escada | 0,80 m | – | – | – | 2,10 m | 8-11-12-13 |
    """
    )
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

