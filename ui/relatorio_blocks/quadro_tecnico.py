from __future__ import annotations

from typing import Dict, List

import pandas as pd
import streamlit as st


def render_quadro_tecnico() -> None:
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

    st.markdown("**Observações:**")
    observacoes = [
        "1. Tolerada a iluminação e ventilação zenital.",
        "2. Poderão utilizar ventilação mecânica ou serem ventilados e iluminados indiretamente através de outros banheiros, circulações, depósitos ou áreas de serviços.",
        "3. Não poderão comunicar-se diretamente com a cozinha e sala de jantar.",
        "4. As condições de iluminação e ventilação naturais poderão ser substituídas por meios artificiais.",
        "5. Para corredores com mais de 5,00m de comprimento, a largura mínima é de 1,00m.",
        "6. Para corredores com mais de 10,00m de comprimento é obrigatória a ventilação na relação de 1/20 da área do piso.",
        "7. Poderá ser computada como área de ventilação a área da porta com venezianas.",
        "8. Deverá ser material incombustível ou tratada para tal.",
        "9. Serão permitidas escadas em curva, desde que a curvatura interna tenha um raio mínimo de 2,00m e os degraus tenham largura mínima de 0,28m, medida na linha do piso, desenvolvida à distância de 1,00m da linha de curvatura externa.",
        "10. As exigências da observação 9 ficam dispensadas para escadas tipo marinheiro e caracol, admitidas para acesso a torres, jiraus, adegas, ateliêrs, escritórios e outros casos especiais.",
        "11. Serão obrigatórios os patamares intermediários sempre que houver mudança de direção ou quando o lance da escada precisar vencer altura superior a 2,90m; o comprimento do patamar não será inferior a largura da escada.",
        "12. A largura mínima do degrau será de 0,25m.",
        "13. A altura máxima do degrau será de 0,19m.",
        "14. O piso deve ser antiderrapante.",
        "15. A inclinação máxima será de 10%.",
        "16. Consideram-se corredores principais os que dão acesso às unidades habitacionais em residências multifamiliares.",
        "17. Quando a área for superior a 10,00m², deverão ser ventilados na relação de 1/24 da área do piso.",
        "18. Quando o comprimento for superior a 10,00m, deverá ser alargado de 0,10m por metro, ou fração, do comprimento excedente a 10,00m.",
        "19. Quando não houver ligação direta com o exterior, será tolerada ventilação por meio de chaminés de ventilação ou pela caixa de escada, nos casos que precisar.",
        "20. Deverá haver ligação direta entre o “hall” e a caixa de escada.",
        "21. Tolerada ventilação pela caixa de escada.",
        "22. A área mínima de 6,00m² é exigida quando houver um só elevador. Quando houver mais de um elevador, a área deverá ser aumentada de 30% para o elevador excedente.",
        "23. A área mínima de 12,00m², exigida quando houver um só elevador, deverá ser aumentada de 30% por elevador excedente.",
        "24. Será tolerado um diâmetro de 2,50m, quando os elevadores se situarem no mesmo lado do “hall”.",
        "25. Consideram-se corredores principais os de uso comum do edifício.",
        "26. Quando a área for superior a 20,00m², deverão ser ventilados na relação de 1/20 da área do piso.",
        "27. A abertura de ventilação deverá se situar, no máximo, a 10,00m de qualquer ponto do corredor.",
        "28. Consideram-se corredores secundários os de uso exclusivo da administração do edifício ou destinado a serviço.",
    ]
    for item in observacoes:
        st.markdown(item)

    st.markdown("**Observações gerais:**")
    gerais = [
        "a) Para o uso residencial o revestimento impermeável das paredes será, no mínimo, até 1,50m na cozinha, banheiro e lavanderia.",
        "b) Para os edifícios de habitação multifamiliar ou coletiva e comerciais, o revestimento impermeável das paredes será, no mínimo, até 1,50m nas escadas e sanitários.",
        "c) Para os edifícios de habitação multifamiliar ou coletiva e comerciais, o revestimento impermeável do piso será no hall do prédio, hall dos pavimentos, corredores principais e secundários, escadas, rampas e sanitários.",
        "d) As edificações construídas com estruturas de conteineres devem observar a legislação vigente e apresentar um pé direito mínimo de 2,40m (dois metros e quarenta centímetros).",
        "e) Para todos os usos, as colunas “iluminação mínima” e “ventilação mínima” deste Anexo referem-se à relação entre a área da abertura e a área do piso.",
    ]
    for item in gerais:
        st.markdown(item)
