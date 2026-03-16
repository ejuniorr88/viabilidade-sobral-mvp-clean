# Como usar a blindagem automática de login e relatório

## O que estes arquivos fazem
Estes testes servem para avisar no GitHub Actions se partes críticas de:
- login / sessão
- relatório
- PDF

sumirem ou forem alteradas de forma perigosa.

## Arquivos
- `tests/test_auth_contract.py`
- `tests/test_report_contract.py`

## Como isso funciona
Quando você fizer commit e push:
1. o GitHub Actions roda os testes
2. se tudo passar, fica verde
3. se alguma âncora crítica sumir, fica vermelho

## O que estes testes não fazem
Eles não testam o fluxo visual completo.
Eles servem como alarme técnico para:
- função crítica sumiu
- integração importante sumiu
- arquivo sensível perdeu uma parte essencial

## Quando isso ajuda mais
- mudanças em `core/auth.py`
- mudanças em `ui/relatorio.py`
- mudanças em `core/report_pdf.py`
- mudanças em `app.py` que impactem login ou relatório
