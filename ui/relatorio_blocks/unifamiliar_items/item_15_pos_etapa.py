from __future__ import annotations

import streamlit as _st


def render(ctx: dict) -> None:
    st = ctx.get("st", _st)
    st.markdown("---\n### 🏛️ 1️⃣4️⃣ O que acontece depois desta etapa?")
    st.markdown(
        "Após a finalização dos projetos, será necessário dar entrada na documentação junto à **Prefeitura** para obter o **alvará de construção**.\n\n"
        "De forma geral, esse processo pode seguir por **duas vias**:\n\n"
        "- **Alvará de Construção Simplificado** → voltado para casos mais simples e de menor porte;\n"
        "- **Alvará de Construção (Obra Nova)** → usado quando a obra exige análise técnica mais completa e documentação complementar.\n\n"
        "Abaixo, apresentamos um resumo dos dois caminhos e um checklist básico dos itens que normalmente precisam ser providenciados."
    )

    st.markdown("#### 📄 Alvará de Construção Simplificado")
    st.markdown(
        "O **Alvará de Construção Simplificado** é uma forma mais rápida de licenciamento, voltada para casos mais simples. "
        "Ele costuma ser usado para **residência unifamiliar** e para **comércio/serviços de pequeno porte**, com área construída de até **250,00 m²**.\n\n"
        "A lógica desse alvará é mais enxuta e autodeclaratória, mas isso não elimina a necessidade de apresentar os documentos corretos "
        "e atender às exigências urbanísticas e técnicas do Município."
    )
    st.markdown("**✅ Checklist — documentos e itens principais**")
    st.markdown("[ ] Documento de identidade do requerente ou representante legal")
    st.markdown("[ ] CPF ou CNPJ")
    st.markdown("[ ] Matrícula atualizada do imóvel ou documento equivalente")
    st.markdown("[ ] Certidão negativa de IPTU")
    st.markdown("[ ] Parecer favorável de Adequabilidade Locacional")
    st.markdown("[ ] Tabela com índices urbanísticos e áreas da edificação")
    st.markdown("[ ] Projeto arquitetônico em arquivo digital")
    st.markdown("[ ] ART/RRT do responsável técnico")
    st.markdown("[ ] Termo de responsabilidade do responsável técnico")
    st.markdown("[ ] Termo de responsabilidade do proprietário")
    st.markdown("[ ] Isenção da licença ambiental")

    st.markdown("**📌 Atenção**")
    st.markdown("[ ] Confirmar se o caso realmente se enquadra como simplificado")
    st.markdown("[ ] Conferir se a área construída está dentro do limite permitido")
    st.markdown("[ ] Protocolar o pedido com antecedência mínima indicada pelo procedimento")
    st.markdown("[ ] Verificar se todos os arquivos digitais estão prontos e legíveis")

    st.markdown("#### 🏗️ Alvará de Construção (Obra Nova)")
    st.markdown(
        "O **Alvará de Construção (Obra Nova)** é o caminho regular de licenciamento para obras novas que exigem análise técnica completa da Prefeitura. "
        "Ele é mais detalhado e costuma ser necessário em casos que não se enquadram no procedimento simplificado ou que exigem documentação complementar.\n\n"
        "Esse tipo de alvará pede uma conferência mais ampla do projeto, incluindo aspectos urbanísticos, arquitetônicos, hidrossanitários, ambientais e, em alguns casos, exigências de outros órgãos."
    )
    st.markdown("**✅ Checklist — documentos principais**")
    st.markdown("[ ] Requerimento único")
    st.markdown("[ ] Documento de identidade do requerente ou representante legal")
    st.markdown("[ ] CPF ou CNPJ")
    st.markdown("[ ] Matrícula atualizada do imóvel")
    st.markdown("[ ] Autorização do proprietário, quando necessária")
    st.markdown("[ ] BCI")
    st.markdown("[ ] ART/RRT com comprovante de pagamento")
    st.markdown("[ ] Projeto arquitetônico assinado")
    st.markdown("[ ] Projeto hidrossanitário")
    st.markdown("[ ] Memorial de cálculo e drenagem pluvial")
    st.markdown("[ ] Declaração do SAAE sobre rede de esgoto, quando necessária")

    st.markdown("**✅ Checklist — documentos adicionais que podem ser exigidos**")
    st.markdown("[ ] Aprovação do Corpo de Bombeiros")
    st.markdown("[ ] Aprovação do IPHAN, quando o imóvel estiver em ZEIP")
    st.markdown("[ ] Licenciamento ambiental ou termo de isenção")
    st.markdown("[ ] PGRSCC")
    st.markdown("[ ] Autorização do COMAR, quando aplicável")
    st.markdown("[ ] Aprovação do DNIT ou SOP, quando houver acesso por rodovia")
    st.markdown("[ ] EIV, quando exigido pela legislação")

    st.markdown("**📌 Atenção**")
    st.markdown("[ ] Confirmar se o caso realmente exige alvará regular de obra nova")
    st.markdown("[ ] Conferir se há exigência de documentos complementares por localização ou tipologia")
    st.markdown("[ ] Verificar se o imóvel está em área com proteção especial")
    st.markdown("[ ] Conferir se o projeto atende às exigências técnicas antes do protocolo")
