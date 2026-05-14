from __future__ import annotations
from . import common

def render(ctx):
    common.st.markdown("## 🏢 RELATÓRIO URBANÍSTICO")
    common.st.markdown(
        """Este relatório mostra, de forma simples, se o uso residencial multifamiliar pode ou não ser desenvolvido neste terreno, com base na zona, na via e nas regras urbanísticas do município.

A ideia aqui é facilitar a leitura: primeiro explicamos o tipo multifamiliar analisado, depois apresentamos a localização do terreno, verificamos se o uso é viável e, em seguida, apresentamos os principais limites urbanísticos e pontos importantes para iniciar o estudo do projeto.

**Importante:** este relatório é uma análise inicial. A aprovação final depende da conferência completa no licenciamento municipal."""
    )
    common._render_intro_tipo(ctx["multi_tipo"], ctx["use_type_code"])
