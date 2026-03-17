# Fluxo de atualização do projeto

Este arquivo explica, de forma simples, como aplicar uma alteração no projeto com mais segurança.

---

## 1. Receber a alteração
Quando houver uma mudança, primeiro identificar:

- quais arquivos são **novos**
- quais arquivos devem ser **substituídos**
- qual é a **tarefa**
- o que **não pode ser tocado**

---

## 2. Aplicar a alteração
No GitHub normal ou no editor que estiver usando:

- criar os arquivos novos
- substituir o conteúdo dos arquivos existentes
- salvar

---

## 3. Fazer commit e push
Depois de aplicar a alteração:

- escrever uma mensagem simples de commit
- confirmar
- enviar para a branch correta

Preferência atual:
- trabalhar primeiro em `dev`

---

## 4. Olhar a aba Actions
Depois do push:

1. abrir o repositório no GitHub
2. clicar em **Actions**
3. verificar se ficou:

- **verde** = testes automáticos passaram
- **vermelho** = algum teste falhou

Se ficar vermelho:
- abrir a execução
- abrir o bloco que falhou
- olhar o passo **Run tests**
- copiar ou tirar print do erro

---

## 5. Usar o checklist manual da tarefa
Depois de olhar o Actions, abrir o checklist manual correto.

Arquivo guia:
- `tests/COMO_USAR_CHECKLISTS.md`

Exemplos:
- mapa / zona / seção 3 / seção 4 → `tests/test_calculo_viabilidade_flow.md`
- login → `tests/test_login_flow.md`
- relatório → `tests/test_gerar_relatorio_flow.md`
- PDF → `tests/test_pdf_flow.md`
- Área do cliente → `tests/test_client_area_flow.md`
- créditos → `tests/test_creditos_flow.md`

---

## 6. Testar só a frente da tarefa
Não precisa testar o sistema inteiro toda vez.

O ideal é:
- olhar Actions
- testar a frente alterada
- testar as frentes sensíveis ligadas a ela

Exemplo:
se a tarefa for seção 4, testar:
- seção 3
- seção 4
- relatório, se depender disso

---

## 7. Quando considerar a tarefa fechada
Só considerar uma atualização segura quando:

- os testes automáticos estiverem verdes
- o checklist manual da tarefa passar
- a função principal da tarefa estiver funcionando
- nenhuma frente blindada tiver sido alterada sem necessidade

---

## 8. Regra para tarefas sensíveis
Quando a tarefa for sensível, sempre trabalhar com:

**Tarefa: [nome da tarefa]**  
**Proteção alta: não mexer em outras partes do sistema sem me avisar antes**

---

## 9. O que fazer se algo quebrar
Se uma alteração causar regressão:

- não empilhar patch em cima de patch
- restaurar o comportamento funcional conhecido
- comparar com a base estável
- corrigir pela causa raiz

---

## 10. Regra prática final
Em toda atualização sensível, seguir esta ordem:

1. aplicar alteração
2. commit / push
3. olhar **Actions**
4. abrir o checklist da tarefa
5. testar a frente alterada
6. só então considerar concluído
