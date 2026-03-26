from __future__ import annotations
from . import common

def render(ctx):
    common.st.markdown(
        f"**A quantidade de vagas depende do tamanho da unidade habitacional.**\n\nRegras:\n- apartamento com menos de **90 m²** → **1 vaga por unidade**\n- apartamento com **90 m²** ou mais → **1,5 vaga por unidade**\n\n**Quando aparecer 1,5, o total final deve ser arredondado para cima.**\n\n**Informação importante:**\n- pode haver **redução de até 20% das vagas** se o imóvel estiver em raio de **250 m do VLT**;\n- **Art. 121, § 4º:** “Poderá ser utilizada até **30%** (trinta por cento) das vagas de estacionamento previstas para estacionamento de motocicletas.”\n\n👉 **Na prática:** como o **{common._tipo_multifamiliar_label(ctx['multi_tipo'], ctx['use_type_code']).split(' — ')[0]}** é multifamiliar, essa lógica de vagas entra no cálculo do estudo."
    )
