from __future__ import annotations
from . import common

def render(ctx):
    if ctx["tp_min_pct"] is None or ctx["tp_m2"] is None:
        common.st.info("Ainda não foi possível calcular a Taxa de Permeabilidade com base na regra carregada.")
        return

    lot_area = ctx["lot_area_f"]
    tp_pct = ctx["tp_min_pct"]
    tp_m2 = ctx["tp_m2"]
    area_recuos = ctx.get("A_recuos")
    area_to = ctx.get("to_m2")

    common.st.markdown(f"A zona exige **{common._fmt_pct(tp_pct)}** de área permeável.")
    common._formula_box(f"{common._fmt_num(lot_area)} × {common._fmt_pct(tp_pct)} = {common._fmt_num(tp_m2)} obrigatórios permeáveis")
    common.st.markdown("Isso quer dizer que parte do terreno precisa continuar permitindo a infiltração da água da chuva no solo.")

    if area_to is not None:
        area_restante_to = lot_area - area_to if lot_area is not None else None
        area_impermeavel_to = area_restante_to - tp_m2 if (area_restante_to is not None and tp_m2 is not None) else None

        common.st.markdown("**Cenário 1 — usando o máximo da TO**")
        common.st.markdown(f"Se você utilizar **{common._fmt_num(area_to)}** no térreo:")
        common.st.markdown(
            f"👉 **Área restante no lote: {common._fmt_num(lot_area)} − {common._fmt_num(area_to)} = {common._fmt_num(area_restante_to)}**"
        )
        common.st.markdown("Desses:")
        common.st.markdown(f"- **{common._fmt_num(tp_m2)}** devem permitir infiltração no solo")
        if area_impermeavel_to is not None:
            common.st.markdown(f"- **{common._fmt_num(area_impermeavel_to)}** podem receber piso impermeável")

    if area_recuos is not None:
        area_restante_recuos = lot_area - area_recuos if lot_area is not None else None
        area_impermeavel_recuos = area_restante_recuos - tp_m2 if (area_restante_recuos is not None and tp_m2 is not None) else None

        common.st.markdown("**Cenário 2 — usando a implantação pelos recuos da zona**")
        common.st.markdown(f"Se você utilizar **{common._fmt_num(area_recuos)}** no térreo:")
        common.st.markdown(
            f"👉 **Área restante no lote: {common._fmt_num(lot_area)} − {common._fmt_num(area_recuos)} = {common._fmt_num(area_restante_recuos)}**"
        )
        common.st.markdown("Desses:")
        common.st.markdown(f"- **{common._fmt_num(tp_m2)}** devem permitir infiltração no solo")
        if area_impermeavel_recuos is not None:
            common.st.markdown(f"- **{common._fmt_num(area_impermeavel_recuos)}** podem receber piso impermeável")

    common.st.markdown(
        "👉 **Leitura prática:** no multifamiliar, quando a implantação aumenta, a área livre diminui. "
        "Por isso, quanto maior a ocupação do térreo, menor fica a sobra disponível além do mínimo exigido para a permeabilidade."
    )
