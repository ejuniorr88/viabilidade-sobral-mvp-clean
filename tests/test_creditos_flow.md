# Teste manual obrigatório — Créditos / Carteira / Pagamento

## Quando usar
Usar este checklist sempre que houver mudança em:
- créditos
- carteira
- pagamentos
- Mercado Pago
- extrato
- consumo de crédito
- app.py
- core/credits.py
- core/payments.py
- ui/payments_panel.py

## Checklist
- [ ] Confirmar que o saldo atual aparece
- [ ] Confirmar que o saldo não sumiu
- [ ] Com saldo maior que 0, gerar relatório e confirmar débito de 1 crédito
- [ ] Confirmar que não houve débito duplicado
- [ ] Com saldo 0, clicar em gerar relatório
- [ ] Confirmar que o relatório não é gerado
- [ ] Confirmar que os planos/pagamento inline aparecem
- [ ] Confirmar que o extrato aparece corretamente quando aplicável
- [ ] Confirmar que pagamentos recentes aparecem quando aplicável
- [ ] Confirmar que não houve duplicação de crédito
- [ ] Confirmar que a carteira continua vinculada corretamente ao usuário
