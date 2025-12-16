# Janus: PII Filter API

![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-v0.110.0-brightgreen)
![Ollama](https://img.shields.io/badge/AI-Ollama%20%7C%20Llama3-orange)
![License](https://img.shields.io/badge/license-MIT-yellow)

> **Uma Arquitetura de Middleware para Detecção, Anonimização e Restauração de PII em Grandes Modelos de Linguagem no Contexto da LGPD.**

Este projeto foi desenvolvido como **Trabalho de Conclusão de Curso (TCC)** do Bacharelado em Engenharia de Software da [**Universidade Católica do Salvador - UCSal**](https://www.ucsal.br/).

---

## O Problema

### Contexto Geral
A integração de Grandes Modelos de Linguagem (LLMs) em ambientes corporativos oferece ganhos de produtividade, mas introduz riscos críticos de privacidade. Ao enviar prompts contendo **Informações Pessoalmente Identificáveis (PII)** — como CPFs, nomes, e dados de saúde — para APIs públicas (OpenAI, Google Gemini), as organizações podem violar a **LGPD** e expor segredos industriais.

### Cenário de Aplicação: Recursos Humanos (RH)
O sistema foi validado no domínio de RH, onde a manipulação de dados é sensível e constante. Dados como históricos disciplinares, pretensões salariais e laudos médicos exigem proteção rigorosa, inviabilizando o uso de LLMs "crus" sem uma camada de proteção.

---

## Arquitetura Janus

O **Janus** atua como um *Reverse Proxy* inteligente e uma camada de segurança ("Firewall de Privacidade"). Ele intercepta o prompt do usuário, anonimiza os dados sensíveis localmente e, após a resposta do LLM externo, restaura os dados originais.

A solução adota uma estratégia de **"Defesa em Profundidade"**, orquestrando três camadas de filtragem sequencial (Pattern Pipe & Filter):

### 1. Filtro Determinístico (Regex)
A primeira linha de defesa. Extremamente rápida e precisa.
* **Foco:** Dados estruturados (CPF, CNPJ, E-mail, Telefone, RG).
* **Técnica:** Expressões Regulares com validação algorítmica (Dígito Verificador - Módulo 11).

### 2. Filtro Probabilístico (NER - Híbrido)
A camada de inteligência estatística.
* **Foco:** Entidades não estruturadas (Nomes, Locais, Organizações, Cargos).
* **Técnica:** Modelo de Deep Learning (`spaCy` pt_core_news_lg) aprimorado com um **EntityRuler** customizado para detectar profissões e cargos específicos de RH.

### 3. Filtro Semântico (LLM Local)
A camada de análise contextual ("Privacidade por Design").
* **Foco:** Dados sensíveis subjetivos (Saúde, Religião, Sindicalização, Segredos de Negócio).
* **Técnica:** Execução local de um LLM (Llama 3 via **Ollama**). Os dados sensíveis são detectados dentro da infraestrutura, sem nunca sair para a internet.

### Serviço de Restauração (Re-hidratação)
Diferente de soluções de mascaramento destrutivo (DLP tradicional), o Janus mantém a utilidade da resposta.
1.  O prompt anonimizado é enviado ao LLM externo (ex: `Gerar carta para [NOME_1]`).
2.  O LLM responde mantendo os placeholders (`Prezado [NOME_1]...`).
3.  O Janus intercepta a resposta e substitui `[NOME_1]` pelo nome original antes de entregar ao usuário.

---

## Tecnologias Utilizadas

* **Core:** Python 3.10+, FastAPI (Async/Await), Pydantic V2 (Validação Estrita).
* **IA & NLP:** spaCy (NER), Ollama (Llama 3 Local), Google Gemini (LLM Externo).
* **Engenharia de Software:** Design Patterns (Factory, Strategy, Dependency Injection), Server-Sent Events (SSE) para logs em tempo real.
* **Testes:** Pytest (Unitários e Integração), Análise de F1-Score.

---

## Instalação e Execução

### 1. Pré-requisitos
* Python 3.10 ou superior.
* [Ollama](https://ollama.com/) instalado e rodando.
* Uma API Key do Google Gemini (ou outro provedor configurado).

### 2. Configuração do Ambiente

Clone o repositório e crie o ambiente virtual:

```bash
git clone git@github.com:DiegoAndradeD/pii-filter.git
cd pii-filter

# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate

```

### 3. Dependências e Modelos
Instale as bibliotecas Python:

```bash
pip install -r requirements.txt

```

**Importante:** Baixe os modelos de IA necessários (spaCy e Ollama):

```bash
# Modelo de língua portuguesa para o spaCy
python -m spacy download pt_core_news_lg

# Modelo Llama 3 para o Ollama (execute no terminal)
ollama pull llama3:8b

```

### 4. Variáveis de Ambiente
Crie um arquivo `.env` na raiz do projeto:

```env
GEMINI_API_KEY=sua_chave_aqui
EXTERNAL_LLM_PROVIDER=gemini

```

### 5. Executando a API
Inicie o servidor (certifique-se que o Ollama também está rodando):

```bash
uvicorn src.main:app --reload

```

Acesse a documentação interativa em: `http://127.0.0.1:8000/docs`

---

## Testes e Validação
O projeto inclui uma suíte robusta de testes para garantir a eficácia da anonimização (F1-Score) e a performance.

### Executando os Testes
```bash
# Rodar todos os testes (Unitários e Integração)
pytest tests/

# Rodar testes com logs detalhados (útil para ver o fluxo)
pytest -v -s tests/

```

### Resultados ExperimentaisNos testes de validação com datasets de RH, a arquitetura atingiu um **F1-Score de ~0.60** em cenários de alta complexidade.

* **Filtro Regex:** Precisão > 99% para dados fiscais.
* **Estratégia:** O sistema prioriza o **Recall (Revocação)** em detrimento da precisão absoluta. Em segurança de dados, é preferível mascarar um falso positivo do que vazar um dado real (*Fail-Safe*).

---

## Referências
### Tecnologias Base
* **[FastAPI](https://fastapi.tiangolo.com/)** - Framework web moderno e rápido.
* **[Pydantic](https://www.google.com/search?q=https://docs.pydantic.dev/)** - Validação de dados robusta.
* **[spaCy](https://spacy.io/)** - Processamento de Linguagem Natural industrial.
* **[Ollama](https://ollama.com/)** - Execução de LLMs locais.

### Conceitos e Artigos
* **[Lei Geral de Proteção de Dados (LGPD)](https://www.gov.br/esporte/pt-br/acesso-a-informacao/lgpd)**
* **[Regular Expressions 101](https://regex101.com/)** - Ferramenta para debug de Regex.
* **[Privacy by Design](https://en.wikipedia.org/wiki/Privacy_by_design)** - Princípio arquitetural adotado.

---

## Equipe

* \[DIEGO ANDRADE DEIRO]
* \[DENILSON XAVIER OLIVEIRA]
* \[JOÃO VICTOR AZIZ LIMA DE SANTANA]
* \[LOREN VITORIA CAVALCANTE SANTOS]
* \[NEILLANE DE CARVALHO SÁ BARRETO DO ROSARIO]

---

## Licença

Este projeto está licenciado sob a **GNU General Public License (GPL) v3**.
Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

---

## Documentação Técnica

<details>
  <summary><strong>Clique aqui para expandir a Documentação Técnica Oficial (Detalhes de Arquitetura e Código)</strong></summary>

  <br>

## 1. Visão Geral da Arquitetura

O **Janus** atua como um _reverse proxy_ inteligente entre o usuário final e um Grande Modelo de Linguagem (LLM) externo. Sua função primordial é garantir que nenhum dado sensível (PII - _Personally Identifiable Information_) saia do perímetro seguro da infraestrutura local antes de ser enviado para processamento em nuvem.

### 1.1 Fluxo de Dados (Pipeline de Processamento)

A arquitetura segue um padrão de **Pipeline Sequencial de Filtragem** com **Restauração Inversa**.

1. **Input:** O usuário envia um prompt (ex: "Gere uma carta para o funcionário [CPF REAL]").

2. **Camada 1 - Filtro Determinístico (Regex):** Identifica padrões rígidos (CPF, CNPJ, Email).

3. **Camada 2 - Filtro Probabilístico (NER):** Identifica entidades nomeadas (Pessoas, Organizações, Cargos).

4. **Camada 3 - Filtro Semântico (LLM Local):** Utiliza um modelo Llama3 (via Ollama) para entender contextos sensíveis (Saúde, Finanças, Religião).

5. **Envio Seguro:** O texto anonimizado (com placeholders como `[CPF_1]`, `[NOME_2]`) é enviado ao LLM Externo (Gemini).

6. **Processamento Externo:** O Gemini processa o pedido mantendo os placeholders.

7. **Restauração:** O sistema recebe a resposta e substitui os placeholders de volta pelos dados originais.

8. **Output:** O usuário recebe a resposta com os dados reais, sem saber que o LLM externo nunca teve acesso a eles.


Snippet de código

```
graph TD
    User[Usuário] -->|Prompt Original| Proxy[Janus Proxy API]
    Proxy -->|Texto| Regex[Filtro 1: Regex Service]
    Regex -->|Texto + Placeholders| NER[Filtro 2: NER Service]
    NER -->|Texto + Placeholders| LocalLLM[Filtro 3: Local LLM Service]
    LocalLLM -->|Prompt Anonimizado| ExtLLM[LLM Externo (Gemini)]
    ExtLLM -->|Resposta com Placeholders| Restore[Restoration Service]
    Restore -->|Resposta Final Restaurada| User
```

---

## 2. Componentes do Sistema (Core)

### 2.1. Regex Service (`src/services/regex_service.py`)

A primeira linha de defesa. É extremamente rápida e precisa para formatos fixos.

- **Tecnologia:** Expressões Regulares (Python `re`).

- **Padrões Cobertos:** CPF, CNPJ, RG, E-mail, Telefone, CEP, Conta Bancária.

- **Validação Algorítmica:** Integração com `src/utils/validators.py` para verificar dígitos verificadores (CPF/CNPJ) e evitar falsos positivos (ex: "111.111.111-11").

- **Estratégia:** Priorização de padrões (ex: um e-mail tem prioridade sobre um padrão genérico de texto).


### 2.2. NER Service (`src/services/ner_service.py`)

Responsável por identificar "quem", "onde" e "o quê".

- **Tecnologia:** spaCy (Modelo `pt_core_news_lg`).

- **Entidades:** `NOME_COMPLETO`, `ORGANIZACAO`, `LOCAL`.

- **Entity Ruler Customizado:** Um componente adicional foi injetado no pipeline do spaCy para detectar **Profissões/Cargos** (ex: "Analista de Suporte", "Engenheiro de Software"), baseado em listas definidas em `constants.py`.

- **Prevenção de Sobreposição:** O serviço respeita os placeholders já inseridos pelo Regex (não tenta anonimizar o que já foi anonimizado).


### 2.3. Local LLM Service (`src/services/local_llm_service.py`)

O filtro mais sofisticado, capaz de entender contexto.

- **Tecnologia:** Ollama rodando `llama3:8b` (ou similar) localmente.

- **Objetivo:** Detectar dados sensíveis não estruturados (ex: "diagnosticado com Burnout" -> `CONDIÇÃO_DE_SAÚDE`, "salário de R$ 5.000" -> `INFORMAÇÃO_FINANCEIRA`).

- **Prompt Engineering:** Utiliza um _System Prompt_ otimizado para extração de JSON, instruindo o modelo a retornar trechos exatos e categorias.


### 2.4. Restoration Service (`src/services/restoration_service.py`)

O cérebro da reconstrução.

- **Lógica Inversa:** A restauração ocorre na ordem inversa da filtragem:

    1. Restaura Placeholders do LLM Local.

    2. Restaura Placeholders do NER.

    3. Restaura Placeholders do Regex.

- **Integridade:** Verifica se sobraram placeholders não tratados no texto final e remove duplicações de rótulos que o LLM externo possa ter gerado (ex: "CPF [CPF_1]" virar "CPF 123.456...").


---

## 3. Validação Científica e Testes

O projeto inclui um conjunto robusto de testes automatizados (`tests/`) para validar tanto a performance quanto a eficácia (F1-Score).

### 3.1. Benchmarking de Performance (`tests/test_benchmark.py`)

Mede o tempo de resposta (latência) de cada filtro isoladamente e do pipeline completo.

- **Métrica:** Segundos por requisição.

- **Utilidade:** Permite identificar gargalos (geralmente o Local LLM) e justificar escolhas arquiteturais na apresentação.


### 3.2. Testes de Eficácia (Ablation Studies)

Calculam **Precisão**, **Revocação (Recall)** e **F1-Score** comparando o output do sistema contra um _Ground Truth_ (Dataset anotado manualmente em `final-dataset.json`).

- **`test_regex_service.py`:** Testa isoladamente a capacidade de pegar CPFs, RGs, etc.

- **`test_ner_service.py`:** Testa a capacidade do spaCy de pegar nomes e locais.

- **`test_local_llm_service.py`:** Testa se o Llama3 está alucinando ou acertando os contextos sensíveis.

- **`test_pipeline_integration.py`:** O teste mais importante. Verifica como os 3 filtros trabalham juntos, garantindo que um não "atropela" o outro (lógica de precedência de spans).


---

## 4. Guia de Configuração e Execução

### 4.1. Pré-requisitos

- Python 3.10+

- [Ollama](https://ollama.com/) instalado e rodando.

- Chave de API do Google Gemini (para o LLM externo).


### 4.2. Instalação

1. **Clone o repositório e crie o ambiente virtual:**

    Bash

    ```
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # venv\Scripts\activate   # Windows
    ```

2. **Instale as dependências:**

    Bash

    ```
    pip install -r requirements.txt
    ```

3. **Baixe os modelos necessários:**

    Bash

    ```
    # Modelo spaCy para Português
    python -m spacy download pt_core_news_lg

    # Modelo Ollama (execute em outro terminal)
    ollama pull llama3:8b
    ollama serve
    ```

4. Configuração de Ambiente:

    Crie um arquivo .env na raiz:

    Snippet de código

    ```
    GEMINI_API_KEY=sua_chave_aqui
    EXTERNAL_LLM_PROVIDER=gemini
    ```


### 4.3. Executando a Aplicação

Bash

```
uvicorn main:app --reload
```

Acesse `http://localhost:8000` para ver a interface gráfica (Frontend React/Jinja2).

### 4.4. Executando os Testes (Benchmark)

Bash

```
# Para rodar todos os testes com output detalhado
pytest -v -s tests/
```

---

## 5. Diferenciais Técnicos para a Apresentação

Ao apresentar, destaque estes pontos no seu código:

1. **Dependency Injection (`src/api/proxy.py`):**

    - Mostre como `get_proxy_service` injeta as dependências. Isso torna o sistema modular. Se quiserem trocar o spaCy por outra IA no futuro, basta trocar a classe que implementa a interface `INERService`.

2. **Server-Sent Events (SSE):**

    - O uso de SSE (`stream_generator` em `proxy.py`) permite que o usuário veja o processo acontecendo em tempo real ("Detectando PII...", "Mascarando...", "Enviando ao Gemini..."). Isso gera uma UX superior e transparência no processo de segurança.

3. **Hibridismo (Regex + IA + LLM):**

    - Explique que Regex sozinho é "burro" para contexto, e LLM sozinho é "lento e caro" para achar CPF. A arquitetura Janus usa **o melhor de cada mundo**.

4. **Tratamento de Sobreposição (Overlap Handling):**

    - Mostre o método `_handle_overlaps` no `regex_service.py` ou a lógica no pipeline de teste. Isso evita erros comuns como mascarar um número dentro de um endereço erradamente.


---

## 6. Estrutura de Arquivos

Plaintext

```
janus-project/
├── src/
│   ├── api/
│   │   ├── proxy.py              # Endpoints da API e SSE
│   │   └── proxy_service.py      # Orquestrador principal
│   ├── core/
│   │   ├── constants.py          # Padrões Regex e Listas
│   │   └── llm_factory.py        # Factory para LLM Externo
│   ├── interfaces/               # Protocolos (Contratos)
│   ├── models/                   # Modelos Pydantic (Dados)
│   ├── services/
│   │   ├── regex_service.py      # Filtro 1
│   │   ├── ner_service.py        # Filtro 2
│   │   ├── local_llm_service.py  # Filtro 3
│   │   ├── gemini_service.py     # Conector Gemini
│   │   └── restoration_service.py# Lógica de Restauração
│   └── utils/
│       ├── validators.py         # Validação de CPF/CNPJ
│       └── sse_utils.py          # Formatação de Stream
├── tests/                        # Testes de Unidade e Integração
├── templates/
│   └── index.html                # Frontend
├── main.py                       # Entrada da aplicação FastAPI
└── requirements.txt
```

---
## 7. Detalhamento da Infraestrutura: `main.py`

### 7.1. Visão Geral e Responsabilidade

O arquivo `main.py` atua como o **Ponto de Entrada (Entry Point)** e o orquestrador central da aplicação web. Ele não contém lógica de negócio (como detecção de PII ou chamadas a LLMs); sua responsabilidade é estritamente **estrutural**. Ele inicializa o ciclo de vida do servidor ASGI (Asynchronous Server Gateway Interface), carrega as configurações de ambiente, agrega as rotas definidas em módulos dispersos e configura o serviço de arquivos estáticos.

Em uma arquitetura de microsserviços ou aplicações modulares modernas, o `main.py` deve ser mantido o mais limpo possível ("thin entry point"), delegando a lógica complexa para serviços injetáveis, garantindo que o acoplamento entre a infraestrutura web (FastAPI) e o domínio (Janus) seja mínimo.

### 7.2. Análise de Dependências

O arquivo depende de bibliotecas essenciais para o funcionamento do servidor e localização de recursos:

- **`fastapi` (`FastAPI`):** O framework web escolhido. Sua seleção se justifica pela necessidade de alta performance e, crucialmente, suporte nativo a `async/await`. Como o Janus depende de I/O (Input/Output) intensivo — chamadas de rede para APIs externas (Gemini/Ollama) e streaming de dados (SSE) —, o FastAPI evita o bloqueio da _event loop_, permitindo concorrência eficiente.

- **`fastapi.staticfiles` (`StaticFiles`):** Necessário para servir o frontend desacoplado (CSS, JS, imagens) que reside na pasta `/static`.

- **`dotenv` (`load_dotenv`):** Responsável pela segurança e configuração. Carrega variáveis de ambiente de um arquivo `.env` para o `os.environ`. Isso é vital para que chaves de API (como `GEMINI_API_KEY`) não fiquem _hardcoded_ no código fonte.

- **`pathlib` (`Path`):** Utilizada para manipulação agnóstica de sistema operacional dos caminhos de arquivos. Garante que o servidor encontre a pasta `/static` ou `/templates` tanto em Linux quanto em Windows sem erros de diretório.

- **Módulos Internos (`src.api.proxy`, `src.views.main_view`):** Importa os roteadores onde a lógica real dos endpoints reside. Isso demonstra a aplicação do padrão de projeto de **Separação de Preocupações (SoC)**.


### 7.3. Fluxo de Inicialização e Configuração

O script segue uma ordem de execução linear e crítica:

#### A. Carregamento de Ambiente

Python

```
load_dotenv()
```

**Análise:** Esta é a primeira instrução executável. É imperativo que ocorra antes da inicialização de qualquer serviço que dependa de credenciais (como o `GeminiService` ou `LocalLLMService`). Se isso falhar ou for movido para baixo, as _Factories_ podem levantar exceções de `KeyError` ao tentar instanciar os clientes de LLM.

#### B. Definição do Diretório Base

Python

```
BASE_DIR = Path(__file__).resolve().parent
```

**Análise:** Define dinamicamente a raiz do projeto baseada na localização do arquivo `main.py`. Isso torna a aplicação portátil, permitindo que ela seja executada em containers Docker ou estruturas de pastas diferentes sem quebra de referências relativas.

#### C. Instanciação da Aplicação

Python

```
app = FastAPI(
    title="PII FILTER",
    description="Proxy para filtragem de PII...",
    version="0.1.0",
)
```

**Análise:** Cria a instância do servidor ASGI. Os metadados (`title`, `description`, `version`) não são apenas cosméticos; eles são utilizados automaticamente pelo FastAPI para gerar a documentação **OpenAPI (Swagger UI)** acessível em `/docs`. Isso facilita a integração e teste por terceiros.

### 7.4. Arquitetura de Roteamento Modular

O `main.py` utiliza o método `.include_router()` para compor a API final. Isso confirma a arquitetura modular do Janus:

1. **API Router (`/api`):**

    Python

    ```
    app.include_router(proxy.router, prefix="/api")
    ```

    Agrega as rotas definidas em `src/api/proxy.py` (onde ocorre o processamento de SSE e lógica de negócio). O prefixo `/api` versiona semanticamente as chamadas de backend, separando-as das chamadas de visualização.

2. **View Router (`/`):**

    Python

    ```
    app.include_router(main_view.router)
    ```

    Agrega as rotas de `src/views/main_view.py`. Responsável por renderizar o HTML (Jinja2). A ausência de prefixo indica que este roteador gerencia a raiz do domínio.


### 7.5. Servindo Arquivos Estáticos

Python

```
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
```

**Análise:** O método `.mount()` é diferente de uma rota comum; ele "monta" uma aplicação WSGI/ASGI independente num sub-caminho. Aqui, ele instrui o FastAPI a servir qualquer arquivo dentro de `BASE_DIR / "static"` na URL `/static`.

- **Importância:** Sem isso, o `index.html` não conseguiria carregar o `main.css` ou scripts JavaScript, quebrando a interface do usuário. O uso de `BASE_DIR` garante que o caminho absoluto seja correto.


### 7.6. Conclusão Técnica sobre `main.py`

O arquivo `main.py` do projeto Janus é um exemplo de configuração "lean" (enxuta). Ele não polui o escopo global com lógica de negócio e estabelece corretamente as fronteiras entre a camada de apresentação (HTML/Static), a camada de serviço (API Proxy) e a configuração do ambiente. Ele expõe o objeto `app` que será consumido por servidores de produção como Uvicorn ou Gunicorn.

---
## 8. Camada de API e Streaming: `src/api/proxy.py`

### 8.1. Visão Geral e Responsabilidade

O arquivo `proxy.py` define o **Roteador da API** (API Router). Enquanto o `main.py` configura o servidor, o `proxy.py` define _como_ as requisições HTTP são processadas.

Sua responsabilidade primária não é executar a lógica de negócio (isso fica no `ProxyService`), mas sim **expor** essa lógica para o mundo externo via HTTP. Ele atua como um controlador que:

1. Resolve e injeta dependências.

2. Recebe o payload do cliente.

3. Estabelece um canal de **Streaming (SSE)**.

4. Invoca o orquestrador e transmite os resultados progressivamente.


### 8.2. Padrão de Injeção de Dependência (Dependency Injection)

O Janus utiliza fortemente o sistema de Injeção de Dependência (DI) do FastAPI. Isso é visível nas funções `get_...` e no uso de `Depends()`.

- Fábricas de Serviços (get_regex_service, get_ner_service, etc.):

    Estas funções simples atuam como "provedores". Elas instanciam as classes concretas que implementam as interfaces definidas em src/interfaces/.

    - _Por que isso é profissional?_ Isso desacopla a rota da implementação. Se amanhã você quiser trocar o `LocalLLMService` por um serviço remoto na AWS, você altera apenas a função `get_sensitive_topic_detector`, sem tocar na rota ou no orquestrador.

- **Composição do Orquestrador (`get_proxy_service`):**

    Python

    ```
    def get_proxy_service(
        regex_service: IRegexService = Depends(get_regex_service),
        ...
    ) -> ProxyService:
    ```

    O FastAPI resolve recursivamente todas as dependências. Ele cria o Regex, o NER, o LLM Local, o LLM Externo, e então passa todos eles para o construtor do `ProxyService`. Isso garante que o serviço principal já nasça "pronto para uso" com todas as suas ferramentas configuradas.


### 8.3. Arquitetura de Streaming (Server-Sent Events)

A função `stream_generator` implementa a lógica de **Server-Sent Events (SSE)**. Diferente de uma API REST tradicional que espera o processamento terminar para devolver um JSON (Request-Response), o SSE mantém a conexão aberta e envia "pedacinhos" de dados.

O fluxo dentro do gerador reflete o pipeline sequencial do Janus, mas com a adição crítica de **Observabilidade em Tempo Real**:

1. Pipeline em Cascata:

    O código demonstra explicitamente a passagem de estado entre os filtros:

    - `regex_filtered_text` alimenta o NER.

    - Os _placeholders_ do Regex (`regex_placeholders`) são passados para o NER para evitar colisões.

    - O `ner_filtered_text` alimenta o LLM Local.

    - Todos os placeholders anteriores (`all_previous_placeholders`) são passados para o LLM Local.

2. Feedback Visual (Logs):

    A cada etapa, o código itera sobre eventos (for event in ... yield event). Isso permite que o frontend exiba logs como:

    - _"Detecting PII with regex..."_

    - "PII detected: '123.456.789-00'..."

        Isso transforma uma "caixa preta" (o servidor processando) em uma "caixa de vidro", aumentando a confiança do usuário no sistema de segurança.

3. Execução Assíncrona:

    O uso de async def e await é vital. Enquanto o LLM externo (Gemini) está pensando (await proxy_service.call_external_llm), o servidor não fica travado; ele pode processar requisições de outros usuários. Os await asyncio.sleep(0.5) são inseridos estrategicamente para melhorar a UX (User Experience) no frontend, evitando que os logs passem rápido demais para serem lidos.


### 8.4. O Endpoint: `/process-prompt-stream`

Python

```
@router.post("/process-prompt-stream")
async def process_prompt_stream(...)
```

Este é o ponto de contato público.

- **Método POST:** Necessário pois o prompt pode ser longo (maior que o limite de URL de um GET).

- **Response Class:** Retorna `StreamingResponse` com `media_type="text/event-stream"`. Isso instrui o navegador a não fechar a conexão imediatamente e tratar a resposta como um fluxo de eventos contínuo.


### 8.5. Destaques do Código para Apresentação

Ao apresentar este arquivo, aponte para a linha que cria o payload final:

Python

```
final_payload = ProcessedResponse(
    final_response=final_response_text,
    pii_masked=all_pii_masked,  # Lista unificada de todas as PIIs achadas
    sensitive_topics_detected=...
)
```

Isso prova que o sistema não apenas devolve o texto, mas mantém um **rastreamento auditável** (`pii_masked`) de tudo que foi alterado, o que é um requisito fundamental para conformidade com a LGPD (princípio da transparência).

---
## 9. Orquestração de Serviço: `src/api/proxy_service.py`

### 9.1. Visão Geral e Responsabilidade

A classe `ProxyService` implementa o padrão de design **Facade** (ou Fachada). Ela simplifica a complexidade do subsistema, oferecendo uma interface unificada para o roteador da API.

Sua responsabilidade é **Orquestrar o Pipeline de Segurança**. Ela não sabe _como_ validar um CPF (papel do `RegexService`) nem _como_ carregar um modelo spaCy (papel do `NERService`). A função dela é garantir que esses serviços sejam chamados na ordem correta, que os dados fluam de um para o outro, e que o processo seja observável (logs).

### 9.2. Gerenciamento de Concorrência (Asyncio & Threads)

Este é, tecnicamente, um dos arquivos mais críticos para a performance da aplicação. Note o uso extensivo de `async` e `await`, mas com um detalhe crucial:

Python

```
filtered_text, mappings = await asyncio.to_thread(
    self.ner_service.filter_by_ner, text, existing_placeholders
)
```

**Análise Técnica:**

- **O Problema:** Python tem um _Global Interpreter Lock_ (GIL). Bibliotecas de processamento intensivo de CPU (como o **spaCy** no NER) ou chamadas de rede síncronas (como `requests` no **Ollama**) são "bloqueantes". Se executássemos `self.ner_service.filter_by_ner(...)` diretamente numa função `async`, travaríamos o servidor inteiro (Event Loop) até o processamento terminar. Ninguém mais conseguiria acessar o site nesse meio tempo.

- **A Solução:** O método `asyncio.to_thread` (disponível no Python 3.9+) envia essa execução pesada para uma _thread_ separada (pool de threads), liberando o Event Loop principal para aceitar novas conexões. Isso garante que o Janus seja escalável mesmo sob carga.


### 9.3. Fluxo Granular de Processamento

A classe divide o grande problema "Anonimizar Prompt" em 5 etapas atômicas e testáveis:

1. **`detect_pii_with_regex`:**

    - Executa rápido (CPU bound leve).

    - Gera os primeiros logs de SSE (`events.append(...)`).

    - Passa o `validate_pii_data=True` para ativar a verificação de dígitos verificadores (CPF/CNPJ).

2. **`detect_pii_with_ner`:**

    - Recebe `existing_placeholders`. Isso é vital para a integridade dos dados. Se o Regex já mascarou `[CPF_1]`, o NER precisa saber disso para não tentar achar uma entidade dentro da string `[CPF_1]` ou sobrescrevê-la incorretamente.

3. **`detect_sensitive_topics`:**

    - A camada mais lenta e inteligente.

    - Também recebe a lista acumulada de placeholders (Regex + NER) para garantir que o LLM Local foque apenas no texto "limpo" restante.

4. **`call_external_llm`:**

    - Abstrai a chamada para o Gemini (ou qualquer outro provedor configurado).

    - Isola o sistema de falhas externas (se o Gemini cair, o erro é capturado aqui antes de quebrar o fluxo de restauração).

5. **`restore_pii`:**

    - Recebe os mapeamentos de **todas** as etapas anteriores (`regex`, `ner`, `llm`).

    - Centraliza a lógica de reconstrução, garantindo que a resposta final faça sentido para o usuário.


### 9.4. Observabilidade (Server-Sent Events)

Uma característica marcante deste serviço é que todos os métodos retornam uma lista de `events` (além dos dados processados).

Python

```
events.append(
    create_sse_event({
        "type": "log",
        "message": f"   - PII detected: '{m.original_value}'..."
    })
)
```

Isso permite que o Frontend desenhe aquele console de "hackers" (log em tempo real), mostrando passo a passo o que a IA está detectando. Isso não é apenas estético; é uma ferramenta de **Auditoria em Tempo Real** para o usuário final.

### 9.5. Destaques para Apresentação

- **Baixo Acoplamento:** Aponte para o construtor `__init__`. Ele recebe interfaces (`IRegexService`, etc.), não classes concretas. Isso facilita tremendamente os **Testes Unitários** (Mocking). Você pode testar o `ProxyService` passando um `FakeRegexService` que sempre retorna sucesso, sem precisar processar texto de verdade.

- **Escalabilidade:** Mencione o tratamento de operações bloqueantes com `asyncio.to_thread`, essencial para middlewares de alta performance em Python.

---
## 10. Contratos e Interfaces: A Base do SOLID

Os arquivos `src/interfaces/external_llm_interface.py` e `src/api/proxy_service_interface.py` não contêm lógica de execução, mas definem as "leis" que o restante do sistema deve obedecer. Eles são a materialização do **D** do SOLID (_Dependency Inversion Principle_ - Princípio da Inversão de Dependência): módulos de alto nível (como o `ProxyService`) não devem depender de módulos de baixo nível (como o `RegexService`), ambos devem depender de abstrações.

### 10.1. Protocolos de Serviço Interno: `src/interfaces/proxy_service_interface.py`

Este arquivo utiliza o recurso moderno de **`typing.Protocol`** (introduzido no Python 3.8). Isso implementa a "Tipagem Estrutural" (ou _Duck Typing_ estático).

Análise Técnica:

Diferente de classes abstratas tradicionais onde você precisa herdar explicitamente (class MeuServico(IServico)), com Protocolos, qualquer classe que tenha os métodos com as assinaturas corretas é considerada válida. Isso torna o código Python mais flexível e idiomático.

- **`IRegexService`:**

    - **Contrato:** `filter_by_regex(text, validate_pii_data) -> Tuple[str, List[PIIMapping]]`.

    - **Propósito:** Garante que qualquer filtro determinístico retorne não apenas o texto limpo, mas a lista de mapeamentos (essencial para a restauração).

    - **Detalhe:** O parâmetro `validate_pii_data` força a implementação a considerar a validação algorítmica (ex: cálculo de dígito verificador de CPF), e não apenas o "match" visual.

- **`INERService`:**

    - **Contrato:** `filter_by_ner(text, existing_placeholders) -> Tuple[...]`.

    - **Propósito:** Define a interface para Reconhecimento de Entidade Nomeada.

    - **Ponto Crítico:** A presença obrigatória de `existing_placeholders` no contrato dita que qualquer implementação de NER **deve** ser capaz de lidar com (e ignorar) textos que já foram processados por camadas anteriores. Isso previne conflitos de pipeline no nível da arquitetura.

- **`ISensitiveTopicDetector`:**

    - **Contrato:** `filter_sensitive_topics(text, existing_placeholders) -> Tuple[...]`.

    - **Propósito:** Abstrai a detecção semântica. Hoje usamos Ollama (`LocalLLMService`), mas graças a essa interface, poderíamos trocar amanhã por um modelo BERT ou DistilRoBERTa sem alterar uma linha do código do `ProxyService`.

- **`IRestorationService`:**

    - **Contrato:** Define dois métodos vitais: `create_restoration_data` (prepara o estado) e `restore_all` (executa a ação).

    - **Propósito:** Garante que a lógica de "desfazer" a anonimização seja desacoplada da lógica de detecção. O retorno `Any` em `restoration_data` oferece flexibilidade para a implementação decidir qual estrutura de dados é melhor para guardar o estado de restauração.


### 10.2. Abstração de LLM Externo: `src/interfaces/external_llm_interface.py`

Aqui, o sistema utiliza **`abc.ABC`** (Abstract Base Classes).

Análise Técnica:

Ao contrário dos Protocolos, o uso de abc.ABC exige uma herança explícita. Isso é uma decisão de design mais rígida, apropriada para componentes críticos de infraestrutura externa onde queremos garantir conformidade estrita na hierarquia de classes.

- **Classe `ExternalLLMInterface`:**

    - **Método:** `send_prompt(prompt: str) -> Optional[str]`.

    - **Responsabilidade:** Define o canal de saída do Janus. Qualquer provedor de IA (Gemini, GPT-4, Claude, Llama-70b-Cloud) deve ser "encapsulado" numa classe que herde disto.

    - **Segurança:** O retorno é `Optional[str]`, forçando o consumidor desse método a tratar o caso de `None` (falha na comunicação ou bloqueio de conteúdo), evitando _crashes_ inesperados em produção.


### 10.3. Diagrama de Classes (Relacionamento Interface vs. Implementação)

Para ilustrar na sua apresentação como o sistema se conecta, visualize (ou desenhe) o seguinte esquema:

- **Nível Alto:** `ProxyService` (Orquestrador) "conhece" apenas `IRegexService`, `INERService`, etc.

- **Nível Baixo:** `RegexService` implementa `IRegexService`. `GeminiService` herda de `ExternalLLMInterface`.

- **Vantagem:** Durante os testes automatizados, nós injetamos "Mocks" (imitações) que obedecem a essas interfaces, permitindo testar o orquestrador sem carregar modelos pesados de IA.


### 10.4. Por que isso é importante para o TCC?

Incluir esses arquivos na documentação demonstra **maturidade de engenharia de software**. A maioria dos projetos acadêmicos foca apenas em "fazer funcionar" (scripting). O Janus foca em "ser sustentável e expansível".

- **Extensibilidade:** Se vocês quiserem adicionar um filtro novo (ex: Filtro de Imagem), basta criar uma nova interface e injetá-la.

- **Manutenibilidade:** As interfaces servem como documentação viva do que cada parte do sistema deve fazer.


---
## 11. Modelagem de Dados: `src/models/models.py`

### 11.1. Visão Geral e Responsabilidade

O arquivo `models.py` centraliza as estruturas de dados do Janus. Ele utiliza a biblioteca **Pydantic**, que é o padrão de ouro no ecossistema Python moderno (e a base do FastAPI) para _Data Parsing_ e _Validation_.

Sua responsabilidade é garantir a **Integridade dos Dados**. Quando um serviço recebe um objeto `PIIMapping`, ele não precisa verificar "será que o campo `span` existe?". O Pydantic garante que, se o objeto foi instanciado, ele é válido e possui os tipos corretos.

### 11.2. A Integração com FastAPI

O FastAPI usa esses modelos para fazer três coisas automaticamente:

1. **Validação de Request:** Se o frontend enviar um JSON sem o campo `original_prompt`, a API rejeita automaticamente com erro 422 (Unprocessable Entity).

2. **Serialização de Response:** Converte os objetos Python em JSON válido para enviar ao navegador.

3. **Documentação Automática:** Gera os esquemas que aparecem no Swagger UI (`/docs`), permitindo que outros desenvolvedores saibam exatamente o que enviar e o que esperar.


### 11.3. Análise das Estruturas

#### A. O Input: `PromptRequest`

Python

```
class PromptRequest(BaseModel):
    original_prompt: str
```

- **Função:** Atua como um DTO (_Data Transfer Object_) de entrada.

- **Simplicidade:** É intencionalmente simples. Define que a única coisa necessária para iniciar o processo é uma string de texto.


#### B. O Core do Rastreamento: `PIIMapping`

Esta é a classe mais crítica do sistema. Ela representa uma "unidade de anonimização".

Python

```
class PIIMapping(BaseModel):
    placeholder: str = Field(..., description="...")
    original_value: str = Field(..., description="...")
    type: str = Field(..., description="...")
    span: Tuple[int, int] = Field(..., description="...")
```

- **Rastreabilidade (`placeholder` & `original_value`):** Mantém o vínculo entre o que foi mascarado (ex: `[CPF_1]`) e o dado real (ex: `123.456.789-00`). Isso é o que permite a **Restauração** posterior.

- **Auditoria (`type`):** Classifica o dado (CPF, EMAIL, CARGO). Essencial para relatórios de conformidade LGPD.

- **Precisão Cirúrgica (`span`):**

    - O campo `span: Tuple[int, int]` guarda as coordenadas exatas (início e fim) onde o dado foi encontrado no texto original.

    - **Por que é vital?** Isso permite que testes automatizados (como os que vimos no `test_ner_service.py`) verifiquem se a detecção ocorreu no lugar certo, e ajuda a resolver conflitos se duas regras tentarem mascarar a mesma palavra.

- **Documentação (`Field`):** O uso de `Field(..., description="...")` enriquece a documentação da API, explicando o propósito de cada campo para quem consome a API.


#### C. O Output: `ProcessedResponse`

Python

```
class ProcessedResponse(BaseModel):
    final_response: str
    pii_masked: List[PIIMapping]
    sensitive_topics_detected: List[str]
```

- **Função:** Define o contrato de resposta final para o frontend.

- **Transparência:** Além da resposta textual (`final_response`), ela retorna a lista completa de modificações (`pii_masked`). Isso permite que o frontend mostre ao usuário: "Veja, eu protegi estes 5 dados antes de enviar para a IA".


#### D. Suporte a Testes: `PIIGroundTruth`

Python

```
@dataclass
class PIIGroundTruth:
    ...
```

- **Diferença Técnica:** Note que este usa `@dataclass` (do Python padrão) em vez de `BaseModel` (do Pydantic).

- **Motivo:** Geralmente, usamos dataclasses para estruturas internas leves onde a validação estrita de tipos do Pydantic (que tem um custo de performance) não é necessária. Esta classe é usada provavelmente para carregar o Dataset de Testes (`final-dataset.json`), servindo como gabarito para verificar a eficácia dos filtros.


### 11.4. Destaque para Apresentação

Na sua defesa de TCC, se perguntarem sobre **Tipagem e Segurança de Código**, mostre este arquivo.

- "Nós utilizamos **Pydantic** para garantir Type Safety em tempo de execução."

- "O modelo `PIIMapping` é a estrutura central que flui por todo o pipeline, garantindo que nenhum dado sensível se perca no processo de anonimização e restauração."


---
## 12. Regras de Negócio e Definições: `src/core/constants.py`

### 12.1. Visão Geral e Responsabilidade

O arquivo `constants.py` atua como o repositório central de conhecimento estático do Janus. Ele elimina o antipadrão de _Magic Strings_ (strings soltas espalhadas pelo código).

Sua responsabilidade é definir **O Que** o sistema deve detectar, enquanto os serviços (`RegexService`, `NERService`) definem **Como** detectar.

- **Benefício Arquitetural:** Se amanhã a regra de negócio mudar (ex: "Precisamos detectar também número de Passaporte"), você altera apenas este arquivo, e a mudança se propaga para todo o sistema sem risco de quebrar a lógica de processamento.


### 12.2. O Motor de Regex (`PII_PATTERNS`)

Python

```
PII_PATTERNS: Dict[str, re.Pattern] = {
    "CPF": re.compile(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b"),
    ...
}
```

**Análise Técnica:**

- **Pré-compilação:** O uso de `re.compile()` no momento da importação do módulo é uma otimização de performance crítica. O Python processa a string de regex e a transforma em uma estrutura interna de C apenas uma vez (no _startup_), em vez de fazer isso a cada requisição de usuário.

- **Contexto Brasileiro:** Os padrões não são genéricos. O CPF prevê pontuação opcional, o Telefone prevê o `+55` e o nono dígito móvel, e o RG aceita o dígito 'X'.


### 12.3. O Vocabulário do LLM (`SENSITIVE_CATEGORIES`)

Esta lista define o escopo de atuação do `LocalLLMService`.

- **Prompt Injection:** Estas strings são injetadas dinamicamente no _System Prompt_ do Llama-3.

- **Categorias Abstratas:** Note itens como `CONDICAO_DE_SAUDE` ou `PROBLEMA_PESSOAL_FAMILIAR`. Regex não consegue capturar isso ("Minha mãe está doente"). Definir isso aqui instrui a IA a buscar contextos semânticos específicos.


### 12.4. Refinamento do NER (`NER_PROFESSION_PATTERNS`)

Esta é talvez a seção mais sofisticada do arquivo.

**O Problema:** Modelos genéricos de NER (como o `pt_core_news_lg`) são treinados em notícias (Wikipédia, Jornais). Eles são ótimos para identificar "Lula" (PER) ou "Brasília" (LOC), mas péssimos para identificar "Analista de Suporte Júnior" em um texto de RH.

A Solução Híbrida:

O Janus utiliza o spaCy EntityRuler.

Python

```
{
    "label": "CARGO",
    "pattern": [
        {"LOWER": {"IN": ["analista", "gerente", ...]}},
        {"LOWER": "de", "OP": "?"},
        ...
        {"LOWER": {"IN": ["júnior", "pleno", ...]}, "OP": "?"},
    ],
},
```

Este padrão define uma gramática:

1. Começa com um cargo base (Analista).

2. Pode ter a preposição "de" (opcional).

3. Termina com a senioridade (Júnior, Pleno).


Isso permite que o Janus detecte cargos complexos que a IA puramente estatística deixaria passar, aumentando drasticamente o Recall (Revocação) nesta categoria.

### 12.5. Redução de Ruído (`NER_FALSE_POSITIVES`)

Conjunto (`set`) de palavras que o modelo pode confundir, mas que sabemos que não são PII.

- **Exemplos:** "Bom dia", "Urgente", "RH".

- **Performance:** O _lookup_ em um `set` é O(1) (tempo constante), tornando essa filtragem extremamente rápida antes mesmo de aplicar lógicas mais pesadas.


### 12.6. Mapeamento de Entidades (`NER_ENTITY_TYPE_MAPPING`)

Atua como um tradutor (Adapter). O spaCy devolve `PER` (Pessoa), mas o sistema interno do Janus (e o Regex) usa `NOME_COMPLETO`. Este dicionário normaliza a saída para que o `RestorationService` não precise lidar com múltiplos padrões de nomenclatura.

### 12.7. Destaque para Apresentação

Mostre a lista `NER_PROFESSION_PATTERNS`.

- **Argumento:** "Nós não dependemos apenas da 'caixa preta' da IA. Nós implementamos regras linguísticas determinísticas para capturar cargos e profissões específicas do mercado de TI e Corporativo, garantindo uma precisão superior em documentos de RH."


---
## 13. Abstração de Infraestrutura: `src/core/llm_factory.py`

### 13.1. Visão Geral e Responsabilidade

O arquivo `llm_factory.py` implementa o **Design Pattern Factory** (Fábrica). Sua única responsabilidade é instanciar a classe correta de LLM externo com base na configuração do ambiente, devolvendo-a para quem a solicitou (no caso, o `proxy.py`).

Este componente é a chave para evitar o acoplamento forte entre o sistema e um fornecedor específico (Vendor Lock-in). Embora o TCC utilize o Google Gemini, a arquitetura foi desenhada para ser agnóstica.

### 13.2. Padrão Factory (Fábrica)

Python

```
def get_llm_service() -> ExternalLLMInterface:
    provider = os.environ.get("EXTERNAL_LLM_PROVIDER", "gemini").lower()
    ...
    if provider == "gemini":
        return GeminiService()
```

**Análise Técnica:**

- **Desacoplamento de Criação:** O resto do sistema (especialmente o `proxy.py`) não sabe e não deve saber _como_ criar uma conexão com o Gemini, nem que o Gemini está sendo usado. Eles apenas pedem "me dê um LLM" e a fábrica entrega um objeto que obedece ao contrato `ExternalLLMInterface`.

- **Polimorfismo:** A função retorna a interface (`ExternalLLMInterface`), não a classe concreta (`GeminiService`). Isso garante que o Python trate qualquer provedor futuro da mesma maneira.


### 13.3. Configuração Dinâmica

O uso de `os.environ.get("EXTERNAL_LLM_PROVIDER", "gemini")` permite alterar o "cérebro" do sistema sem alterar uma linha de código, apenas mudando a variável de ambiente no arquivo `.env` ou no painel de controle do Docker/Cloud.

### 13.4. Extensibilidade (Scenario de Futuro)

Este arquivo é o lugar perfeito para demonstrar a **evolução futura** do projeto na sua apresentação.

Se amanhã vocês quiserem adicionar suporte ao GPT-4 da OpenAI, o processo seria cirúrgico:

1. Criar `OpenAIService` (implementando a interface).

2. Adicionar um `elif provider == "openai": return OpenAIService()` nesta fábrica.

3. Pronto. O resto do sistema (Regex, NER, Logs, Frontend) continuaria funcionando exatamente igual.


### 13.5. Tratamento de Erros de Configuração

Python

```
else:
    logger.error("LLM provider '%s' is not supported.", provider)
    raise ValueError(...)
```

A fábrica é defensiva. Se alguém configurar o ambiente errado (ex: `EXTERNAL_LLM_PROVIDER=chatgpt` sem ter implementado a classe), o sistema falha imediatamente na inicialização (Fail Fast), impedindo comportamentos imprevisíveis durante a execução.

### 13.6. Destaque para Apresentação

- **Argumento:** "Utilizamos o padrão **Factory** para isolar a dependência do provedor de IA. Isso prova que o Janus é um middleware neutro. Hoje usamos Gemini por custo e eficiência, mas a arquitetura suporta OpenAI, Anthropic ou até modelos locais (Llama via vLLM) apenas alterando uma variável de ambiente."


---
## 14. Validação Algorítmica: `src/utils/validators.py`

### 14.1. Visão Geral e Responsabilidade

Enquanto o `RegexService` encontra padrões visuais (ex: "algo que parece um CPF"), o `validators.py` confirma se aquele dado é matematicamente válido. Este arquivo implementa os algoritmos oficiais do governo brasileiro (Módulo 11) para verificação de dígitos.

Sua responsabilidade é **Reduzir Falsos Positivos**.

- _Cenário:_ O texto contém o número "111.222.333-44". O Regex vai capturar. Mas o `validators.py` vai rejeitar (CPFs com todos os dígitos iguais são inválidos). Isso impede que o sistema anonimize números aleatórios que não são dados pessoais reais.


### 14.2. Algoritmos de Checksum (CPF, CNPJ, CNH)

O código implementa a lógica "hardcore" de validação:

- **`validate_cpf` e `validate_cnpj`:** Implementam o cálculo dos dois dígitos verificadores (DV). Isso prova tecnicamente que a equipe se preocupou com a precisão dos dados, e não apenas com uma "limpeza superficial".

- **`validate_cnh`:** Um diferencial interessante. A validação de Carteira Nacional de Habilitação segue uma regra específica do DENATRAN, menos comum em bibliotecas genéricas, demonstrando profundidade na pesquisa do TCC.


### 14.3. Estratégia de "Plausibilidade" (`is_plausible_cpf`)

Python

```
def is_plausible_cpf(cpf: str) -> bool:
    ...
    if cpf == cpf[0] * 11: return False
    return True
```

Análise Técnica:

Note que o método validate_pii (o dispatcher) chama is_plausible_cpf para CPF, em vez de validate_cpf (que checa o dígito verificador estrito).

- **Decisão de Design:** Em sistemas de anonimização, é preferível pecar pelo excesso de cautela (Falso Positivo) do que deixar passar um dado real (Falso Negativo).

- **Justificativa:** Se um usuário digitar seu CPF com um dígito errado (erro de digitação), o algoritmo matemático diria "Inválido". Se o sistema ignorasse isso, vazaria o CPF quase completo do usuário. Ao usar a "plausibilidade" (tem 11 dígitos e não são repetidos?), o Janus decide proteger o dado mesmo que ele esteja com erro de digitação. Isso é uma decisão de segurança defensiva.


### 14.4. O Dispatcher (`validate_pii`)

Atua como um **Roteador de Validação**. Recebe o tipo (`type`) e o valor, e decide qual função específica chamar. Isso facilita a expansão: para adicionar validação de Cartão de Crédito (algoritmo de Luhn), basta adicionar um `elif pii_type == "CREDIT_CARD"` aqui.

---

## 15. Normalização de Dados: `src/utils/normalizers.py`

### 15.1. Visão Geral e Responsabilidade

Este módulo garante a **Consistência dos Dados**. Em análise de dados e segurança, "123.456.789-00" e "12345678900" são frequentemente tratados como entidades diferentes se não houver normalização.

### 15.2. Técnicas Aplicadas

Python

```
if pii_type in ["CPF", ...]:
    return re.sub(r"\D", "", value)
```

- **Sanitização Numérica:** Remove qualquer caractere que não seja dígito (`\D`). Isso é crucial para armazenar os dados de forma limpa no banco de dados (caso o Janus tivesse persistência) ou para comparar com listas de bloqueio.

- **Padronização de CEP:** Converte qualquer input de CEP para o formato visual `XXXXX-XXX`, garantindo que, se o dado for exibido no frontend ou logs, ele tenha uma formatação amigável.


---

## 16. Protocolo de Transporte: `src/utils/sse_utils.py`

### 16.1. Visão Geral e Responsabilidade

Este pequeno utilitário abstrai a complexidade do protocolo **Server-Sent Events (SSE)**.

### 16.2. O Formato SSE

Python

```
def create_sse_event(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"
```

Análise Técnica:

O SSE é um protocolo baseado em texto simples sobre HTTP. Para que o navegador (EventSource API) entenda a mensagem, ela deve começar com data: e terminar com duas quebras de linha \n\n.

- **Encapsulamento:** Ao centralizar essa formatação aqui, evita-se o erro comum de esquecer um `\n` ou formatar o JSON incorretamente no meio do `proxy.py`.

- **Serialização JSON:** Garante que o payload (seja um log ou a resposta final) seja um JSON válido, prevenindo erros de parse no JavaScript do frontend.


---
## 17. O Motor Determinístico: `src/services/regex_service.py`

### 17.1. Visão Geral e Responsabilidade

A classe `RegexService` representa a primeira linha de defesa do Janus. Sua responsabilidade é identificar padrões de texto rígidos e estruturados. Ao contrário dos modelos probabilísticos (IA) que "adivinham" se algo é um nome, este serviço "sabe" se algo é um CPF com base em regras matemáticas e sintáticas.

**Características Chave:**

- **Alta Velocidade:** Utiliza o motor de expressões regulares otimizado do Python (`re`), capaz de processar milhares de caracteres em milissegundos.

- **Baixa Taxa de Falsos Negativos:** Se um CPF válido estiver presente no texto, este serviço **vai** encontrá-lo.

- **Determinismo:** Para uma mesma entrada, a saída é sempre idêntica (sem alucinações).


### 17.2. Lógica de Resolução de Conflitos (Overlap Handling)

Um dos maiores desafios técnicos em sistemas de extração de entidades é a **Sobreposição de Spans**.

- _Exemplo:_ O texto contém o número `12345678`.

    - A Regex de `TELEFONE` pode achar que é um telefone incompleto.

    - A Regex de `RG` pode achar que é um RG.

    - A Regex de `CONTA_BANCARIA` pode achar que é uma conta.


A Solução Algorítmica:

O método _handle_overlaps implementa uma lógica robusta de priorização:

1. **Agrupamento:** Identifica todos os matches que ocupam o mesmo espaço físico no texto.

2. **Ranking de Prioridade:** Utiliza o dicionário estático `_TYPE_PRIORITY`:

    Python

    ```
    _TYPE_PRIORITY: Dict[str, int] = {
        "CPF": 1,
        "RG": 2,
        "TELEFONE": 3,
        ...
    }
    ```

    Isso diz ao sistema: "Se você estiver em dúvida se um número é um CPF ou um Telefone, assuma que é um **CPF** (Prioridade 1 > 3)". Essa hierarquia de decisão é vital para reduzir ruído.


### 17.3. Estratégia de Substituição Segura (Reverse Replacement)

No método `_replace_pii_with_placeholders`, há um detalhe técnico sutil, mas crítico:

Python

```
matches.sort(key=lambda x: x["match"].start(), reverse=True)
```

Análise Técnica:

A lista de matches é ordenada de trás para frente (do final do texto para o início) antes da substituição.

- **O Problema:** Se você tem um texto de 100 caracteres e substitui uma palavra na posição 10 por um placeholder maior ou menor, todos os índices das palavras subsequentes mudam (shift). Se você tentar substituir a próxima palavra baseada nos índices originais, vai substituir o texto errado.

- **A Solução:** Ao substituir do fim para o começo, a alteração do tamanho da string à direita não afeta os índices dos elementos à esquerda que ainda precisam ser processados. Isso garante integridade posicional perfeita.


### 17.4. Integração com Validação

O método `_find_all_matches` demonstra o uso do padrão **Filter**:

Python

```
if validate_pii_data and not validate_pii(pii_type, pii_value):
    continue
```

Aqui o serviço se conecta ao `src/utils/validators.py`. Isso transforma o Regex de uma ferramenta puramente sintática ("parece um CPF") para uma ferramenta semântica ("é um CPF válido"). Isso é essencial para evitar mascarar números de versão de software (ex: "v1.02.333") achando que são documentos pessoais.

### 17.5. Geração de Mapeamento (`PIIMapping`)

Para cada substituição, o serviço instancia um objeto `PIIMapping`.

- **Contador Sequencial:** Note a lógica `placeholder = f"[{pii_type}_{current_counts[pii_type]}]"`. Isso gera identificadores únicos (`[CPF_1]`, `[CPF_2]`) em vez de genéricos (`[CPF]`). Isso é fundamental para a **Restauração**, permitindo que o sistema saiba exatamente qual CPF original pertence a qual posição no texto processado pelo LLM.


### 17.6. Destaques para Apresentação (TCC)

- **Complexidade Algorítmica:** Mencione que o algoritmo de _Overlap Resolution_ é uma implementação simplificada do problema clássico de _Interval Scheduling_, focado em maximizar a segurança (prioridade) em vez da quantidade de itens.

- **Integridade:** Destaque a estratégia de substituição reversa como prova de cuidado com a manipulação de strings em memória.

- **Eficiência:** Enfatize que este serviço remove 80-90% das PIIs mais comuns (CPFs, E-mails) antes mesmo de acionar as IAs pesadas, economizando recursos computacionais.


---
## 18. A Inteligência Probabilística: `src/services/ner_service.py`

### 18.1. Visão Geral e Responsabilidade

A classe `NERService` introduz a Inteligência Artificial no pipeline de filtragem. Sua responsabilidade é detectar PIIs que não possuem formato fixo, como **Nomes de Pessoas** (que podem ser qualquer coisa), **Organizações**, **Locais** e, crucialmente para o seu contexto de RH, **Cargos e Profissões**.

Diferencial Técnico:

O serviço implementa uma abordagem Híbrida:

1. **Estatística (Deep Learning):** Utiliza o modelo pré-treinado `pt_core_news_lg` do spaCy para identificar entidades genéricas baseadas em vetores de palavras e contexto.

2. **Baseada em Regras (EntityRuler):** Injeta regras gramaticais customizadas (definidas em `constants.py`) diretamente no pipeline da IA para detectar cargos específicos (ex: "Desenvolvedor Full Stack Sênior") que o modelo padrão ignoraria.


### 18.2. Inicialização Resiliente

Python

```
if "entity_ruler" not in self.nlp.pipe_names:
    ruler = self.nlp.add_pipe("entity_ruler", before="ner")
    ruler.add_patterns(self._PROFESSION_PATTERNS)
```

Análise Técnica:

Note a instrução before="ner".

- **Estratégia:** O código força as regras de profissão (EntityRuler) a rodarem **antes** da rede neural (NER).

- **Por que?** Isso garante que "Analista de Sistemas" seja classificado como `CARGO` (nossa regra) e não como `PESSOA` ou `ORG` (alucinação comum da IA). Isso mostra controle refinado sobre o pipeline de NLP.


### 18.3. Consciência de Pipeline (`_extract_entities_avoiding_placeholders`)

Esta é talvez a lógica mais importante para a integridade do sistema como um todo.

O Problema:

Imagine que o Regex já transformou "João, CPF 123..." em "João, CPF [CPF_1]...".

Se o spaCy rodar cegamente, ele pode interpretar [CPF_1] como uma Organização ou um Nome Estranho, tentando mascarar o que já é uma máscara. Isso geraria algo como [ORG_1] escondendo o [CPF_1], quebrando a restauração.

A Solução:

O método recebe existing_placeholders e calcula as posições (spans) onde eles estão.

Python

```
if entity_start < ph_end and entity_end > ph_start:
    overlaps = True
    break
```

Ele ignora qualquer entidade nova que colida com o trabalho feito pela camada anterior. Isso valida a tese de "Arquitetura em Camadas Cooperativas".

### 18.4. Heurísticas de Redução de Ruído (`_extract_entities`)

Modelos de IA geram ruído. O código implementa várias "guardrails" (proteções) para limpar a saída do spaCy:

- **Filtro de Tamanho:** Ignora entidades menores que 3 caracteres (`len < 3`), evitando mascarar iniciais ou preposições soltas.

- **Filtro de Digitos:** `if ent_text.isdigit(): continue`. O NER não deve tentar mascarar números puros; essa é a função do Regex. Isso evita conflito de responsabilidades.

- **Filtro de Falsos Positivos:** Checa contra o `set` definido em `constants.py` (ex: "Bom dia", "Olá").

- **Sanitização de Artefatos:** Remove entidades que parecem placeholders (`[` ou `]`) ou labels (`:`), prevenindo loops de processamento.


### 18.5. Resolução de Conflitos Internos (`_filter_overlapping_entities`)

Assim como no Regex, o spaCy pode retornar entidades sobrepostas (ex: "São Paulo" e "Paulo").

O algoritmo aqui prioriza a Entidade Mais Longa (Greedy Longest Match), assumindo que ela carrega mais contexto semântico ("São Paulo" > "Paulo").

### 18.6. Substituição e Mapeamento

Segue o mesmo padrão robusto do Regex:

1. Ordenação reversa (`reverse=True`) para evitar quebra de índices.

2. Geração de placeholders únicos (`[NOME_COMPLETO_1]`).

3. Criação de objetos `PIIMapping` com coordenadas exatas.


### 18.7. Destaques para Apresentação

- **Customização de Domínio:** Enfatize fortemente o uso do `EntityRuler`. Isso mostra que você não apenas "baixou uma biblioteca", mas adaptou a tecnologia para o problema de negócio (RH/LGPD).

- **Robustez:** Aponte para o tratamento de erros no `__init__`. Se o modelo não carregar, o sistema loga um erro crítico, mas não derruba a aplicação inteira (dependendo de como o `main.py` trata, mas o serviço avisa).

- **Integração Inteligente:** O método que evita placeholders prova que os componentes do sistema conversam entre si, resolvendo o problema complexo de orquestração de múltiplos filtros.


---
## 19. A Inteligência Semântica Local: `src/services/local_llm_service.py`

### 19.1. Visão Geral e Responsabilidade

A classe `LocalLLMService` é responsável pela análise profunda do texto. Enquanto Regex e NER procuram por padrões sintáticos e entidades gramaticais, este serviço utiliza o modelo **Llama 3 (via Ollama)** para entender o significado semântico.

O Problema que Resolve:

Um Regex não consegue detectar "Minha conta é aquela que você sabe" (contexto implícito) ou "diagnosticado com Burnout" (dado sensível de saúde não estruturado). O LLM consegue ler e entender que isso constitui um dado sensível segundo a LGPD.

### 19.2. Engenharia de Prompt (Prompt Engineering)

O método `_build_system_prompt` é uma peça de engenharia crítica.

- **Persona:** "Você é um especialista em LGPD e RH." Isso ancora o modelo num subespaço latente mais profissional e jurídico.

- **Instrução Negativa:** "NÃO extraia PIIs de padrão óbvio como CPF...". Isso é vital para economizar tokens e evitar redundância com o `RegexService`.

- **Saída Estruturada (JSON Mode):** O prompt exige `Retorne APENAS um objeto JSON`. Além disso, o payload da requisição usa `"format": "json"`. Isso força o Ollama a restringir a geração de tokens para garantir um JSON válido, facilitando o parseamento pelo Python.


### 19.3. Integração com Ollama (API)

Python

```
self.api_url = f"{host}/api/generate"
payload = { "model": self.model_name, ..., "stream": False }
requests.post(...)
```

Análise Técnica:

O serviço atua como um Client REST.

- **Timeout:** O uso de `timeout=90` é realista para inferência local em CPU/GPU modesta. LLMs podem demorar a responder.

- **Stream False:** Aqui optou-se por esperar a resposta completa para garantir a integridade do JSON antes de processar.


### 19.4. Orquestração e Prevenção de Sobreposição

Assim como no NER, o LLM precisa respeitar o trabalho das camadas anteriores.

1. **Mapeamento de Placeholders:** `_find_placeholder_spans` localiza onde estão os `[CPF_1]`, `[NOME_2]` já inseridos.

2. **Verificação de Colisão:**

    Python

    ```
    if start_pos < ph_end and end_pos > ph_start:
        overlaps = True
    ```

    Se o LLM disser que "CPF [CPF_1]" é um dado sensível, o código ignora essa sugestão, pois ela invade um espaço protegido.


### 19.5. Tratamento de Alucinações

LLMs alucinam (inventam textos que não estão no original). O código implementa defesas:

- **Verificação de Existência:** `start_pos = text.find(exact_text)`. Se o LLM disser que encontrou a palavra "Banana" mas "Banana" não está no texto original (ou seja, o LLM inventou), `find` retorna -1 e o código descarta o fragmento. Isso garante que o Janus nunca estrague o texto original com base em um delírio da IA.


### 19.6. Substituição Reversa

Novamente, a estratégia de `found_fragments.sort(key=lambda x: x["start_pos"], reverse=True)` é utilizada para garantir que as substituições no final do texto não alterem os índices do início, mantendo a integridade do documento.

### 19.7. Destaques para Apresentação

- **Privacidade Total:** Enfatize que, como o Ollama roda localmente (`localhost:11434`), os dados sensíveis nunca saem da infraestrutura da empresa durante essa etapa de análise. É o conceito de _Privacy by Design_.

- **Custo Zero:** Diferente de usar GPT-4 para filtrar PII (que custaria por token), rodar Llama 3 localmente tem custo marginal zero após o investimento em hardware.


---
## 20. Arquitetura Base: `src/services/base_llm_service.py`

### 20.1. Visão Geral e Responsabilidade

A classe `BaseLLMService` é uma classe abstrata que atua como a **Fundação da Comunicação Externa**. Ela define o comportamento padrão que _qualquer_ LLM (seja Gemini, OpenAI ou Claude) deve seguir ao interagir com o Janus.

Padrão de Projeto: Template Method

Este é o ponto arquitetural mais forte deste arquivo.

- **O Método Template (`send_prompt`):** Define o esqueleto do algoritmo.

    1. Prepara o contexto (System Prompt).

    2. Concatena com o prompt do usuário.

    3. Chama o método abstrato `_send_request` (o "gancho").

- **A Regra:** As classes filhas (como `GeminiService`) **não** devem sobrescrever `send_prompt`. Elas apenas implementam o detalhe de como enviar a string final para a API. Isso garante que o **Protocolo de Segurança (System Prompt)** seja aplicado _sempre_, independentemente do provedor de IA escolhido.


### 20.2. Injeção de Contexto de Segurança (`_SYSTEM_PROMPT`)

Esta constante é vital para a UX do sistema.

Python

```
_SYSTEM_PROMPT = """
Atenção: Você é um assistente de IA... Informações Pessoais Identificáveis (PII) foram substituídas por placeholders...
"""
```

Análise Técnica:

Sem isso, se o usuário perguntasse "Gere uma carta para [NOME_1]", o LLM externo poderia responder: "Não entendi o que é [NOME_1], por favor forneça o nome real".

Com esse prompt injetado no pre-flight, o Janus "ensina" ao LLM externo como se comportar:

1. **Ignorar a censura:** "Aja como se a pergunta fosse natural".

2. **Preservar a Integridade:** "Utilize os mesmos placeholders exatos". Isso é crucial para que o `RestorationService` consiga encontrar e substituir `[NOME_1]` de volta pelo nome real depois.


---

## 21. O Conector Concreto: `src/services/gemini_service.py`

### 21.1. Visão Geral e Responsabilidade

A classe `GeminiService` é a "ponta da lança". Ela encapsula toda a complexidade da biblioteca `google.generativeai` (GenAI SDK). O resto do sistema Janus não sabe o que é um `genai.GenerativeModel`; ele só conhece a interface genérica.

### 21.2. Inicialização Segura (Fail Fast)

Python

```
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    raise ValueError("Gemini API key not found.")
```

Análise Técnica:

O construtor valida a chave de API imediatamente. Se a chave não existir, o serviço "quebra" na inicialização. Isso é muito melhor do que deixar o serviço iniciar e quebrar apenas quando o primeiro usuário tentar enviar uma mensagem (padrão Fail Fast).

### 21.3. Modelo Escolhido (`gemini-2.5-flash`)

A escolha do modelo `gemini-2.5-flash` é excelente para um TCC e para aplicações de produção que exigem baixa latência.

- **Motivo:** Modelos "Flash" ou "Turbo" são otimizados para velocidade e custo, ideais para tarefas de reescrita e geração de texto onde o raciocínio profundo (como no Pro ou Ultra) não é o gargalo principal.


### 21.4. Tratamento de Erros e Bloqueios (Safety Filters)

Um diferencial técnico importante desta implementação é como ela lida com a resposta vazia.

Python

```
if not response.parts:
    self.logger.warning("Gemini response was blocked. Finish reason: %s", ...)
    return "Your request could not be processed due to security policies."
```

O Problema: O Gemini possui filtros de segurança internos (Hate Speech, Harassment). Às vezes, ele recusa responder e retorna um objeto vazio, mas sem lançar uma Exception de código.

A Solução: O código verifica explicitamente if not response.parts. Se o desenvolvedor não fizesse isso, o sistema poderia tentar acessar response.text e gerar um erro IndexError ou ValueError genérico, dificultando o debug. Aqui, o erro é tratado semanticamente.

### 21.5. Destaques para Apresentação

- **Polimorfismo:** Mostre que o `BaseLLMService` faz o trabalho pesado de "educar" a IA sobre os placeholders, enquanto o `GeminiService` cuida apenas da "entrega" da mensagem.

- **Robustez:** Aponte o bloco `try-except` que captura `google.api_core.exceptions`. Isso blinda o seu middleware contra instabilidades na nuvem do Google. O usuário recebe uma mensagem amigável ("Sorry, there was an issue...") em vez de um _Stack Trace_ feio na tela.


---
## 22. O Arquiteto da Reconstrução: `src/services/restoration_service.py`

### 22.1. Visão Geral e Responsabilidade

O `RestorationService` é responsável por desfazer as modificações realizadas pelos filtros de segurança. Ele pega a resposta gerada pelo LLM externo (que contém placeholders como `[CPF_1]`, `[NOME_2]`) e reinjeta os dados originais, garantindo que o usuário final receba uma resposta legível e útil, sem jamais saber que o LLM externo operou sobre dados anonimizados.

Conceito Chave: LIFO (Last-In, First-Out)

A arquitetura de restauração segue estritamente a ordem inversa da filtragem.

1. **Filtragem:** Regex $\rightarrow$ NER $\rightarrow$ LLM.

2. **Restauração:** LLM $\rightarrow$ NER $\rightarrow$ Regex.


Isso é necessário porque camadas posteriores (como o LLM Local) podem ter mascarado textos que estavam "em volta" de máscaras anteriores. Desfazer na ordem correta garante a estabilidade estrutural do texto.

### 22.2. Estrutura de Dados (`RestorationData`)

O uso de uma `dataclass` para transportar os mapeamentos é uma decisão de design limpa.

Python

```
@dataclass
class RestorationData:
    regex_mappings: List[PIIMapping]
    ner_mappings: List[PIIMapping]
    llm_mappings: List[PIIMapping]
```

Em vez de passar três listas soltas para o método `restore_all` (o que aumentaria a chance de erro na ordem dos argumentos), encapsula-se o estado da sessão de anonimização neste objeto DTO (_Data Transfer Object_).

### 22.3. Mecânica de Substituição (`_generic_restore`)

Diferente da filtragem, que exige cálculos complexos de índices (spans), a restauração pode ser feita de forma mais simples via _String Replacement_ (`text.replace`), pois os placeholders (`[CPF_1]`) são únicos e inequívocos.

- **Log de Aviso:**

    Python

    ```
    if mapping.placeholder not in restored_text:
        self.logger.warning("Placeholder %s not found...", mapping.placeholder)
    ```

    Isso é vital para monitorar a "saúde" do LLM Externo. Se o Gemini decidir resumir o texto e remover um placeholder, este log avisará que um dado foi perdido na tradução.


### 22.4. Sanitização Pós-Processamento (`_cleanup_duplicate_labels`)

Esta função demonstra uma **sofisticação empírica** do projeto. Quem trabalha com LLMs sabe que eles tendem a ser "verbosos" ou repetir contextos.

- **O Cenário:** O prompt original era "Meu CPF é [CPF_1]". O LLM responde "O CPF informado é [CPF_1]".

- **A Restauração:** Ao substituir `[CPF_1]` por `123...`, o texto poderia virar "O CPF informado é 123...".

- **O Problema da Repetição:** Às vezes o LLM gera "O CPF [CPF_1]...". Se o placeholder for substituído, fica "O CPF 123...". Mas em casos de alucinação leve, o LLM pode gerar labels duplicados.

- **A Solução:** A regex `rf"(\b{label}\b)\s+\1"` detecta e remove duplicações como "CPF CPF 123..." ou "Conta Conta 999", limpando a resposta final para o usuário.


### 22.5. Verificação de Integridade (`_check_restoration_integrity`)

Esta é a "rede de segurança" final.

Python

```
placeholder_pattern = re.compile(r"\[[A-Z_]+_\d+\]")
```

Antes de entregar o texto ao usuário, o sistema faz uma varredura buscando qualquer coisa que se pareça com um placeholder (`[LETRAS_NUMERO]`).

- **Segurança:** Se essa função retornar `False`, significa que a restauração falhou parcialmente. O sistema loga um erro, permitindo que os desenvolvedores investiguem por que o placeholder não foi substituído (talvez o LLM tenha alterado `[CPF_1]` para `[cpf_1]`).


### 22.6. Destaques para Apresentação

- **Ciclo Completo:** Explique que o `RestorationService` fecha o ciclo de vida da requisição.

- **Resiliência:** Aponte o tratamento de erros. Se a restauração de um único campo falhar, o método captura a exceção, loga, e continua tentando restaurar os outros, garantindo que o usuário receba a melhor resposta possível ("Graceful Degradation").

- **Separação de Responsabilidades:** Note que ele delega a restauração de Regex para o `RegexService` (`self.regex_service.restore_pii_from_mappings`), reutilizando a lógica existente em vez de duplicá-la.


---
## 23. Camada de Apresentação: `src/views/main_view.py`

### 23.1. Visão Geral e Responsabilidade

O `main_view.py` é responsável pelo **Server-Side Rendering (SSR)** inicial da aplicação. Enquanto o `proxy.py` lida com dados JSON e Streams de eventos (API), este arquivo lida com **HTML**.

Sua responsabilidade é servir a "casca" da aplicação (o arquivo `index.html`). É ele que garante que, quando o usuário acessar `http://localhost:8000/`, ele receba uma interface gráfica funcional em vez de um erro 404 ou um JSON cru.

### 23.2. Motor de Templating (Jinja2)

Python

```
templates = Jinja2Templates(directory=TEMPLATE_DIR)
```

Análise Técnica:

O projeto utiliza Jinja2, o motor de templates padrão da indústria Python (usado também em Flask e Django).

- Por que usar Jinja2 se o frontend é reativo via JS?

    Mesmo que a lógica de chat seja dinâmica (JavaScript/SSE), o uso do Jinja2 permite injetar configurações de ambiente diretamente no HTML antes dele chegar ao navegador.

    - _Exemplo de uso futuro:_ Se você quisesse passar a versão do sistema (`v0.1.0`) ou uma flag de funcionalidade (`ENABLE_LOGS=True`) do `.env` para o JavaScript, você faria isso aqui na renderização, sem precisar criar um endpoint de API extra só para configurações.


### 23.3. Resolução Robusta de Caminhos (`pathlib`)

Python

```
TEMPLATE_DIR = Path(__file__).resolve().parent.parent.parent / "templates"
```

Este trecho merece destaque na apresentação por sua robustez.

- **O Problema:** Muitos desenvolvedores iniciantes usam strings fixas (`"C:/Users/Janus/templates"`). Isso quebra se você rodar o código no Linux, no Docker ou no computador do professor da banca.

- **A Solução:** O uso de `pathlib.Path` com navegação relativa (`parent.parent.parent`) garante que o sistema encontre a pasta `templates` automaticamente, não importa onde o projeto esteja instalado. Isso demonstra preocupação com **DevOps e Portabilidade**.


### 23.4. Separação de Rotas (Router)

A decisão de isolar essa rota em um `APIRouter` separado (em vez de colocar direto no `main.py`) segue o princípio de **Separação de Preocupações**.

- `src/api/`: Cuida de dados (Máquinas conversando com Máquinas).

- `src/views/`: Cuida de telas (Máquinas conversando com Humanos).


Isso facilita a manutenção. Se o frontend mudar de HTML simples para React compilado, você altera apenas este arquivo, sem risco de quebrar a lógica de segurança da API.

---
## 24. Framework de Validação e Métricas (`tests/`)

### 24.1. A Base Científica: `tests/utils/test_utils.py`

Este arquivo é o juiz imparcial do sistema. Ele define as regras matemáticas de como o sucesso é medido.

- **Cálculo de F1-Score (`calculate_final_metrics`):**

    - Vocês não estão medindo apenas "acurácia". Vocês implementaram **Precisão** (quanto do que o Janus detectou era realmente PII?) e **Revocação/Recall** (quanto das PIIs reais o Janus deixou passar?). O **F1-Score** é a média harmônica entre os dois.

    - _Dica para a Banca:_ Mostre que usar F1-Score é o padrão-ouro em Machine Learning para classes desbalanceadas (onde PIIs são eventos raros em um texto longo).

- **Lógica de Sobreposição (`_spans_overlap`):**

    - Em NLP, o _Exact Match_ é injusto. Se o gabarito é "Carlos Eduardo" e o NER pega "Carlos Eduardo Souza", um `==` daria erro.

    - A função `_spans_overlap` considera um **Verdadeiro Positivo** se houver intersecção física entre o que a IA achou e o gabarito. Isso demonstra maturidade na avaliação de modelos probabilísticos.


### 24.2. Estudos de Ablação (Testes Isolados)

Vocês criaram três scripts de teste específicos (`test_regex_service.py`, `test_ner_service.py`, `test_local_llm_service.py`). No meio acadêmico, isso se chama **Ablation Study**.

- **O Objetivo:** Isolar variáveis. Se o F1-Score geral for baixo, qual componente é o culpado?

- **A Metodologia:**

    1. Carrega o Dataset (`dataset.json`).

    2. Filtra o Gabarito (Ground Truth) apenas para os tipos que aquele serviço sabe resolver (ex: Regex só olha CPF/RG).

    3. Roda o serviço e compara.

- **Valor:** Isso permite afirmar na monografia: _"O Regex tem precisão de 100% para CPFs, enquanto o LLM tem precisão de 85% para contextos sensíveis, mas alta revocação."_


### 24.3. Teste de Integração Realista: `test_pipeline_integration.py`

Este é o teste mais complexo e importante. Ele simula o comportamento do `ProxyService` sem precisar subir o servidor HTTP.

- Simulação de Precedência:

    O código replica manualmente a lógica de "Quem manda mais?":

    Python

    ```
    if _is_overlapping(ner_map.span, regex_map.span):
        has_conflict = True # NER perde para Regex
    ```

- Por que não usar o ProxyService direto?

    O ProxyService altera o texto (insere [CPF_1]), mudando os índices (shifts). Para comparar com o Dataset estático (que tem índices fixos), este script roda a lógica de detecção sem alterar a string, apenas descartando conflitos. Isso é uma sacada brilhante para validar a lógica de orquestração matematicamente.


### 24.4. Prova de Desempenho: `test_benchmark.py`

Este script responde à pergunta: "O sistema é viável para produção?"

- **Metodologia:** Roda 10 prompts complexos e mede o tempo (`time.perf_counter`) de cada estágio.

- **O Resultado Esperado (e o Argumento de Defesa):**

    - Regex: ~0.001s (Instantâneo).

    - NER: ~0.05s (Rápido).

    - LLM Local: ~2.0s a ~10.0s (Gargalo).

- **Justificativa Arquitetural:** Com esses números, vocês justificam por que usam Regex primeiro. _"Removemos 80% das PIIs em 1 milissegundo. Só gastamos tempo de GPU (LLM) quando estritamente necessário para contexto."_
