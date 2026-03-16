# Regras fixas do projeto — Viabilidade Fácil / Viabilidade Urbana Sobral

Este arquivo registra as regras operacionais e de proteção do projeto para reduzir regressão e retrabalho.

---

## 1. Regra-mãe
**Nunca fazer remendo.**

Toda correção deve priorizar:
- causa raiz
- persistência forte
- fonte de verdade clara
- menor risco de regressão

---

## 2. Frentes blindadas

### Arquivos blindados
- `core/auth.py`
- `core/zone_resolution.py`

### Contratos blindados
#### Contrato da Seção 3 — Localização
Deve continuar entregando:
- `zone`
- `zone_lookup`
- `zone_sigla`
- `subzone_code`
- `road_name`
- `road_type`
- `distance_to_road_m`

#### Contrato da Seção 4 — Índices
Deve continuar buscando regra com base em:
- `zone_lookup`
- `zone_sigla`
- `subzone_code`
- `use_type_code`

#### Área do cliente
Deve continuar garantindo:
- clique no topo funciona
- abertura sem perder sessão
- pós-login volta para a Área do cliente
- nome/e-mail/créditos continuam aparecendo
- relatórios salvos continuam listados

---

## 3. Regras funcionais que não podem quebrar
- sem login, o fluxo protegido não deve ser liberado
- carteira só aparece depois do login
- saldo 0 não gera relatório
- saldo 0 pode clicar e deve abrir planos inline
- gerar relatório debita 1 crédito
- não pode haver débito duplicado
- não pode haver crédito duplicado
- créditos do usuário não podem sumir
- mudança de user_id não pode perder carteira
- refresh não deve derrubar sessão
- logout deve ser limpo
- item 3 só aparece depois do cálculo
- lógica de terreno irregular deve ser preservada
- descrição da zona deve aparecer só uma vez quando aplicável

---

## 4. Regra de escopo por tarefa
Toda tarefa sensível deve vir com:
- nome da tarefa
- proteção alta

Modelo:
**Tarefa: [nome da tarefa]**  
**Proteção alta: não mexer em outras partes do sistema sem me avisar antes**

---

## 5. Regra de alteração em arquivo sensível
Antes de tocar em frente sensível, deve ficar explícito:
- o que já funciona e não pode quebrar
- se a mudança é **aditiva** ou **substitutiva**
- quais arquivos serão alterados
- quais arquivos não serão tocados
- quais casos antigos serão preservados

---

## 6. Regras de verificação
### Teste automático
Sempre olhar a aba **Actions** depois de atualização sensível.

### Teste manual
Usar os checklists em `tests/` conforme a frente alterada.

Arquivo guia:
- `tests/COMO_USAR_CHECKLISTS.md`

---

## 7. Frentes que exigem checagem obrigatória
- mapa / zona / subzona
- seção 3
- seção 4
- login / sessão
- Área do cliente
- relatório
- PDF
- créditos / carteira / pagamento

---

## 8. Regra de patches
- preferir patch mínimo
- evitar muitos arquivos por tarefa sensível
- não expandir escopo silenciosamente
- não alterar layout sem necessidade
- quando houver arquivos envolvidos, preferir envio para baixar

---

## 9. Regra para Supabase
Quando houver SQL para Supabase, enviar no chat com a frase:
**Rode no supabase**

---

## 10. Regra operacional de segurança
Se uma alteração em frente sensível gerar regressão:
- não empilhar patch em cima de patch
- restaurar comportamento funcional conhecido
- comparar com base estável
- corrigir pela causa raiz

---

## 11. Regra prática final
Sempre que houver atualização sensível:
1. aplicar alteração
2. fazer commit/push
3. olhar **Actions**
4. usar o checklist manual da frente
5. só considerar fechado se o teste automático e o teste manual passarem
