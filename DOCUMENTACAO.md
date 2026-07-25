# Gestão de Vagas — Documentação do Projeto

## 1. Visão geral

O **Gestão de Vagas** é um sistema local em Python para **buscar, armazenar e gerenciar vagas de emprego** coletadas na internet. Ele combina:

- **Robô de scraping** para captura automática de vagas em 13 portais
- **Filtro inteligente de relevância** para evitar vagas fora do termo buscado
- **Banco de dados SQLite** local para persistência
- **Dashboard web** em Streamlit com gráficos, filtros e quadro Kanban

O sistema foi desenvolvido conforme os requisitos definidos no arquivo `Projeto.txt`.

---

## 2. Arquitetura

```
[ Robô de Scraping ] ──> [ Filtro de Relevância + Data ] ──> [ SQLite (vagas.db) ] <── [ Painel Streamlit ]
```

### Fluxo da busca

1. O robô consulta os portais configurados com as **palavras-chave** ativas
2. As vagas coletadas passam pelo **filtro de relevância** (`scraper/filtros.py`)
3. Vagas fora do termo (ex.: "Operador de Caixa" ao buscar "Delphi") são **descartadas**
4. Vagas dentro do **intervalo de datas** (quando informado) são mantidas
5. Resultados relevantes são salvos no banco sem duplicar links

### Componentes principais

| Arquivo / Pasta          | Função                                              |
|--------------------------|-----------------------------------------------------|
| `app.py`                 | Interface web (dashboard Streamlit)                 |
| `init_db.py`             | Inicialização do banco de dados                     |
| `executar.bat`           | Atalho para iniciar o sistema no Windows            |
| `database/db.py`         | Acesso ao SQLite (CRUD, métricas, histórico)        |
| `scraper/scraper.py`     | Orquestração das buscas e gravação no banco         |
| `scraper/sites.py`       | Scrapers específicos por portal de vagas            |
| `scraper/filtros.py`     | Filtro de relevância e intervalo de datas           |
| `vagas.db`               | Banco local (criado automaticamente na 1ª execução) |
| `requirements.txt`       | Dependências Python                                 |

---

## 3. Tecnologias utilizadas

| Categoria             | Biblioteca / Ferramenta   |
|-----------------------|---------------------------|
| Interface             | Streamlit                 |
| Gráficos              | Plotly                    |
| Dados                 | Pandas                    |
| Banco de dados        | SQLite3 (nativo Python)   |
| Scraping (HTML)       | Requests + BeautifulSoup4 |
| Scraping (JavaScript) | Playwright                |

---

## 4. Sites de busca configurados

O robô consulta **13 portais**:

| Portal          | Método de coleta              |
|-----------------|-------------------------------|
| LinkedIn        | HTML (localização Brasil)     |
| Vagas.com.br    | HTML                          |
| Catho           | Playwright                    |
| Indeed          | Playwright + fallback HTML    |
| Glassdoor       | HTML                          |
| GeekHunter      | HTML                          |
| Revelo          | Playwright                    |
| Coodesh         | Playwright                    |
| Trampos.co      | API interna                   |
| Jerimum Jobs    | HTML                          |
| Remotar         | API (`api.remotar.com.br`)    |
| Upwork          | Playwright                    |
| Toptal          | HTML                          |

Cada vaga salva inclui o campo **fonte**, indicando de qual portal foi capturada.

**Portais que usam Playwright** (mais lentos, exigem Chromium instalado): Catho, Indeed, Revelo, Coodesh e Upwork.

---

## 5. Filtro de relevância

Muitos sites retornam vagas genéricas mesmo quando o termo de busca é específico. O módulo `scraper/filtros.py` resolve isso com regras rigorosas:

### Como funciona

- Termos técnicos como **delphi**, **python**, **c#**, **.net** são **obrigatórios** no título ou na descrição
- Palavras genéricas (desenvolvedor, remoto, pleno, analista etc.) **não bastam sozinhas**
- A comparação usa correspondência por palavra inteira (evita falsos positivos)

### Exemplos

| Palavra-chave | Vaga                         | Resultado    |
|---------------|------------------------------|--------------|
| `delphi`      | Desenvolvedor Delphi Pleno   | ✅ Aceita    |
| `delphi`      | Operador de Caixa            | ❌ Descartada |
| `python`      | Analista de Suporte          | ❌ Descartada |
| `c#`          | Desenvolvedor C# .NET        | ✅ Aceita    |

Após cada busca, o sistema informa quantas vagas foram **relevantes**, **novas** e **descartadas pelo filtro**.

---

## 6. Intervalo de datas de busca

Em **Parâmetros → Intervalo de Busca**, é possível definir:

- **Data inicial** — vagas publicadas antes desta data são ignoradas (quando a data é informada pelo portal)
- **Data final** — vagas publicadas depois desta data são ignoradas

### Comportamento

- Se **nenhuma data** estiver definida, o robô busca vagas de qualquer período (filtro de relevância continua ativo)
- Vagas **sem data de publicação** são mantidas (não descartadas por falta de informação)
- LinkedIn e Indeed ajustam automaticamente o período de busca com base na data inicial

Os valores ficam salvos na tabela `parametros` (`data_inicio_busca`, `data_fim_busca`).

---

## 7. Banco de dados

Arquivo: `vagas.db` (na raiz do projeto)

### Tabelas

#### `vagas`

| Campo           | Descrição                                     |
|-----------------|-----------------------------------------------|
| id              | Identificador único                           |
| titulo          | Título da vaga                                |
| empresa         | Nome da empresa                               |
| localizacao     | Cidade / região                               |
| link            | URL original (chave única — evita duplicatas) |
| descricao       | Resumo ou descrição da vaga                   |
| data_publicacao | Data de publicação (quando disponível)        |
| data_captura    | Data/hora em que o robô capturou a vaga       |
| status          | Estágio no funil de candidatura               |
| obs             | Observações (recrutador, WhatsApp, etc.)      |
| palavra_chave   | Termo que originou a busca                    |
| fonte           | Portal de origem (LinkedIn, Remotar, etc.)    |

**Status possíveis:** Pendente, Interessado, Candidatado, Entrevista, Proposta, Rejeitado

#### `palavras_chave`

Termos usados pelo robô na busca (ex.: `Delphi`, `Desenvolvedor Python Remoto`).

#### `parametros`

| Campo              | Descrição                              |
|--------------------|----------------------------------------|
| usuario, senha     | Credenciais de e-mail                  |
| smtp_servidor/porta| Configuração SMTP                      |
| pop_servidor/porta | Configuração POP                       |
| data_inicio_busca  | Data inicial do intervalo de busca     |
| data_fim_busca     | Data final do intervalo de busca       |

#### `historico_buscas`

Log de execuções do robô: data, termo buscado, vagas encontradas, vagas novas e mensagem com detalhes do filtro.

### Zerar banco de dados

Em **Parâmetros → Manutenção**, é possível apagar todos os dados:

- Remove **vagas**, **histórico de buscas** e **palavras-chave**
- Mantém **parâmetros de e-mail** e **intervalo de datas**
- Exige confirmação antes de executar (ação irreversível)

---

## 8. Telas do sistema

Acesso pelo menu lateral do Streamlit:

| Tela                    | Descrição                                                         |
|-------------------------|-------------------------------------------------------------------|
| **Dashboard**           | Métricas, funil, gráficos, filtros por tecnologia/modelo/nível    |
| **Kanban**              | Cartões de vagas por status, com opção de mover entre colunas     |
| **Cadastro de Vagas**   | Listar, cadastrar, editar e excluir vagas manualmente             |
| **Palavras-chave**      | Cadastro de termos, lista de sites e botão para executar o robô   |
| **Parâmetros**          | E-mail, intervalo de busca e manutenção (zerar banco)             |
| **Histórico de Buscas** | Registro de todas as execuções do robô                            |

### Parâmetros (abas)

| Aba                  | Função                                           |
|----------------------|--------------------------------------------------|
| **E-mail**           | Usuário, senha, servidores SMTP e POP            |
| **Intervalo de Busca** | Data inicial e final para filtrar publicações |
| **Manutenção**       | Zerar banco de dados com confirmação             |

---

## 9. Instalação (primeira vez)

### Pré-requisitos

- Windows 10 ou superior
- Python 3.10 ou superior instalado
- Conexão com a internet

### Passo a passo

1. Abra o **Prompt de Comando** ou **PowerShell**
2. Acesse a pasta do projeto:

```powershell
cd C:\GenVagas
```

3. Instale as dependências:

```powershell
python -m pip install -r requirements.txt
```

4. Instale o navegador usado pelo Playwright (necessário para Catho, Indeed, Revelo, Coodesh e Upwork):

```powershell
python -m playwright install chromium
```

5. Inicialize o banco (opcional — também ocorre automaticamente ao abrir o sistema):

```powershell
python init_db.py
```

---

## 10. Como executar o sistema

### Forma recomendada (um clique)

Dê um duplo clique no arquivo:

```
executar.bat
```

O painel será aberto automaticamente no navegador, geralmente em:

```
http://localhost:8501
```

### Forma manual (linha de comando)

```powershell
cd C:\GenVagas
python -m streamlit run app.py
```

---

## 11. Fluxo de uso recomendado

1. **Parâmetros → Intervalo de Busca** — defina o período desejado (opcional)
2. **Parâmetros → E-mail** — configure os dados de e-mail, se for utilizar envio futuro
3. **Palavras-chave** — cadastre termos específicos como `Delphi`, `Python`, `C#`
4. Clique em **Iniciar Robô de Busca** para coletar vagas nos 13 portais
5. Verifique o resultado: vagas **relevantes**, **novas** e **descartadas pelo filtro**
6. Acompanhe no **Dashboard** e organize no **Kanban**
7. Atualize o **status** das vagas conforme avança no processo seletivo
8. Consulte o **Histórico de Buscas** para ver o log de cada execução

### Dica para melhores resultados

- Use termos **específicos** (`Delphi`, `React`, `C#`) em vez de genéricos (`emprego`, `vaga`)
- Combine tecnologia + nível quando necessário: `Desenvolvedor Delphi Pleno`
- O filtro exige que os termos técnicos apareçam no título ou descrição da vaga

---

## 12. Execução automática do robô (agendador Windows)

Para rodar o robô em segundo plano sem abrir o painel:

```powershell
python C:\GenVagas\scraper\scraper.py
```

No **Agendador de Tarefas do Windows**, crie uma tarefa diária apontando para o comando acima. O robô utilizará as palavras-chave ativas e o intervalo de datas salvo nos parâmetros.

---

## 13. Observações importantes

- **Duplicatas:** o sistema usa `INSERT OR IGNORE` pelo link da vaga — a mesma vaga não é inserida duas vezes
- **Filtro de relevância:** vagas sem relação com o termo buscado são descartadas automaticamente
- **Bloqueios:** portais como LinkedIn, Indeed, Catho e Upwork podem limitar acessos automatizados
- **Playwright:** portais com JavaScript (Catho, Indeed, Revelo, Coodesh, Upwork) são mais lentos
- **Trampos.co:** a API lista oportunidades gerais; o filtro de relevância aplica o termo buscado
- **Remotar:** utiliza API pública com bom suporte a busca por termo
- **Dados locais:** todo o histórico fica em `vagas.db` na máquina do usuário
- **Zerar banco:** use com cuidado — remove vagas, histórico e palavras-chave de forma irreversível

---

## 14. Estrutura de pastas

```
Gestão de Vagas/
├── app.py                 # Dashboard Streamlit
├── init_db.py             # Script de inicialização do banco
├── executar.bat           # Atalho de execução no Windows
├── requirements.txt       # Dependências
├── DOCUMENTACAO.md        # Este documento
├── Projeto.txt            # Requisitos originais do projeto
├── vagas.db               # Banco SQLite (gerado automaticamente)
├── database/
│   ├── __init__.py
│   └── db.py              # Camada de acesso ao banco
└── scraper/
    ├── __init__.py
    ├── scraper.py         # Orquestrador do robô
    ├── sites.py           # Scrapers por portal (13 sites)
    └── filtros.py         # Filtro de relevância e datas
```

---

## 15. Suporte e manutenção

Se algum portal parar de retornar vagas, pode ser necessário atualizar os seletores HTML em `scraper/sites.py`, pois sites de emprego alteram sua estrutura com frequência.

Para ajustar o comportamento do filtro de busca, edite `scraper/filtros.py` (lista de palavras genéricas e regras de correspondência).

Para portais com muito JavaScript, o sistema já utiliza **Playwright**. Caso um novo portal exija navegador headless, adicione-o à constante `SITES_PLAYWRIGHT` em `scraper/sites.py`.
