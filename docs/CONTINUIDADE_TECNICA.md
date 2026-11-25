# ABIR TI — Guia de Continuidade Técnica

## 1. Objetivo do projeto

A ABIR TI é uma plataforma de consulta e monitoramento de oportunidades imobiliárias provenientes de leilões e modalidades de venda online no Brasil.

A aplicação utiliza Python e Streamlit, com uma base consolidada de imóveis e integração de diferentes fontes.

Aplicação publicada:
https://abir-ti-leiloes-imobiliarios-dt2e5dm7ftryzzsv8w32uh.streamlit.app/

Repositório:
https://github.com/AvnerAbir/abir-ti-leiloes-imobiliarios

## 2. Tecnologias

- Python
- Streamlit
- Pandas
- Playwright
- Git e GitHub
- GitHub Actions

Arquivo principal da aplicação: `app.py`.

## 3. Dados disponíveis

A base consolidada documentada possui:
- 26.804 registros de imóveis.
- 35 colunas.

Existe também uma base histórica:
- 1.144 registros.
- 27 colunas.

A divergência entre essas bases e o caminho utilizado pelo `app.py` precisa ser conferida antes de futuras alterações.

Campos disponíveis na base ampliada incluem identificação, tipo, estado, cidade, bairro, endereço, preço, avaliação, desconto, financiamento, áreas, quartos, vagas, modalidade, descrição e links.

Atenção: preço de oferta não deve ser confundido com lance inicial. Modalidades de venda direta e venda online não devem ser classificadas automaticamente como leilões.

## 4. Fontes e situação dos coletores

### Lance no Leilão
- Coletor desenvolvido e publicado.
- Envio de dados ao GitHub implementado.
- Integração com a base consolidada por rotina própria.
- Existe workflow do GitHub Actions relacionado à integração dos dados Lance.

### Caixa
- Foi realizada coleta de dados por API de serviço de terceiros.
- Snapshot documentado com 18.276 registros.
- Coletor desenvolvido localmente, mas não publicado como funcionalidade oficial.
- A integração de teste não acrescentou novos registros à base consolidada.

### Zuk e Mega Leilões
- Dados históricos presentes na base menor.

### Bradesco
- Coletor experimental desenvolvido localmente.
- Não publicado nem habilitado para execução automática.

### Banco PAN / D1LANCE
- Fonte identificada para investigação futura.
- Situação pendente de autorização e validação de acesso.

## 5. Integração de dados

O integrador publicado é `coleta/integrar_lance.py`.

A lógica atual acrescenta registros novos, mas não atualiza automaticamente os dados de imóveis que já existem na base.

Essa limitação deve ser considerada em futuras melhorias.

Não presumir que todos os registros representam leilões efetivamente realizados ou arrematados.

## 6. Arquivos importantes

- `app.py`: aplicação Streamlit.
- `requirements.txt`: dependências.
- `coleta/`: coletores, integradores e bases.
- `coleta/coletar_lance.py`: coletor Lance.
- `coleta/enviar_lance_github.py`: envio dos dados Lance.
- `coleta/integrar_lance.py`: integração.
- `.github/workflows/coleta_diaria.yml`: workflow relacionado à integração Lance.
- `README.md`: apresentação e visão geral do projeto.

## 7. Ambiente de desenvolvimento

Repositório local de trabalho:

`C:\Projetos\abir-ti-leiloes-imobiliarios-github`

Para instalar dependências em um ambiente virtual:

```powershell
pip install -r requirements.txt
```

Para executar a aplicação:

```powershell
streamlit run app.py
```

## 8. Segurança e publicação

Não publicar:
- Senhas, tokens ou credenciais.
- Arquivos de configuração com segredos.
- Bases temporárias e arquivos de teste.
- Backups e arquivos de cache.
- Arquivos locais não validados.

Evitar `git add .` indiscriminadamente. Adicionar somente os arquivos que foram revisados e que devem integrar o repositório.

## 9. Pendências técnicas conhecidas

1. Conferir qual base CSV o `app.py` utiliza efetivamente.
2. Resolver a divergência entre a base de 27 e a de 35 colunas.
3. Documentar integralmente os campos e filtros da aplicação.
4. Revisar os caminhos e dependências dos arquivos publicados.
5. Melhorar futuramente a atualização de registros existentes.
6. Validar as fontes adicionais antes de publicar novos coletores.

## 10. Diretriz de desenvolvimento

A prioridade é manter uma versão funcional da ABIR TI e aperfeiçoá-la gradualmente conforme as necessidades dos usuários.

Não implementar automações ou novos coletores sem necessidade definida.

O desenvolvimento deve priorizar estabilidade, confiabilidade dos dados, facilidade de manutenção e continuidade por outros profissionais.

## 11. Histórico e continuidade

Último commit de documentação confirmado:

`4400f91` — Atualiza README do projeto.

Este guia registra o estado conhecido do projeto em 24/11/2026. Antes de modificar funcionalidades, o desenvolvedor deverá conferir o código e os arquivos efetivamente presentes no repositório, pois algumas informações descrevem testes e componentes locais que ainda não foram publicados.