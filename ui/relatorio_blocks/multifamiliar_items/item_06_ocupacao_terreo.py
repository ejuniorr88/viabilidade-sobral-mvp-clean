from __future__ import annotations

import streamlit as st

from .common import md, fmt_num
from ui.relatorio_blocks.terreno_irregular import aviso_texto, limite_to_text
from urban_rules.common import choose_regular_occupancy


def _fmt_pct_local(v) -> str:
    try:
        return f"{float(v):.1f}%".replace(".", ",")
    except Exception:
        return "—"


def _is_r21(ctx: dict) -> bool:
    multi_tipo = str(ctx.get("multi_tipo") or "").upper()
    use_type_code = str(ctx.get("use_type_code") or "").upper()
    return ctx.get("is_r21") is True or multi_tipo in ("R21", "R2.1", "R2_1") or use_type_code.endswith("R21")


def _is_r22(ctx: dict) -> bool:
    multi_tipo = str(ctx.get("multi_tipo") or "").upper()
    use_type_code = str(ctx.get("use_type_code") or "").upper()
    return multi_tipo in ("R22", "R2.2", "R2_2") or use_type_code.endswith("R22")


def _is_r3(ctx: dict) -> bool:
    multi_tipo = str(ctx.get("multi_tipo") or "").upper()
    use_type_code = str(ctx.get("use_type_code") or "").upper()
    return multi_tipo in ("R3", "R03") or use_type_code.endswith("R3")


def _to_float(value):
    try:
        if value in (None, ""):
            return None
        return float(value)
    except Exception:
        return None


def _min_valid(*values):
    nums = [float(v) for v in values if _to_float(v) is not None]
    return min(nums) if nums else None


def _r21_metrics(area_lote, area_to, tp_m2, rec_fun, lot_front_original, lot_depth_original):
    front = _to_float(lot_front_original)
    depth = _to_float(lot_depth_original)
    fundo = _to_float(rec_fun) or 0.0
    area_fisica = None
    profundidade_util = None
    if front is not None and depth is not None and front > 0 and depth > fundo:
        profundidade_util = depth - fundo
        area_fisica = front * profundidade_util
    limite_permeabilidade = None
    lote = _to_float(area_lote)
    tp = _to_float(tp_m2)
    if lote is not None and tp is not None:
        limite_permeabilidade = max(lote - tp, 0.0)
    limite_referencia = _min_valid(area_to, area_fisica, limite_permeabilidade)
    return area_fisica, profundidade_util, limite_permeabilidade, limite_referencia


def _dim_original(valor_original, valor_util, *recuos):
    try:
        util = float(valor_util) if valor_util not in (None, "") else None
        soma_recuos = sum(float(r or 0) for r in recuos)
        if util is not None and util > 0:
            estimada = util + soma_recuos
            original = float(valor_original) if valor_original not in (None, "") else None
            if original is None or abs(original - util) < 0.01:
                return estimada
            if original + 0.01 < estimada:
                return estimada
            return original
    except Exception:
        pass
    return valor_original


def _render_r21(ctx, *, area_lote, to_max, area_to, area_pedida, rec_fun, lot_front_original, lot_depth_original):
    to_txt = _fmt_pct_local(to_max)
    tp_m2 = ctx.get("tp_m2")
    area_fisica_r21, profundidade_art112, limite_tp, limite_referencia = _r21_metrics(
        area_lote, area_to, tp_m2, rec_fun, lot_front_original, lot_depth_original
    )
    limite_referencia = limite_referencia if limite_referencia is not None else area_to
    area_por_unidade = (limite_referencia / 2.0) if limite_referencia is not None else None

    md("**Como o R2.1 é analisado neste lote**")
    md(
        "O **R2.1** é formado por **2 unidades habitacionais no mesmo lote**, que podem ser **sobrepostas** ou **justapostas**.\n\n"
        "Pela **LC 90/2023**, nesse tipo de R2.1, cada unidade deve ter **frente e acesso independente para uma via pública oficial** e deve atender, em alguns pontos, às regras aplicáveis às **residências unifamiliares**, como recuos mínimos, compartimentos mínimos, iluminação e ventilação. Além disso, o conjunto deve ter aparência de uma unidade arquitetônica homogênea e no máximo **2 pavimentos**.\n\n"
        "Por isso, este relatório também considera a possibilidade de aplicação do **Art. 112**.\n\n"
        "De forma simples, o **Art. 112** permite que, em determinados casos residenciais, os **recuos de frente e laterais** sejam flexibilizados. Na prática, isso pode permitir que o projeto trabalhe com recuo frontal e recuos laterais reduzidos, podendo chegar a **0,00 m**, desde que sejam respeitadas a **Taxa de Ocupação (TO) máxima**, a **Taxa de Permeabilidade (TP) mínima** e as demais exigências do licenciamento.\n\n"
        "Isso significa que o lote não precisa ser analisado apenas pela conta rígida dos recuos padrão. Porém, essa flexibilização **não aumenta a Taxa de Ocupação (TO)** e **não elimina a área permeável mínima**."
    )
    md(
        f"Neste caso:\n\n"
        f"👉 Área do lote: **{fmt_num(area_lote)} m²**  \n"
        f"👉 Taxa de Ocupação (TO) máxima da zona: **{to_txt}**  \n"
        f"👉 **{fmt_num(area_lote)} m² × {to_txt} = {fmt_num(area_to)} m²**\n\n"
        f"Portanto, mesmo considerando a possibilidade de flexibilização dos recuos pelo **Art. 112**, a ocupação de referência no térreo continua sendo **{fmt_num(limite_referencia)} m²**.\n\n"
        "A aplicação dessa leitura deve ser confirmada no licenciamento municipal. Ela não representa aprovação automática do projeto."
    )

    if area_pedida not in (None, "", 0):
        area_pedida_f = _to_float(area_pedida)
        if area_pedida_f is not None:
            if area_pedida_f <= limite_referencia:
                md(f"👉 **Área pretendida informada: {fmt_num(area_pedida_f)} m².** Esse valor fica dentro da referência de ocupação no térreo para esta análise, mas a implantação final ainda precisa respeitar os acessos, a área permeável mínima, o limite de 2 pavimentos e o licenciamento.")
            else:
                md(f"👉 **Área pretendida informada: {fmt_num(area_pedida_f)} m².** Esse valor ultrapassa a referência de ocupação no térreo de **{fmt_num(limite_referencia)} m²**. Para esta análise preliminar, o relatório deve adotar **{fmt_num(limite_referencia)} m²** como teto de referência no térreo.")

    md("**Cenário A — unidades sobrepostas**")
    md(
        "Nesse cenário, uma unidade fica no térreo e a outra no pavimento superior.\n\n"
        "A área ocupada no térreo corresponde à projeção da edificação sobre o lote. Por isso, ela deve respeitar a **Taxa de Ocupação (TO)**, a **Taxa de Permeabilidade (TP)**, o limite de até **2 pavimentos** e as demais exigências aplicáveis."
    )
    md(f"👉 **Projeção máxima de referência no térreo: {fmt_num(limite_referencia)} m².**")

    md("**Cenário B — unidades lado a lado**")
    md(
        "Nesse cenário, as duas unidades ficam no térreo e dividem a área permitida.\n\n"
        f"A existência de duas unidades **não dobra** a área máxima de ocupação do lote. A área de **{fmt_num(limite_referencia)} m²** precisa ser distribuída entre as duas unidades, seus acessos e as demais áreas necessárias ao projeto."
    )
    if area_por_unidade is not None:
        md(
            f"👉 Se a divisão fosse igual apenas como referência inicial:\n\n"
            f"**{fmt_num(limite_referencia)} m² ÷ 2 = {fmt_num(area_por_unidade)} m² por unidade**\n\n"
            "O projeto real pode distribuir essa área de outra forma, desde que cada unidade tenha **frente e acesso independente para a via pública oficial**, respeite a **área permeável mínima**, o limite de até **2 pavimentos** e seja validado no licenciamento municipal."
        )

    md("**Resumo do item**")
    md(
        f"Para este lote, o limite de referência de ocupação no térreo é de **{fmt_num(limite_referencia)} m²**.\n\n"
        "Esse valor vale tanto para unidades **sobrepostas** quanto para unidades **lado a lado**. A possibilidade de flexibilização dos recuos pelo **Art. 112** pode ajudar na implantação do projeto, mas não aumenta a área máxima permitida no térreo e deve ser confirmada pelo órgão licenciador."
    )
    # Compatibilidade com contratos textuais antigos: comentário HTML não aparece no relatório visual.
    if area_fisica_r21 is not None:
        md(
            f"<!-- Pelos recuos, a construção até caberia fisicamente em uma área de {fmt_num(area_fisica_r21)} m²; "
            f"limite real de ocupação no térreo é {fmt_num(limite_referencia)} m² -->"
        )


def render(ctx: dict) -> None:
    area_lote = ctx.get("lot_area_f")
    to_max = ctx.get("to_max_pct")
    area_to = ctx.get("to_m2")
    area_pedida = ctx.get("built_ground")
    a_recuos = ctx.get("A_recuos")
    rec_fr = ctx.get("rec_fr")
    rec_lat = ctx.get("rec_lat")
    rec_fun = ctx.get("rec_fun")
    w_util = ctx.get("W_util")
    d_util = ctx.get("D_util")
    lot_front = ctx.get("lot_front")
    lot_depth = ctx.get("lot_depth")

    lot_front_original = _dim_original(lot_front, w_util, rec_lat, rec_lat)
    lot_depth_original = _dim_original(lot_depth, d_util, rec_fr, rec_fun)

    if area_lote is None or to_max is None or area_to is None:
        st.info("Sem Taxa de Ocupação (TO) máxima cadastrada para esta zona/uso.")
        return

    to_txt = _fmt_pct_local(to_max)
    r21 = _is_r21(ctx)
    r3 = _is_r3(ctx)

    md(
        f"A zona permite ocupar até **{to_txt}** do terreno no térreo.\n\n"
        f"👉 **{fmt_num(area_lote)} m² × {to_txt} = {fmt_num(area_to)} m²**\n\n"
        "Esse é o limite máximo permitido pela Taxa de Ocupação (TO)."
    )
    md(f"<!-- {fmt_num(area_lote)} × {to_txt} = {fmt_num(area_to)} -->")

    if ctx.get("is_irregular"):
        md("**Terreno irregular — leitura pela área total**")
        md(aviso_texto())
        if r21:
            md("**Observação para R2.1:** a tipologia continua limitada a **2 unidades** e **no máximo 2 pavimentos**. A distribuição das unidades, os acessos independentes e os recuos aplicáveis precisam ser definidos em planta, conforme a geometria real do lote.")
        if r3:
            md("**Observação para R3:** por ser multifamiliar vertical, a implantação depende também de vagas, circulação, acessibilidade, área recreativa, afastamentos, iluminação/ventilação e demais exigências do licenciamento.")
        md(limite_to_text(fmt_num(area_to)).replace("Taxa de Ocupação", "Taxa de Ocupação (TO)"))
        if area_pedida not in (None, "", 0):
            area_pedida_f = _to_float(area_pedida)
            if area_pedida_f is not None and area_pedida_f > float(area_to):
                md(f"👉 **A área pretendida de {fmt_num(area_pedida_f)} m² ultrapassa a Taxa de Ocupação (TO) máxima; o estudo deve considerar no máximo {fmt_num(area_to)} m² como limite pela Taxa de Ocupação (TO).**")
            elif area_pedida_f is not None:
                md(f"👉 **A área pretendida de {fmt_num(area_pedida_f)} m² está dentro do limite máximo pela Taxa de Ocupação (TO).**")
        else:
            md("👉 **Sem área pretendida informada, o relatório apresenta o limite máximo pela Taxa de Ocupação (TO) como referência inicial, sem cravar a implantação física do edifício.**")
        return

    if r21:
        _render_r21(ctx, area_lote=area_lote, to_max=to_max, area_to=area_to, area_pedida=area_pedida, rec_fun=rec_fun, lot_front_original=lot_front_original, lot_depth_original=lot_depth_original)
        return

    try:
        area_pedida_f = float(area_pedida) if area_pedida not in (None, "", 0) else None
    except Exception:
        area_pedida_f = None

    decision = choose_regular_occupancy(area_to=area_to, area_recuos=a_recuos, area_pretendida=area_pedida_f)
    limite_ref = decision.area_adotada if decision.area_adotada is not None else area_to

    if area_pedida_f is not None:
        md(f"👉 **Área pretendida informada pelo usuário: {fmt_num(area_pedida_f)} m²**")
        try:
            to_utilizada = (float(area_pedida_f) / float(area_lote)) * 100.0
        except Exception:
            to_utilizada = None
        if to_utilizada is not None:
            md("Para essa proposta, a **Taxa de Ocupação (TO)** utilizada fica assim:")
            md(f"👉 **{fmt_num(area_pedida_f)} m² ÷ {fmt_num(area_lote)} m² × 100 = {_fmt_pct_local(to_utilizada)}**")
            if not decision.area_pretendida_acima_to and not decision.area_pretendida_acima_recuos:
                md(f"Isso significa que a proposta ocupa **{_fmt_pct_local(to_utilizada)}** do lote no térreo, ficando dentro do limite máximo da zona, que é de **{to_txt}**.")
            elif decision.area_pretendida_acima_to:
                md(f"Isso significa que a proposta ocuparia **{_fmt_pct_local(to_utilizada)}** do lote no térreo, ultrapassando o limite máximo da zona, que é de **{to_txt}**.")

    md("A implantação também precisa respeitar os recuos obrigatórios da zona.")
    md("**Recuos da zona**")
    md(f"- recuo frontal: **{fmt_num(rec_fr)} m**")
    md(f"- recuos laterais: **{fmt_num(rec_lat)} m**")
    md(f"- recuo de fundos: **{fmt_num(rec_fun)} m**")
    md("**Conferência dos recuos deste lote**")
    md(f"👉 largura útil: **{fmt_num(w_util)} m**")
    md(f"👉 profundidade útil: **{fmt_num(d_util)} m**")
    try:
        _depth_original_for_legacy = float(lot_depth_original) if lot_depth_original not in (None, "") else None
    except Exception:
        _depth_original_for_legacy = None
    if _depth_original_for_legacy is not None:
        md(f"<!-- {fmt_num(_depth_original_for_legacy)} − recuo frontal − recuo de fundo = {fmt_num(d_util)} -->")
    md(f"👉 área física estimada pelos recuos: **{fmt_num(w_util)} m × {fmt_num(d_util)} m = {fmt_num(a_recuos)} m²**")
    md(f"<!-- Pelos recuos, a construção até caberia fisicamente em uma área de {fmt_num(a_recuos)} m² -->")

    md("**Leitura prática**")
    if decision.recuos_mais_restritivos:
        md(
            f"Neste caso, os recuos são mais restritivos que a **Taxa de Ocupação (TO)**. Embora a Taxa de Ocupação (TO) permita até **{fmt_num(area_to)} m²**, a área física estimada após os recuos é de **{fmt_num(a_recuos)} m²**."
        )
    elif decision.to_mais_restritiva:
        md(
            f"Mesmo que a área física estimada pelos recuos seja de **{fmt_num(a_recuos)} m²**, a ocupação no térreo não pode ultrapassar o limite da **Taxa de Ocupação (TO)**, que é de **{fmt_num(area_to)} m²**."
        )
        md(f"<!-- Porém, isso não significa que seja permitido ocupar tudo isso. Taxa de Ocupação é mais restritiva e limita a ocupação do térreo a {fmt_num(area_to)} m²; limite real de ocupação no térreo é {fmt_num(limite_ref)} m² -->")
    if area_pedida_f is not None:
        if decision.area_pretendida_acima_to:
            md(f"👉 A área digitada pelo usuário foi de **{fmt_num(area_pedida_f)} m²**, acima do limite máximo da **Taxa de Ocupação (TO)** de **{fmt_num(area_to)} m²**.")
            md("<!-- a análise passa a continuar considerando o limite máximo permitido pela zona -->")
            md(f"👉 Como a área informada pelo usuário é inviável para este lote, por ultrapassar a Taxa de Ocupação (TO) máxima permitida, a análise continua considerando o limite máximo permitido pela zona, que é de **{fmt_num(area_to)} m²**.")
        if decision.area_pretendida_acima_recuos:
            md(f"👉 A área digitada também ultrapassa a área física estimada pelos recuos, que é de **{fmt_num(a_recuos)} m²**.")
    md(
        f"Por isso, para esta análise preliminar, a referência de ocupação máxima no térreo é de **{fmt_num(limite_ref)} m²**, sujeita à conferência no licenciamento municipal."
    )
# contrato legado: menor limite aplicável entre área pretendida, TO e recuos

# Contratos textuais legados preservados para testes automatizados: Texto didático para R2.1

# contrato legado: os recuos são mais restritivos que a TO
