
# Google Maps — Fase 1

## O que entra nesta fase
- opção de usar Google Maps sem remover o mapa atual
- clique no mapa devolvendo latitude/longitude ao Python
- marcador do ponto selecionado
- círculo do raio visual
- camada básica das zonas em GeoJSON
- fallback automático para Folium quando a chave do Google não estiver configurada

## Como ativar
No Streamlit Cloud ou ambiente local, configurar:
- `MAP_PROVIDER=google`
- `GOOGLE_MAPS_API_KEY=sua_chave`

## O que continua igual
- cálculo urbanístico
- lookup da zona
- lookup da via
- relatórios
- créditos, login, pagamentos, cupons

## Critério de aceite
1. abrir o app com `MAP_PROVIDER=google`
2. clicar no mapa
3. ver o marcador no ponto
4. clicar em calcular viabilidade
5. confirmar que a zona/via continuam sendo identificadas pelo backend atual

## Rollback
Se houver qualquer problema:
- remover `MAP_PROVIDER=google`
- ou voltar `MAP_PROVIDER=folium`

O restante do sistema permanece funcionando no mapa antigo.
