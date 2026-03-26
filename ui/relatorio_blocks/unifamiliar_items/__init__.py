from __future__ import annotations

from .common import fmt_num, fmt_pct, md_table
from . import (
    item_01_localizacao,
    item_02_adequabilidade,
    item_03_leitura_adequabilidade,
    item_04_zona,
    item_05_regras_principais,
    item_06_ocupacao_terreo,
    item_07_permeabilidade,
    item_08_tipos_piso,
    item_09_ia_altura,
    item_10_vagas,
    item_11_quadro_tecnico,
    item_12_calcada,
    item_13_dicas,
    item_14_resumo,
    item_15_pos_etapa,
    item_16_fechamento,
)


def render_unifamiliar_items(ctx: dict) -> None:
    item_01_localizacao.render(ctx)
    item_02_adequabilidade.render(ctx)
    item_03_leitura_adequabilidade.render(ctx)
    item_04_zona.render(ctx)
    item_05_regras_principais.render(ctx)
    item_06_ocupacao_terreo.render(ctx)
    item_07_permeabilidade.render(ctx)
    item_08_tipos_piso.render(ctx)
    item_09_ia_altura.render(ctx)
    item_10_vagas.render(ctx)
    item_11_quadro_tecnico.render(ctx)
    item_12_calcada.render(ctx)
    item_13_dicas.render(ctx)
    item_14_resumo.render(ctx)
    item_15_pos_etapa.render(ctx)
    item_16_fechamento.render(ctx)
