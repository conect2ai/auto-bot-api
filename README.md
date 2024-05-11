![Conecta.ai Logo](./img/logo.jpg)

## API - Chatbot Automotivo
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-black.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10-black.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-6.0.1-black.svg)](https://www.docker.com/)
[![Milvus](https://img.shields.io/badge/Milvus-2.4.0-black.svg)](https://milvus.io/)

Este repositório contém o código-fonte para a API de Chatbot Automotivo. A API foi construída utilizando FastAPI e Python, e usa Milvus para busca de similaridade. A API é projetada para fornecer respostas a consultas de usuários relacionadas a manuais automotivos.

### Funcionalidades
- **FastAPI**: framework web moderno e rápido (de alta performance) para a construção de APIs com Python 3.7+;
- **Milvus**: banco de dados vetorial de código aberto que fornece capacidades de busca por similaridade para conjuntos de dados de grande escala;
- **Docker**: plataforma de código aberto que facilita a criação, implantação e execução de alicações em contêineres.

Você precisa ter o Docker instalado em sua máquina para executar este projeto. Se você não tem o Docker instalado, pode baixá-lo no [site oficial](https://www.docker.com/).

### Aplicação Flutter
O Aplicativo Flutter que interage com esta API pode ser encontrado [aqui](https://github.com/conect2ai/search_app).

### Instalação e Execução
1. Clone o repositório:
    ```bash
    git clone https://github.com/conect2ai/auto-bot-api.git
    ```
2. Mude para o diretório do projeto:
    ```bash
    cd auto-bot-api
    ```
3. Execute o seguinte comando para construir e iniciar a API:
    ```bash
    docker-compose up --build api
    ```
4. A API estará disponível em `http://localhost:8000`. Você pode acessar a documentação da API em `http://localhost:8000/docs` ou `http://localhost:8000/redoc`.
5. Além disso, a aplicação Streamlit estará disponível em `http://localhost:8501`, que pode ser usada para interagir com a API.

Quando você fizer o upload de um manual automotivo no formato PDF, ele deve ser nomeado no formato `Marca_Modelo_Ano.pdf`. Por exemplo, `Volkswagen_Polo_2020.pdf`.

### Dependências Externas e Configuração
- **OpenAI API Key**: a API usa a API OpenAI para realizar algumas de suas operações. Para usar esses recursos, você precisará:
  1. Criar uma conta em [OpenAI](https://www.openai.com/).
  2. Seguir as instruções para solicitar acesso à API.
  3. Uma vez aprovado, gerar uma chave de API no painel da sua conta OpenAI.
  4. Armazenar essa chave de forma segura e usá-la em suas solicitações de API conforme mostrado nos endpoints que requerem autenticação.
  5. Observe que os serviços da OpenAI podem incorrer em custos com base no uso.

### Documentação dos Endpoints da API
A API fornece os seguintes endpoints:

#### Endpoint: GET /get_stored_cars

Este endpoint busca uma lista de carros armazenados no banco de dados vetorial Milvus, organizados por marca, modelo e ano. Ele é projetado para fornecer uma rápida consulta para os dados de carros disponíveis no banco de dados.

##### Fluxo de Trabalho
1. **Conexão**: conecta-se ao Milvus.
2. **Verificar Coleção**: verifica se a coleção existe. Retorna um erro se não existir.
3. **Consultar Dados**: executa uma consulta para buscar entradas onde o campo `brand` não está vazio, coletando os campos `brand`, `model` e `year`.
4. **Organizar Dados**: estrutura a resposta para agrupar anos sob modelos, que são agrupados sob marcas.

##### Formato da Resposta
- **Sucesso** (Código de Status: 200) - retorna dados estruturados por marca, modelo e ano:
  ```json
  {
    "message": {
      "Toyota": {
        "Corolla": ["2020", "2021"],
        "Camry": ["2019"]
      },
      "Ford": {
        "Fiesta": ["2018", "2019"]
      }
    },
    "status_code": 200
  }
  ```

- **Falha** (Código de Status: 400) - se a coleção não existir:
  ```json
  {
    "message": "Collection COLLECTION_NAME does not exist",
    "status_code": 400
  }
  ```

---

#### Endpoint: POST /answer_question_audio
Converte consultas faladas em texto e, em seguida, gera respostas com base no texto transcrito usando uma base de conhecimento. Este endpoint é adequado para sistemas ativados por voz, em que os usuários podem fazer perguntas sobre especificações de carros via áudio.

##### Fluxo de Trabalho
1. **Receber Áudio**: aceita um arquivo de áudio.
2. **Extrair Conteúdo de Áudio**: lê o conteúdo do arquivo de áudio enviado.
3. **Transcrição**: converte o conteúdo de áudio em texto usando uma função de fala para texto que envolve:
   - Escrever o áudio em um arquivo temporário.
   - Transcrever o áudio usando o modelo Faster Whisper.
   - Excluir arquivos temporários após a transcrição.
4. **Consultar Base de Conhecimento**: usa o texto transcrito para consultar uma base de conhecimento com detalhes sobre o carro (marca, modelo, ano) fornecidos pelo usuário.
5. **Gerar Resposta**: retorna a resposta da consulta, extraída da base de conhecimento usando o texto transcrito como entrada.

##### Parâmetros
- `audio_file` (UploadFile): o arquivo de áudio contendo a consulta falada;
- `brand` (str, opcional): a marca do carro;
- `model` (str, opcional): o modelo do carro;
- `year` (str, opcional): o ano do carro;
- `authorization` (Header): token de autorização necessário para acessar a API OpenAI.

##### Formato da Resposta
- **Sucesso** (Código de Status: 200) - retorna o texto transcrito e o conteúdo da resposta com base na consulta:
  ```json
  {
    "text": "Qual é a eficiência de combustível do modelo?",
    "response_content": "A eficiência de combustível do modelo é de 20 km por hora.",
    "status_code": 200
  }
  ```
- **Falha** (Código de Status: 400) - em caso de erro, retorna uma mensagem de erro:
  ```json
  {
    "message": "No audio file provided.",
    "status_code": 400
  }
  ```

---

#### Endpoint: POST /knowledge_base

O endpoint recupera informações sobre a base de conhecimento existente armazenada no banco de dados vetorial Milvus. Ele verifica a presença da coleção especificada.

##### Fluxo de Trabalho
1. **Verificação de Autorização**: garante que um cabeçalho de autorização com uma chave de API OpenAI válida esteja incluído na solicitação;
2. **Verificar Coleção**: verifica se a coleção especificada existe no banco de dados Milvus;
3. **Recuperação da Base de Conhecimento**: se a coleção existir, inicializa a base de conhecimento usando os embeddings e os parâmetros de conexão especificados. Caso contrário, retorna uma indicação de que a base de conhecimento não está disponível.

##### Parâmetros
- `authorization` (Header): token Bearer necessário para autenticação e autorização.

##### Formato da Resposta
- **Sucesso** (Código de Status: 200) - retorna uma mensagem confirmando o acesso à base de conhecimento:
  ```json
  {
    "knowledge_base": "Available",
    "status_code": 200
  }
  ```
- **Falha** (Código de Status: 401) - se o cabeçalho de autorização não for fornecido:
  ```json
  {
    "message": "Authorization header not provided.",
    "status_code": 401
  }
  ```

---

#### Endpoint: GET /collection_exists

O endpoint verifica se uma coleção específica existe no banco de dados vetorial Milvus. 

##### Fluxo de Trabalho
1. **Verificar Presença da Coleção**: consulta o Milvus para determinar se a coleção especificada está disponível.

##### Parâmetros
- `collection_name` (Parâmetro de Consulta): o nome da coleção que você deseja verificar.

##### Formato da Resposta
- **Sucesso** (Código de Status: 200) - retorna um booleano indicando se a coleção existe:
  ```json
  {
    "exists": true,  // ou false, dependendo da presença da coleção
    "status_code": 200
  }
  ```

---

#### Endpoint: POST /clear_collection

O endpoint é responsável por excluir todos os dados dentro de uma coleção específica no banco de dados vetorial Milvus. É usado para limpar uma coleção para atualizar seu conteúdo ou para gerenciar o armazenamento de dados.

##### Fluxo de Trabalho
1. **Limpar Coleção**: inicia um comando para excluir a coleção especificada do servidor Milvus usando suas funções internas de utilitário.

##### Formato da Resposta
- **Sucesso** (Código de Status: 200) - retorna uma confirmação de que a coleção foi limpa com sucesso:
  ```json
  {
    "message": "Collection COLLECTION_NAME cleared",
    "status_code": 200
  }
  ```

---

#### Endpoint: POST /export_chat_to_pdf

Este endpoint é projetado para exportar o histórico de chat para um formato PDF. Ele recebe as mensagens do chat como entrada e gera um documento PDF, que é então codificado no formato base 64 para facilitar a transmissão via HTTP.

##### Fluxo de Trabalho
1. **Preparar Dados**: extrai todas as mensagens do chat fornecidas nos dados da solicitação sob a chave 'all_messages'.
2. **Criar PDF**: utiliza a biblioteca ReportLab para formatar o texto e criar um documento PDF:
   - Configura um modelo PDF com tamanho de página padrão e margens;
   - Adiciona mensagens de chat, alternando entre mensagens de usuário e assistente;
   - Insere espaçadores para legibilidade.
3. **Codificar PDF**: converte o PDF gerado em uma string codificada em base64 para facilitar a incorporação ou download.

##### Parâmetros
- `data` (JSON Body): um dicionário contendo uma lista de mensagens de chat. Cada mensagem deve incluir o papel do remetente e o texto da mensagem.

##### Formato da Resposta
- **Sucesso** (Código de Status: 200) - retorna uma string codificada em base64 do PDF gerado com as mensagens de chat:
  ```json
  {
    "pdf_bytes": "base64_encoded_string_of_the_PDF",
    "all_messages": [
      {"role": "User", "message": "Hello, how can I help you?"},
      {"role": "Assistant", "message": "I need information about my car status."}
    ],
    "status_code": 200
  }
  ```

---

#### Endpoint: POST /process_pdf

Este endpoint processa arquivos PDF enviados para extrair texto e criar uma base de conhecimento. Ele usa o texto extraído dos PDFs para aprimorar uma base de conhecimento existente ou criar uma nova, integrando informações específicas do veículo, como marca, modelo e ano dos nomes dos arquivos.

##### Fluxo de Trabalho
1. **Verificação de Autenticação**: verifica a presença de um cabeçalho de autorização com uma chave de API válida.
2. **Validação de Arquivos PDF**: verifica se os arquivos PDF são fornecidos na solicitação.
3. **Processamento de PDF**:
   - Salva temporariamente cada PDF em um diretório designado;
   - Extrai texto de cada arquivo PDF;
   - Analisa metadados relacionados ao veículo do nome do arquivo;
   - Divide o texto extraído em partes gerenciáveis;
   - Aplica incorporações de texto usando a API OpenAI.
4. **Integração com a Base de Conhecimento**:
    - Se uma base de conhecimento já existir, a atualiza com o novo texto e metadados;
    - Se nenhuma base de conhecimento existir, cria uma nova com os dados processados.

##### Parâmetros
- `authorization` (Header): obrigatório. Token Bearer para acesso à API.
- `pdfs` (Lista[UploadFile]): obrigatório. Lista de arquivos PDF a serem processados.

##### Formato da Resposta
- **Sucesso** (Código de Status: 200) - retorna uma mensagem indicando o processamento bem-sucedido dos PDFs:
  ```json
  {
    "message": "PDFs processed. You may now ask questions.",
    "status_code": 200
  }
  ```
- **Falha**:
  - Se o cabeçalho de autorização estiver ausente (Código de Status: 401):
    ```json
    {
      "message": "Authorization header not provided.",
      "status_code": 401
    }
    ```
  - Se nenhum arquivo PDF for fornecido (Código de Status: 400):
    ```json
    {
      "message": "No PDF files provided.",
      "status_code": 400
    }
    ```

---

#### Endpoint: POST /answer_question_image

Este endpoint permite que os usuários façam uma pergunta sobre uma imagem e recebam uma resposta. Ele é projetado para lidar com consultas relacionadas a imagens e texto, fornecendo respostas com base na interpretação combinada da imagem e da pergunta.

##### Fluxo de Trabalho
1. **Verificação de Autorização**: garante que um cabeçalho de autorização com uma chave de API válida esteja incluído na solicitação.
2. **Validar Entradas**: confirma se um arquivo de imagem e uma pergunta são fornecidos.
3. **Processamento de Imagem**:
   - O arquivo de imagem é lido e codificado de forma assíncrona em uma string base64.
4. **Configuração da Solicitação**:
    - Prepara uma carga útil que inclui a pergunta e a imagem codificada, formatada para processamento de IA.
5. **Processamento de IA**:
    - Envia uma solicitação à API OpenAI com a pergunta e os dados da imagem;
    - Recebe a resposta da IA à consulta com base na interpretação combinada do texto e da imagem.
6. **Retornar Resposta**: entrega a resposta gerada pela IA como parte da resposta JSON.

##### Parâmetros
- `authorization` (Header): obrigatório. Token Bearer para acesso à API.
- `image_file` (UploadFile): obrigatório. Arquivo de imagem relacionado à pergunta.
- `question` (String): obrigatório. Pergunta textual sobre a imagem.

##### Formato da Resposta
- **Sucesso** (Retorna JSONResponse) - entrega a resposta juntamente com o código de status:
  ```json
  {
    "answer": "Aqui está a resposta com base na análise da imagem.",
    "status_code": 200
  }
  ```
- **Falha**: 
  - Se a autorização estiver ausente (Código de Status: 401):
    ```json
    {
      "message": "Authorization header not provided.",
      "status_code": 401
    }
    ```
  - Se a pergunta estiver ausente (Código de Status: 400):
    ```json
    {
      "message": "Question not provided.",
      "status_code": 400
    }
    ```

##### Response Format
- **Success** (Returns JSONResponse): Delivers the answer along with the status code:
  ```json
  {
    "answer": "Here is the answer based on the image analysis.",
    "status_code": 200
  }
  ```

---

#### Endpoint: POST /answer_question

Este endpoint permite que os usuários enviem uma pergunta com base em modelo, marca e ano de carro específicos usando um formato estruturado e recuperem uma resposta de uma base de conhecimento.

##### Fluxo de Trabalho
1. **Verificação de Autorização**: garante que um cabeçalho de autorização com uma chave de API válida esteja incluído na solicitação.
2. **Validar Parâmetros**: confirma se todos os parâmetros necessários (marca, modelo, ano, pergunta) estão incluídos.
3. **Gerar Resposta**:
   - Usa os parâmetros fornecidos para consultar a base de conhecimento;
   - Alavanca dados previamente integrados para gerar uma resposta abrangente.
4. **Retornar Resposta**: fornece a resposta gerada como parte do corpo da resposta.

##### Parâmetros
- `params` (QuestionParams): uma estrutura de dados que inclui `brand`, `model`, `year`, e `question`. Todos os campos são necessários para adaptar a consulta às necessidades específicas do usuário.
- `authorization` (Header): obrigatório. Token Bearer para acesso à API.

##### Formato da Resposta
- **Sucesso** (Retorna JSONResponse) - entrega a resposta juntamente com o código de status:
  ```json
  {
    "response_content": "Here is the detailed answer based on the knowledge base.",
    "status_code": 200
  }
  ```
- **Falha**:
  - Se a autorização estiver ausente (Código de Status: 401):
    ```json
    {
      "message": "Authorization header not provided.",
      "status_code": 401
    }
    ```

### License
This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.
