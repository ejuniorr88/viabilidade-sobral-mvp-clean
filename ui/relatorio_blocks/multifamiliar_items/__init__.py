from __future__ import annotations

from .item_01_localizacao import render as render_item_01
from .item_02_adequabilidade import render as render_item_02
from .item_03_leitura_adequabilidade import render as render_item_03
from .item_04_zona import render as render_item_04
from .item_05_regras_principais import render as render_item_05
from .item_06_ocupacao_terreo import render as render_item_06
from .item_07_permeabilidade import render as render_item_07
from .item_08_ia_altura import render as render_item_08
from .item_09_vagas import render as render_item_09
from .item_10_quadro_tecnico import render as render_item_10
from .item_11_calcada import render as render_item_11
from .item_12_dicas import render as render_item_12
from .item_13_resumo import render as render_item_13
from .item_14_pos_etapa import render as render_item_14
from .item_15_fechamento import render as render_item_15

MULTIFAMILIAR_ITEM_RENDERERS = {
    "item_01": render_item_01,
    "item_02": render_item_02,
    "item_03": render_item_03,
    "item_04": render_item_04,
    "item_05": render_item_05,
    "item_06": render_item_06,
    "item_07": render_item_07,
    "item_08": render_item_08,
    "item_09": render_item_09,
    "item_10": render_item_10,
    "item_11": render_item_11,
    "item_12": render_item_12,
    "item_13": render_item_13,
    "item_14": render_item_14,
    "item_15": render_item_15,
}

__all__ = ["MULTIFAMILIAR_ITEM_RENDERERS"]
