# ABIR TI — Inteligência em Leilões Imobiliários

## 1. Apresentação

O ABIR TI é uma plataforma desenvolvida em Python e Streamlit para consolidação, consulta e monitoramento de oportunidades imobiliárias provenientes de leilões e outras modalidades de venda.

**Aplicação publicada:**  
https://abir-ti-leiloes-imobiliarios-dt2e5dm7ftryzzsv8w32uh.streamlit.app/

**Repositório:**  
https://github.com/AvnerAbir/abir-ti-leiloes-imobiliarios

**Branch principal:** `main`

## 2. Arquitetura atual

O projeto utiliza:

- Python para coleta e processamento de dados.
- Playwright para automação de navegação no coletor Lance.
- Pandas para manipulação de dados.
- Streamlit para apresentação da plataforma.
- GitHub para versionamento e armazenamento dos arquivos.
- GitHub Actions para integração automatizada dos dados.
- Streamlit Community Cloud para publicação da aplicação.

### Fluxo de dados do Lance

A coleta do portal Lance é executada no computador local.

O fluxo funciona assim:

1. O coletor localiza os imóveis no portal.
2. Os dados são extraídos e salvos progressivamente em CSV.
3. Ao terminar, o coletor chama automaticamente o script de envio ao GitHub.
4. O script verifica se o CSV mudou.
5. Havendo alterações, cria um commit específico para o CSV e envia ao GitHub.
6. O GitHub Actions identifica a alteração e executa o integrador.
7. O integrador incorpora os imóveis novos à base consolidada.
8. O GitHub Actions publica a base atualizada no repositório.
9. O Streamlit utiliza a base publicada.

**Limitação importante:** a coleta Lance ainda depende do computador local ligado e com acesso à internet. A integração e publicação dos dados podem ocorrer na nuvem após o envio do CSV.

## 3. Arquivos principais

| Arquivo | Finalidade |
|---|---|
| `app.py` | Aplicação Streamlit |
| `requirements.txt` | Dependências Python |
| `coleta/base_consolidada_com_caixa.csv` | Base consolidada principal |
| `coleta/coletar_lance.py` | Coletor do portal Lance |
| `coleta/enviar_lance_github.py` | Envio automático do CSV ao GitHub |
| `coleta/integrar_lance.py` | Integração dos dados Lance à base |
| `.github/workflows/coleta_diaria.yml` | Automação da integração na nuvem |
| `coleta/fontes.json` | Cadastro de fontes de dados |
| `gerenciador_fontes.py` | Gerenciamento de fontes |
| `controle_coleta.py` | Controle de execução das coletas |

Os arquivos de teste, backups e capturas temporárias não fazem parte da operação principal.

## 4. Como executar a coleta Lance

O ambiente local utiliza Windows, PowerShell e ambiente virtual Python.

Na raiz do projeto, ativar o ambiente virtual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force; & "C:\Projetos\leiloes_judiciais_br\.venv\Scripts\Activate.ps1"
```

Executar o coletor:

```powershell
python coleta\coletar_lance.py
```

O coletor percorre os imóveis encontrados, verifica os registros já salvos e acrescenta os novos ao CSV progressivo.

Ao final, chama automaticamente:

```powershell
python coleta\enviar_lance_github.py
```

O envio é feito somente quando há alteração no CSV.

Para testar isoladamente o mecanismo de envio:

```powershell
python coleta\enviar_lance_github.py
```

Se não houver novos dados, a mensagem esperada é:

`Nenhum dado novo para enviar.`

## 5. Integração automática no GitHub

O workflow está em:

`.github/workflows/coleta_diaria.yml`

Nome:

`Integracao de Dados ABIR TI`

O workflow é acionado por:

- Push com alteração em `coleta/lance_novo_progressivo.csv`.
- Execução manual pelo GitHub Actions.

O processo executa:

1. Checkout do repositório.
2. Configuração do Python 3.12.
3. Verificação da existência do CSV.
4. Execução de `coleta/integrar_lance.py`.
5. Publicação da base consolidada, quando houver alterações.

O workflow possui permissão de escrita no conteúdo do repositório.

A integração preserva as 35 colunas da base principal e evita duplicidades por identificação de origem e código do imóvel ou URL.

Os campos do CSV Lance são compatíveis com a estrutura atual da base.

## 6. Estado dos dados

Na última integração local bem-sucedida:

| Indicador | Resultado |
|---|---:|
| Registros anteriores | 26.366 |
| Registros coletados do Lance | 653 |
| Novos registros incorporados | 438 |
| Duplicados identificados | 215 |
| Rejeitados | 0 |
| Total final | 26.804 |
| Colunas preservadas | 35 |

A base consolidada principal é:

`coleta/base_consolidada_com_caixa.csv`

### Última coleta local

Em 23/11/2026:

- Imóveis selecionados: 653.
- Novos registros: 0.
- Falhas: 0.
- Os 653 registros já estavam salvos.
- O envio automático foi executado e identificou que não havia alterações.

### Última integração na nuvem

A execução #3 do GitHub Actions terminou com sucesso.

Ela recebeu o CSV e identificou 653 registros duplicados, sem novos registros a incorporar.

O total permaneceu em 26.804 imóveis.

Isso comprova o funcionamento da integração na nuvem, mas ainda é necessário validar uma nova execução completa com registros inéditos.

## 7. Limitação da coleta Lance na nuvem

As tentativas de coleta diretamente pelo GitHub Actions receberam HTTP 403 do portal Lance.

Por esse motivo, foi adotada a solução intermediária:

- Coleta executada localmente.
- Envio automático do CSV ao GitHub.
- Integração e publicação executadas na nuvem.

Não implementar tentativas de contornar bloqueios, CAPTCHA, autenticação ou restrições do portal.

## 8. Outras fontes e pendências

O projeto possui cadastro de fontes adicionais, mas elas não devem ser consideradas automaticamente integradas à aplicação.

### Caixa

- Há dados da Caixa incorporados à base consolidada.
- A coleta anterior utilizou um serviço de terceiros, não uma API oficial comprovada da Caixa.
- Não presumir que todos os registros representam leilões.
- Modalidades como venda direta, venda online e licitação devem ser classificadas corretamente.

### Bradesco

- Página de anúncios identificada.
- Endpoint técnico de consulta identificado.
- Conversor e testes locais realizados.
- Coletor ainda não habilitado para coleta em massa.
- A fonte permanece pendente de validação e ativação.

Arquivo local de desenvolvimento: `coleta/coletor_bradesco.py`.

### Banco PAN / D1LANCE

- Página de imóveis do Banco PAN identificada na plataforma D1LANCE.
- Foram identificados links de lotes individuais.
- A fonte permanece pendente de autorização e integração.
- Não tratar venda direta como leilão tradicional.
- Preço sugerido deve ser registrado como preço de oferta, não como lance inicial.

### Demais fontes

O cadastro