from __future__ import annotations
# contrato: [ ] Aprovação do IPHAN, quando o imóvel estiver em ZEIP

from ui.report_components import render_checklist_block, render_html_fragment, render_info_box, render_section_card


def get_item_html(ctx: dict) -> str:
    simplificado = [
        'Documento de identidade do requerente ou representante legal',
        'CPF ou CNPJ',
        'Matrícula atualizada do imóvel ou documento equivalente',
        'Certidão negativa de IPTU',
        'Parecer favorável de Adequabilidade Locacional',
        'Tabela com índices urbanísticos e áreas da edificação',
        'Projeto arquitetônico em arquivo digital',
        'ART/RRT do responsável técnico',
        'Termo de responsabilidade do responsável técnico',
        'Termo de responsabilidade do proprietário',
        'Isenção da licença ambiental',
    ]
    obra_nova = [
        'Requerimento único',
        'Documento de identidade do requerente ou representante legal',
        'CPF ou CNPJ',
        'Matrícula atualizada do imóvel',
        'Autorização do proprietário, quando necessária',
        'BCI',
        'ART/RRT com comprovante de pagamento',
        'Projeto arquitetônico assinado',
        'Projeto hidrossanitário',
        'Memorial de cálculo e drenagem pluvial',
        'Declaração do SAAE sobre rede de esgoto, quando necessária',
        'Aprovação do Corpo de Bombeiros, IPHAN, licenciamento ambiental, PGRSCC, COMAR, DNIT/SOP ou EIV, quando aplicável',
        'Aprovação do IPHAN, quando o imóvel estiver em ZEIP',
    ]
    body = ''.join([
        '<p class="vf-lead">Após a finalização dos projetos, será necessário dar entrada na documentação junto à Prefeitura para obter o alvará de construção.</p>',
        '<p class="vf-lead">De forma geral, esse processo pode seguir por duas vias principais, com checklists diferentes.</p>',
        render_info_box('#### 📄 Alvará de Construção Simplificado', render_checklist_block(simplificado)),
        render_info_box('#### 🏗️ Alvará de Construção (Obra Nova)', render_checklist_block(obra_nova)),
    ])
    return render_section_card(15, 'O que acontece depois desta etapa?', body)


def render(ctx: dict) -> None:
    render_html_fragment(get_item_html(ctx))
