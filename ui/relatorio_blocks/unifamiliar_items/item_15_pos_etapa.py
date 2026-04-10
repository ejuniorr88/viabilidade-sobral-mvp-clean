from __future__ import annotations

from .common import md


def render(ctx: dict) -> None:
    md(
        "Após a finalização dos projetos, será necessário dar entrada na documentação junto à **Prefeitura** para obter o **alvará de construção**.\n\n"
        "De forma geral, esse processo pode seguir por **duas vias**:\n\n"
        "- **Alvará de Construção Simplificado** → voltado para casos mais simples e de menor porte;\n"
        "- **Alvará de Construção (Obra Nova)** → usado quando a obra exige análise técnica mais completa e documentação complementar.\n\n"
        "Abaixo, apresentamos um resumo dos dois caminhos e um checklist básico dos itens que normalmente precisam ser providenciados."
    )

    md("#### 📄 Alvará de Construção Simplificado")
    md(
        "O **Alvará de Construção Simplificado** é uma forma mais rápida de licenciamento, voltada para casos mais simples. "
        "Ele costuma ser usado para **residência unifamiliar** e para **comércio/serviços de pequeno porte**, com área construída de até **250,00 m²**.\n\n"
        "A lógica desse alvará é mais enxuta e autodeclaratória, mas isso não elimina a necessidade de apresentar os documentos corretos "
        "e atender às exigências urbanísticas e técnicas do Município."
    )
    md("**✅ Checklist — documentos e itens principais**")
    for line in [
        "[ ] Documento de identidade do requerente ou representante legal",
        "[ ] CPF ou CNPJ",
        "[ ] Matrícula atualizada do imóvel ou documento equivalente",
        "[ ] Certidão negativa de IPTU",
        "[ ] Parecer favorável de Adequabilidade Locacional",
        "[ ] Tabela com índices urbanísticos e áreas da edificação",
        "[ ] Projeto arquitetônico em arquivo digital",
        "[ ] ART/RRT do responsável técnico",
        "[ ] Termo de responsabilidade do responsável técnico",
        "[ ] Termo de responsabilidade do proprietário",
        "[ ] Isenção da licença ambiental",
    ]:
        md(line)

    md("**📌 Atenção**")
    for line in [
        "[ ] Confirmar se o caso realmente se enquadra como simplificado",
        "[ ] Conferir se a área construída está dentro do limite permitido",
        "[ ] Protocolar o pedido com antecedência mínima indicada pelo procedimento",
        "[ ] Verificar se todos os arquivos digitais estão prontos e legíveis",
    ]:
        md(line)

    md("#### 🏗️ Alvará de Construção (Obra Nova)")
    md(
        "O **Alvará de Construção (Obra Nova)** é o caminho regular de licenciamento para obras novas que exigem análise técnica completa da Prefeitura. "
        "Ele é mais detalhado e costuma ser necessário em casos que não se enquadram no procedimento simplificado ou que exigem documentação complementar.\n\n"
        "Esse tipo de alvará pede uma conferência mais ampla do projeto, incluindo aspectos urbanísticos, arquitetônicos, hidrossanitários, ambientais e, em alguns casos, exigências de outros órgãos."
    )
    md("**✅ Checklist — documentos principais**")
    for line in [
        "[ ] Requerimento único",
        "[ ] Documento de identidade do requerente ou representante legal",
        "[ ] CPF ou CNPJ",
        "[ ] Matrícula atualizada do imóvel",
        "[ ] Autorização do proprietário, quando necessária",
        "[ ] BCI",
        "[ ] ART/RRT com comprovante de pagamento",
        "[ ] Projeto arquitetônico assinado",
        "[ ] Projeto hidrossanitário",
        "[ ] Memorial de cálculo e drenagem pluvial",
        "[ ] Declaração do SAAE sobre rede de esgoto, quando necessária",
    ]:
        md(line)

    md("**✅ Checklist — documentos adicionais que podem ser exigidos**")
    for line in [
        "[ ] Aprovação do Corpo de Bombeiros",
        "[ ] Aprovação do IPHAN, quando o imóvel estiver em ZEIP",
        "[ ] Licenciamento ambiental ou termo de isenção",
        "[ ] PGRSCC",
        "[ ] Autorização do COMAR, quando aplicável",
        "[ ] Aprovação do DNIT ou SOP, quando houver acesso por rodovia",
        "[ ] EIV, quando exigido pela legislação",
    ]:
        md(line)

    md("**📌 Atenção**")
    for line in [
        "[ ] Confirmar se o caso realmente exige alvará regular de obra nova",
        "[ ] Conferir se há exigência de documentos complementares por localização ou tipologia",
        "[ ] Verificar se o imóvel está em área com proteção especial",
        "[ ] Conferir se o projeto atende às exigências técnicas antes do protocolo",
    ]:
        md(line)
