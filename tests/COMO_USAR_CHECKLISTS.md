# Como usar os checklists do projeto

Este arquivo serve para orientar qual checklist manual usar conforme o tipo de alteração feita no projeto.

---

## 1. Se a mudança for em mapa / zona / subzona / seção 3 / seção 4

Use:
- `tests/test_calculo_viabilidade_flow.md`

Também confira:
- GitHub Actions na aba **Actions**

---

## 2. Se a mudança for em login / sessão

Use:
- `tests/test_login_flow.md`

Também confira:
- GitHub Actions na aba **Actions**

---

## 3. Se a mudança for na Área do cliente

Use:
- `tests/test_client_area_flow.md`

Também confira:
- GitHub Actions na aba **Actions**

---

## 4. Se a mudança for em relatório

Use:
- `tests/test_gerar_relatorio_flow.md`

Também confira:
- GitHub Actions na aba **Actions**

---

## 5. Se a mudança for em PDF

Use:
- `tests/test_pdf_flow.md`

Também confira:
- GitHub Actions na aba **Actions**

---

## 6. Se a mudança for em créditos / carteira / pagamento

Use:
- `tests/test_creditos_flow.md`

Também confira:
- GitHub Actions na aba **Actions**

---

## 7. Regra prática simples

### Sempre fazer:
1. Aplicar a alteração
2. Fazer commit/push
3. Abrir a aba **Actions**
4. Ver se ficou verde ou vermelho
5. Rodar o checklist manual correspondente à tarefa

---

## 8. Regra de segurança

Se a tarefa for sensível, sempre confirmar:
- quais arquivos foram alterados
- quais arquivos não deveriam ter sido tocados
- se o Actions ficou verde
- se o checklist manual da frente passou

---

## 9. Lembrete importante

- **Actions verde** = os testes automáticos passaram
- **Checklist manual** = confirma se o sistema real continua funcionando
- Os dois juntos dão mais segurança
