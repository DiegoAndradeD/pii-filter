# pii-filter

![Python](https://img.shields.io/badge/python-3.13.7+-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-v0.110.0-brightgreen)
![License](https://img.shields.io/badge/license-GPL-yellow)

PII Filter API

Este é um projeto desenvolvido para o Trabalho de Conclusão de Curso (TCC) do curso de Engenharia de Software da [**Universidade Católica do Salvador - UCSal**](https://www.ucsal.br/). O objetivo é desenvolver um sistema de proxy, na forma de uma API, para garantir o uso seguro de Modelos de Linguagem de Grande Escala (LLMs), através da detecção e mascaramento de Informações Pessoalmente Identificáveis (PII) em língua portuguesa, em conformidade com a Lei Geral de Proteção de Dados (LGPD).

---

## 🎯 Problema

### Problema Geral

A utilização de LLMs em ambientes corporativos apresenta um risco significativo de vazamento de dados sensíveis. Prompts contendo PII como CPFs, nomes completos, e-mails e outros dados podem ser enviados a serviços de terceiros, violando políticas de privacidade e a LGPD.

### Domínio Aplicado: Recursos Humanos (RH)

No domínio de **Recursos Humanos**, a manipulação de dados pessoais de colaboradores é crítica. Dados como CPFs, endereços, contatos, histórico de desempenho e informações financeiras são frequentemente processados, e qualquer vazamento pode ter consequências legais e reputacionais significativas. Portanto, a proteção desses dados exige uma abordagem rigorosa e especializada.

---

## 🛠️ Solução Proposta

Este projeto implementa uma API REST que atua como uma camada de segurança intermediária. A API recebe um prompt de texto, aplica uma pipeline de filtros modulares para sanitizar os dados e, em seguida, interage com o LLM externo.

A arquitetura de filtros é dividida em três estágios:

1. **Filtro por Regras (Regex)**: Detecção de PII com padrões bem definidos (CPF, e-mail, telefone, etc.).
2. **Filtro por Reconhecimento de Entidades (NER)**: Detecção de PII sem padrão fixo (nomes, locais, organizações) usando modelos de Machine Learning e Reconhecimento de Entidade Nomeada (NER) .
3. **Filtro de Tópicos Sensíveis**: Identificação de contextos sensíveis (jurídico, financeiro, saúde) utilizando um LLM local para garantir a conformidade com a LGPD.

---

## 🚀 Tecnologias Utilizadas

- **Linguagem**: Python 3.13.7+
- **Framework da API**: FastAPI
- **Validação de Dados**: Pydantic V2
- **Servidor ASGI**: Uvicorn

---

## ⚙️ Como Rodar o Projeto Localmente

Siga os passos abaixo para configurar e executar a API na sua máquina.

### 1. Pré-requisitos

- Python 3.13.7 ou superior instalado
- Git

### 2. Clone o Repositório

```bash
git clone git@github.com:DiegoAndradeD/pii-filter.git
cd pii-filter
````

### 3. Crie e Ative o Ambiente Virtual

Para garantir que as dependências do projeto não conflitem com outras instalações do sistema, recomenda-se criar um ambiente virtual isolado. Isso mantém todas as bibliotecas do projeto separadas e facilita o gerenciamento de versões.


**No macOS/Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
```

**No Windows:**

```bash
python -m venv venv
.\venv\Scripts\activate
```

### 4. Instale as Dependências

Instale todas as bibliotecas necessárias listadas no arquivo `requirements.txt`.

```bash
pip install -r requirements.txt
```

> Nota: Se o arquivo `requirements.txt` ainda não existir, crie-o com:

```bash
pip freeze > requirements.txt
```

### 5. Execute o Servidor

Com o ambiente virtual ativado, inicie o servidor Uvicorn:

```bash
uvicorn main:app --reload
```

* `main`: refere-se ao arquivo `main.py`.
* `app`: refere-se ao objeto `app = FastAPI()` criado no arquivo.
* `--reload`: reinicia o servidor automaticamente após qualquer alteração no código.

A API estará rodando em: `http://127.0.0.1:8000`.

---

## 📚 Como Usar a API

Após iniciar o servidor, a maneira mais fácil de interagir com a API é através da documentação interativa gerada automaticamente.

1. Abra seu navegador e acesse: `http://127.0.0.1:8000/docs`
2. Você verá a interface do **Swagger UI** com todos os endpoints disponíveis.
3. Clique no endpoint **POST /process-prompt** para expandi-lo.
4. Clique em **Try it out**.
5. Modifique o corpo da requisição (JSON) com o prompt que deseja testar. Por exemplo:

```json
{
  "prompt_original": "O CPF do cliente é 123.456.789-00 e ele precisa de ajuda."
}
```

6. Clique em **Execute** para ver a resposta da API.

---

## 📖 Referências

Para auxiliar no desenvolvimento e entendimento do projeto, listamos abaixo links de documentação e ferramentas importantes.

---

### Essenciais (Leitura Obrigatória)

- **[FastAPI – Documentação Oficial](https://fastapi.tiangolo.com/)**
  Principal referência para o backend do projeto.

- **[Pydantic V2 – Documentação Oficial](https://docs.pydantic.dev/latest/)**
  Biblioteca utilizada pelo FastAPI para validação e serialização de dados.

---

### Linguagem e Módulos Padrão

- **[Python 3 – Documentação Oficial](https://docs.python.org/3/)**
  Fonte oficial para qualquer dúvida sobre a linguagem.

- **[Módulo `re` do Python](https://docs.python.org/3/library/re.html)**
  Essencial para a implementação do filtro por Regex (`regex_filter.py`).

---

### Ferramentas e Ambiente

- **[Uvicorn – Servidor ASGI](https://www.uvicorn.org/)**
  Motor que executa a aplicação FastAPI.

- **[Ambientes Virtuais (`venv`)](https://docs.python.org/3/library/venv.html)**
  Explica como criar e gerenciar ambientes virtuais, garantindo que as dependências do projeto fiquem isoladas.

---

### Ferramenta Bônus

- **[Regex101 – Testador de Regex Online](https://regex101.com/)**
  Ferramenta online para construir, testar e depurar expressões regulares.

---

### Geração de Dados Mockados

- **[4Devs – Geradores de Dados Online](https://www.4devs.com.br/)**
  Ferramenta online gratuita que oferece diversos geradores de dados, como CPF, CNPJ, RG, entre outros.

- **[Fordev – Módulo Python para 4Devs](https://fordev.readthedocs.io/)**
  Biblioteca Python que mapeia os geradores do 4Devs, permitindo a geração de dados diretamente no código.

- **[Faker – Biblioteca Python para Dados Falsos](https://faker.readthedocs.io/)**
  Biblioteca Python para geração de dados falsos, como nomes, endereços, e-mails, entre outros.

## 📰 Artigos e Textos Úteis

Além da documentação oficial, estes são alguns dos textos e artigos consultados para a implementação do projeto, incluindo tutoriais e guias da comunidade que oferecem diferentes perspectivas sobre Python, FastAPI, Pydantic, Regex, sanitização, desanitização, filtragem, PII, LLMs e organização de projetos.

---

### FastAPI e Pydantic (Tutoriais Práticos)

- **[Como Criar sua Primeira API com FastAPI (Data Hackers - PT-BR)](https://medium.com/data-hackers/como-criar-a-sua-primeira-api-em-python-com-o-fastapi-50b1d7f5bb6d)**

- **[FastAPI and Pydantic: A Powerful Duo (Inglês)](https://data-ai.theodo.com/en/technical-blog/fastapi-pydantic-powerful-duo)**

---

### Estrutura de Projetos FastAPI

- **[Guia de Estrutura de Projetos FastAPI (Medium - Inglês)](https://medium.com/@vignarajj/build-fast-scale-smart-the-ultimate-fastapi-project-structure-guide-dc41c35f64cd)**

---

### Expressões Regulares (Regex) em Python

- **[Python Regex Cheat Sheet (Dataquest - Inglês)](https://www.dataquest.io/cheat-sheet/regular-expressions-cheat-sheet/)**

- **[Tutorial de Expressões Regulares em Python (Google for Developers - Inglês)](https://developers.google.com/edu/python/regular-expressions)**

---

## 👥 Equipe

* \[DIEGO ANDRADE DEIRO]
* \[DENILSON XAVIER OLIVEIRA]
* \[JOÃO VICTOR AZIZ LIMA DE SANTANA]
* \[LOREN VITORIA CAVALCANTE SANTOS]
* \[NEILLANE DE CARVALHO SÁ BARRETO DO ROSARIO]

---

## 📄 Licença

Este projeto está licenciado sob a **GNU General Public License (GPL) v3**.
Veja o arquivo [LICENSE](LICENSE) para mais detalhes.
