# ABIR TI — Fontes pendentes de pesquisa e desenvolvimento

**Data do levantamento:** 23/11/2026  
**Projeto:** ABIR TI — Inteligência em Leilões Imobiliários

## 1. Objetivo

Este documento registra fontes de dados que ainda não foram pesquisadas integralmente,
fontes que apresentaram limitações técnicas e fontes cuja coleta ainda não foi implementada.

Seu objetivo é permitir a continuidade das pesquisas e do desenvolvimento por qualquer
profissional ou ferramenta de inteligência artificial.

O cadastro completo das fontes permanece em `coleta/fontes.json`.

## 2. Fontes com pesquisa parcial ou limitações identificadas

### 2.1 Caixa — portal oficial

- Fonte: Caixa Econômica Federal.
- Situação: pesquisa parcial.
- Limitação identificada: CAPTCHA no portal oficial.
- Alternativa utilizada: serviço intermediário que disponibiliza dados estruturados
  provenientes de arquivos públicos da Caixa.
- Resultado obtido: 25.222 registros.
- Observação: o serviço intermediário não é uma API oficial da Caixa.
- Trabalho futuro: avaliar outras formas de atualização dos dados e acompanhar
  eventuais mudanças na disponibilização dos arquivos públicos.
- Regra: não tentar contornar CAPTCHA ou bloqueios técnicos.

### 2.2 Bradesco — Vitrine Bradesco

- Página: https://vitrinebradesco.com.br/auctions?type=realstate
- API identificada: https://api.vitrinebradesco.com.br/v1/auctions
- Situação: pesquisa técnica realizada; coleta em massa não implementada.
- Resultado da pesquisa: 359 anúncios, distribuídos em 12 páginas.
- Dados identificados: GUID, imóvel, localização, valores, datas, descrição,
  modalidade e links.
- Trabalho futuro: concluir a validação da fonte, implementar coletor,
  preservar os dados originais e integrar os registros à base consolidada.
- Arquivo local de desenvolvimento: `coleta/coletor_bradesco.py`.
- Observação: o coletor ainda não está habilitado para produção.

### 2.3 Banco PAN — D1LANCE

- Página: https://d1lance.com.br/banco-pan
- Situação: pesquisa parcial.
- Resultado da pesquisa: 75 links de imóveis identificados na listagem.
- Página individual examinada: imóvel em Porto Alegre/RS, lote 10 de 35.
- Comitente confirmado no anúncio examinado: Banco Pan S/A.
- Modalidade identificada: venda direta.
- Trabalho futuro: capturar os anúncios individuais, estruturar os campos,
  verificar a modalidade e integrar os registros sem duplicação.
- Observação: não classificar automaticamente essas oportunidades como leilões.
  Separar preço sugerido de lance inicial.

### 2.4 D1LANCE — API geral

- Site: https://d1lance.com.br
- API identificada: https://api-prod.d1lance.com.br
- Situação: pesquisa técnica parcial.
- Rota identificada no código público: `leilao/lotes`.
- Limitação: a rota encontrada está associada à consulta de lotes de um leilão
  específico. Não foi confirmada uma rota geral de listagem Banco PAN.
- Alternativa identificada: listagem pública em HTML com links individuais.
- Trabalho futuro: avaliar outras páginas públicas e estruturar coletores
  por modalidade e instituição.

## 3. Fontes ainda não investigadas individualmente

As demais fontes cadastradas em `coleta/fontes.json` precisam passar por
avaliação individual.

Não atribuir bloqueios, indisponibilidade ou restrições sem evidência.

Para cada fonte, registrar futuramente:

- Nome e endereço oficial.
- Instituição ou leiloeiro responsável.
- Existência de API, CSV, XML, RSS, sitemap ou página pública.
- Método técnico de obtenção dos dados.
- Quantidade de imóveis encontrados.
- Campos disponíveis.
- Histórico de imóveis encerrados disponível ou não.
- Limitações técnicas observadas.
- Situação do desenvolvimento do coletor.
- Data da última pesquisa.

## 4. Prioridades para desenvolvimento futuro

1. Concluir o coletor Banco PAN/D1LANCE.
2. Concluir a implementação do coletor Bradesco, após validação da fonte.
3. Avaliar individualmente as demais fontes cadastradas.
4. Pesquisar fontes de imóveis encerrados e resultados históricos.
5. Priorizar integrações estruturadas por API e arquivos disponibilizados.
6. Manter controle de duplicidades e histórico de atualizações.
7. Registrar falhas e tentativas de coleta.
8. Atualizar este documento sempre que uma fonte for pesquisada.

## 5. Regras de continuidade

- Não apagar dados históricos durante atualizações.
- Não substituir valores desconhecidos por valores presumidos.
- Não confundir venda direta, venda online, licitação e leilão.
- Preservar a origem e o endereço original de cada registro.
- Não considerar uma API intermediária como oficial da instituição sem comprovação.
- Não contornar CAPTCHA, autenticação, bloqueios ou limites técnicos.
- Manter os coletores desabilitados até estarem testados e integrados.
- Registrar resultados negativos e limitações para evitar repetição desnecessária
  de pesquisas.

## 6. Relação com a documentação principal

Este documento complementa:

- `coleta/fontes.json`
- `coleta/README.md`
- `coleta/gerenciador_fontes.py`
- `coleta/controle_coleta.py`
- `coleta/nucleo_integracao.py`

A lista deverá ser utilizada como ponto de partida para futuras pesquisas,
automações e desenvolvimento de inteligência de dados.
