# ABIR TI — Plataforma de Inteligência em Leilões Imobiliários

Plataforma tecnológica para centralização, organização, consulta e análise de oportunidades imobiliárias provenientes de diferentes fontes.

**Aplicação:** https://abir-ti-leiloes-imobiliarios-dt2e5dm7ftryzzsv8w32uh.streamlit.app/

**Repositório:** https://github.com/AvnerAbir/abir-ti-leiloes-imobiliarios

**Branch principal:** `main`

**Guia técnico:** [docs/CONTINUIDADE_TECNICA.md](docs/CONTINUIDADE_TECNICA.md)

**Referência documental:** 24/11/2026.

---

## 1. Objetivo

O ABIR TI tem como objetivo reunir dados de imóveis de diferentes fontes, padronizar informações e oferecer ferramentas de pesquisa e identificação de oportunidades.

A plataforma está em desenvolvimento contínuo e deve evoluir para incorporar novas fontes, histórico de preços, indicadores e recursos de inteligência imobiliária.

## 2. Tecnologias

- Python
- Streamlit
- Pandas
- Playwright
- Requests
- Git e GitHub
- GitHub Actions
- Streamlit Community Cloud

## 3. Situação atual

Última base consolidada documentada:

- 26.804 registros.
- 35 colunas.
- 25.222 registros históricos da Caixa.
- 438 registros novos incorporados do Lance.
- 1.144 registros de outras fontes históricas.

A aplicação oferece consulta, filtros e exportação de dados.

Esses números representam o último estado confirmado, não uma atualização em tempo real.

## 4. Fontes de dados

### Lance

Coletor desenvolvido em Python com Playwright.

Arquivos:
- `coleta/coletar_lance.py`
- `coleta/enviar_lance_github.py`
- `coleta/integrar_lance.py`

Última integração confirmada:
- 653 registros coletados.
- 438 novos registros.
- 215 duplicados.
- Base final com 26.804 registros.

A coleta é local. O envio ao GitHub e o workflow de integração estão implementados.

### Caixa

Foi desenvolvido e executado localmente um coletor para consulta de um serviço de terceiro:

`https://www.imoveisleilaobrasil.com.br/api/imoveis`

Não foi comprovado que esse serviço seja uma API oficial da Caixa.

Coleta realizada em 24/11/2026:
- 18.276 registros.
- 183 páginas.
- 35 colunas.
- 18.276 IDs únicos.
- Nenhum ID vazio.

Teste de integração em cópia da base:
- 18.276 registros coletados.
- 18.276 duplicados.
- Nenhum registro novo.

O teste não atualizou a base principal.

O integrador atual adiciona registros novos, mas não atualiza os campos dos imóveis existentes.

O coletor Caixa permanece como desenvolvimento local. Sua publicação não é prioridade nesta etapa.

### Bradesco

Existe desenvolvimento experimental local em `coleta/coletor_bradesco.py`.

Ainda não está habilitado para operação regular.

### PAN / D1LANCE

Fonte identificada, mas pendente de autorização e integração.

Não presumir que todos os lotes da plataforma sejam imóveis disponíveis diretamente pelo Banco PAN.

## 5. Aplicação

Arquivo principal: `app.py`.

A aplicação é publicada no Streamlit Community Cloud.

A base consolidada documentada é:

`coleta/base_consolidada_com_caixa.csv`

Atenção: o caminho efetivamente utilizado pelo `app.py` deve ser conferido antes de qualquer alteração, pois existe também `coleta/base_consolidada_leiloes.csv`, com estrutura diferente.

## 6. Integração e automação existente

O workflow:

`.github/workflows/coleta_diaria.yml`

Executa a integração do Lance quando acionado pelos eventos configurados ou manualmente.

Não existe automação geral de coleta de todas as fontes.

A automação da Caixa está fora do escopo atual.

## 7. Segurança

Nunca publicar:
- Senhas.
- Tokens.
- `secrets.toml`.
- `usuarios.json`.
- Credenciais.
- Arquivos de configuração sensíveis.

A autenticação utiliza configurações protegidas no Streamlit Cloud.

Revisar os arquivos antes de cada commit. Não utilizar `git add .` indiscriminadamente.

## 8. Prioridades de continuidade

1. Documentar e compreender a aplicação publicada.
2. Confirmar o caminho da base realmente utilizado.
3. Entender a estrutura e a origem dos dados.
4. Documentar o funcionamento dos coletores e integradores existentes.
5. Preservar o histórico da base.
6. Melhorar a atualização de registros existentes.
7. Validar novas fontes antes de ativá-las.
8. Planejar evoluções de inteligência imobiliária.

## 9. Orientação ao novo desenvolvedor

Começar pela leitura do [Guia de Continuidade Técnica](docs/CONTINUIDADE_TECNICA.md).

Consultar o histórico de commits, conferir os arquivos efetivamente publicados e reproduzir o ambiente antes de modificar o projeto.

O código e o histórico do GitHub prevalecem em caso de divergência com esta documentação.

Funcionalidades planejadas não devem ser apresentadas como concluídas.