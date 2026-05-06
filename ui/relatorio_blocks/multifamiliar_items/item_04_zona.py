from __future__ import annotations
from . import common


def render(ctx):
    common.st.markdown("Todo terreno está inserido em uma zona, e cada zona pode ter regras, restrições e critérios próprios de uso e ocupação. Quando o terreno está localizado em área urbana com zoneamento definido, podem existir regras, restrições e critérios próprios de uso e ocupação. Nas áreas urbanas, essas informações normalmente ajudam a definir o que pode ser construído, quanto pode ocupar no térreo, quanto precisa ficar livre e o porte da edificação. Já em áreas rurais ou em zonas com tratamento especial, nem sempre existem parâmetros urbanísticos numéricos definidos da mesma forma. Nesses casos, a análise ficará restrita aos critérios aplicáveis do Código de Ordenamento Urbano e às demais regras específicas que incidirem sobre a área.")
    zona = ctx.get('zone_title') or ctx.get('zone')
    desc = ctx.get('desc')
    if desc and desc.get('description_text'):
        common.st.markdown(f"**{zona}**")
        common.st.markdown(str(desc.get('description_text')))
    else:
        common.st.markdown(f"- **Zona:** {zona or '—'}\n- **Via do terreno:** {ctx.get('via')}\n- **Tipo de via:** {ctx.get('via_tipo_txt')}")
    if common.is_zeip(ctx): common.st.warning(common.zeip_alert_text())
    if common.is_zeip9(ctx): common.st.warning(common.zeip9_alert_text())
    common.st.markdown("**É essa leitura da zona que ajuda a entender o que pode ser implantado no lote e com qual porte.**")
