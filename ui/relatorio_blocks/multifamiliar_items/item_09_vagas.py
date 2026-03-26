from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    md(
        "**A quantidade de vagas depende do tamanho da unidade habitacional.**\n\n"
        "Regras:\n"
        "- apartamento com menos de **90 m²** → **1 vaga por unidade**\n"
        "- apartamento com **90 m²** ou mais → **1,5 vaga por unidade**\n\n"
        "**Quando aparecer 1,5, o total final deve ser arredondado para cima.**\n\n"
        "**Informação importante:**\n"
        "- pode haver **redução de até 20% das vagas** se o imóvel estiver em raio de **250 m do VLT**;\n"
        "- **Art. 121, § 4º:** “Poderá ser utilizada até **30%** (trinta por cento) das vagas de estacionamento previstas para estacionamento de motocicletas.”\n\n"
        f"👉 **Na prática:** como o **{ctx['tipo_sigla']}** é multifamiliar, essa lógica de vagas entra no cálculo do estudo."
    )
