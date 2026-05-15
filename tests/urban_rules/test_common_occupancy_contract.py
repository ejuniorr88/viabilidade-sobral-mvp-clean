from urban_rules.common import choose_regular_occupancy


def test_recuos_menores_que_to_viram_limite_real():
    decision = choose_regular_occupancy(area_to=216, area_recuos=198)

    assert decision.area_adotada == 198
    assert decision.recuos_mais_restritivos is True
    assert decision.to_mais_restritiva is False


def test_area_pretendida_dentro_da_to_mas_acima_dos_recuos_e_ajustada():
    decision = choose_regular_occupancy(area_to=180, area_recuos=154, area_pretendida=170)

    assert decision.area_adotada == 154
    assert decision.area_pretendida_acima_to is False
    assert decision.area_pretendida_acima_recuos is True


def test_area_pretendida_valida_eh_adotada_quando_cabe_em_to_e_recuos():
    decision = choose_regular_occupancy(area_to=216, area_recuos=198, area_pretendida=170)

    assert decision.area_adotada == 170
    assert decision.area_pretendida_acima_to is False
    assert decision.area_pretendida_acima_recuos is False
