![Conecta.ai Logo](./routers/application/img/logo.png)

## Automotive Chatbot API
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110.0-black.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10-black.svg)](https://www.python.org/)
[![Docker](https://img.shields.io/badge/Docker-6.0.1-black.svg)](https://www.docker.com/)
[![Milvus](https://img.shields.io/badge/Milvus-2.4.0-black.svg)](https://milvus.io/)

This repository contains the source code for the Automotive Chatbot API. The API is built using FastAPI and Python, and it uses Milvus for similarity search. The API is designed to provide responses to user queries related to automotive manuals.

### Features
- **FastAPI**: FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.7+ based on standard Python type hints.
- **Milvus**: Milvus is an open-source vector database that provides similar search capabilities for massive-scale datasets.
- **Docker**: Docker is a platform for developing, shipping, and running applications in containers.

You need to have Docker installed on your machine to run this project. If you don't have Docker installed, you can download it from the [official website](https://www.docker.com/).

### Installation
1. Clone the repository:
    ```bash
    git clone https://github.com/conect2ai/auto-bot-api.git
    ```
2. Change the directory:
    ```bash
    cd auto-bot-api
    ```
3. Execute the following command to build the Docker image and run the API:
    ```bash
    docker-compose up --build api
    ```
4. The API will be available at `http://localhost:8000/docs`.
5. In addition, a Streamlit application will be available at `http://localhost:8501`, which can be used to interact with the API. 

When uploading an automotive manual in PDF format, it should be named in the format `Brand_Model_Year.pdf`. For example, `Volkswagen_Polo_2020.pdf`.

### External Dependencies and Setup
- **OpenAI API Key**: This API uses the OpenAI API to perform some of its operations. To use these features, you'll need to:
  1. Create an account at [OpenAI](https://www.openai.com/).
  2. Follow the instructions to apply for API access.
  3. Once approved, generate an API key from your OpenAI account dashboard.
  4. Store this key securely and use it in your API requests as shown in the endpoints that require authentication.
  5. Note that OpenAI services may incur costs based on usage. Please review OpenAI's pricing details to manage your usage according to your budget.

### API Endpoints Documentation
The API provides the following endpoints:

#### Endpoint: GET /get_stored_cars

This endpoint fetches a list of stored cars from the Milvus vector database, organized by brand, model, and year. It is designed to provide a quick lookup for the available car data in the database.

##### Workflow
1. **Connection**: Connects to Milvus using the specified URI.
2. **Check Collection**: Checks if the collection exists. Returns an error if it does not.
3. **Query Data**: Executes a query to fetch entries where the `brand` field is not empty, collecting the `brand`, `model`, and `year` fields.
4. **Organize Data**: Structures the response to group years under models, which are grouped under brands.

##### Response Format
- **Success** (Status Code: 200): Returns data structured by brand, model, and year:
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

- **Failure** (Status Code: 400): If the collection does not exist:
  ```json
  {
    "message": "Collection COLLECTION_NAME does not exist",
    "status_code": 400
  }
  ```

---

#### Endpoint: POST /answer_question_audio

Converts spoken queries into text and then generates answers based on the transcribed text using a knowledge base. This endpoint is suitable for voice-activated systems where users can ask questions about car specifications via audio.

##### Workflow
1. **Receive Audio**: Accepts an audio file and optional parameters (brand, model, year) of a car.
2. **Extract Audio Content**: Reads the content of the uploaded audio file.
3. **Transcription**: Converts the audio content into text using a speech-to-text function which involves:
   - Writing the audio to a temporary file.
   - Transcribing the audio using a machine learning model (e.g., Whisper).
   - Deleting temporary files post transcription.
4. **Query Knowledge Base**: Uses the transcribed text to query a knowledge base with specifics about the car (brand, model, year) provided by the user.
5. **Generate Response**: Returns the query answer, extracted from the knowledge base using the transcribed text as input.

##### Parameters
- `audio_file` (UploadFile): The audio file containing the spoken query.
- `brand` (str, optional): The brand of the car.
- `model` (str, optional): The model of the car.
- `year` (str, optional): The year of the car.
- `authorization` (Header): Bearer token required for OpenAI API access.

##### Response Format
- **Success** (Status Code: 200): Returns the transcribed text and the response content based on the query:
  ```json
  {
    "text": "What is the fuel efficiency of the model?",
    "response_content": "The fuel efficiency of the model is 28 miles per gallon.",
    "status_code": 200
  }
  ```

- **Failure** (Status Code: 500): In case of errors, returns an error message:
  ```json
  {
    "message": "Error description",
    "status_code": 500
  }
  ```

---

#### Endpoint: POST /knowledge_base

This endpoint retrieves information about the existing knowledge base stored in the Milvus vector database. It verifies the presence of the specified collection and provides details about it, ensuring that the user has the appropriate credentials to access this data.

##### Workflow
1. **Authorization Check**: Ensures that an authorization header with a valid OpenAI API key is included in the request.
2. **Verify Collection**: Checks if the specified collection exists in the Milvus database.
3. **Knowledge Base Retrieval**: If the collection exists, initializes the knowledge base using the specified embeddings and connection parameters. If not, it returns an indication that the knowledge base is unavailable.

##### Parameters
- `authorization` (Header): Bearer token required for authentication and authorization. It's essential for accessing the protected resources.

##### Response Format
- **Success** (Status Code: 200): Returns a message confirming access to the knowledge base:
  ```json
  {
    "knowledge_base": "Available",
    "status_code": 200
  }
  ```
- **Failure** (Status Code: 401): If the authorization header is not provided:
  ```json
  {
    "message": "Authorization header not provided.",
    "status_code": 401
  }
  ```

---

#### Endpoint: GET /collection_exists

This endpoint checks if a specific collection exists within the Milvus vector database server. It is designed to quickly verify the presence of a collection by its name.

##### Workflow
1. **Check Collection Presence**: Queries the Milvus server to determine if the specified collection is available.

##### Parameters
- `collection_name` (Query Parameter): The name of the collection you want to check.

##### Response Format
- **Success** (Status Code: 200): Returns a boolean indicating whether the collection exists:
  ```json
  {
    "exists": true,  // or false, depending on the presence of the collection
    "status_code": 200
  }
  ```

---

#### Endpoint: POST /clear_collection

This endpoint is responsible for deleting all data within a specific collection on the Milvus vector database server. It's used to clear a collection to refresh its content or to manage data storage efficiently.

##### Workflow
1. **Clear Collection**: Initiates a command to drop or delete the specified collection from the Milvus server using its internal utility functions.

##### Response Format
- **Success** (Status Code: 200): Returns a confirmation that the collection has been successfully cleared:
  ```json
  {
    "message": "Collection COLLECTION_NAME cleared",
    "status_code": 200
  }
  ```

---

#### Endpoint: POST /export_chat_to_pdf

This endpoint is designed to export chat history into a PDF format. It takes the chat messages as input and generates a PDF document, which is then encoded in base64 format for easy transmission over HTTP. This functionality is crucial for archiving conversations or providing users with downloadable chat transcripts.

##### Workflow
1. **Prepare Data**: Extracts all chat messages provided in the request data under the key 'all_messages'.
2. **Create PDF**: Utilizes the ReportLab library to format the text and create a PDF document:
   - Sets up a PDF template with standard page size and margins.
   - Adds chat messages, alternating between user and assistant messages.
   - Inserts spacers for readability.
3. **Encode PDF**: Converts the generated PDF into a base64-encoded string to facilitate easy embedding or downloading through web interfaces.

##### Parameters
- `data` (JSON Body): A dictionary containing a list of chat messages. Each message should include the sender's role and the message text.

##### Response Format
- **Success** (Status Code: 200): Returns a base64-encoded string of the PDF file along with the list of all messages included in the PDF:
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

This endpoint processes uploaded PDF files to extract text and create a knowledge base. It uses the text extracted from the PDFs to enhance an existing knowledge base or to create a new one, integrating vehicle-specific information like brand, model, and year from the file names.

##### Workflow
1. **Authentication Check**: Verifies the presence of an authorization header with a valid API key.
2. **PDF File Validation**: Checks if PDF files are provided in the request.
3. **PDF Processing**:
   - Temporarily saves each PDF to a designated directory.
   - Extracts text from each PDF file.
   - Parses vehicle-related metadata from the file name.
   - Splits the extracted text into manageable chunks.
   - Applies text embeddings using the OpenAI API.
4. **Knowledge Base Integration**:
   - If a knowledge base already exists, updates it with the new text and metadata.
   - If no knowledge base exists, creates a new one with the processed data.

##### Parameters
- `authorization` (Header): Required. Bearer token for API access.
- `pdfs` (List[UploadFile]): Required. List of PDF files to be processed.

##### Response Format
- **Success** (Status Code: 200): Returns a message indicating successful processing of the PDFs:
  ```json
  {
    "message": "PDFs processed. You may now ask questions.",
    "status_code": 200
  }
  ```
- **Failure**:
  - If the authorization header is missing (Status Code: 401):
    ```json
    {
      "message": "Authorization header not provided.",
      "status_code": 401
    }
    ```
  - If no PDF files are provided (Status Code: 400):
    ```json
    {
      "message": "No PDF files provided.",
      "status_code": 400
    }
    ```

---

#### Endpoint: POST /answer_question_image

This endpoint allows users to ask a question about an image and receive an answer using the knowledge base and image processing capabilities. It integrates advanced AI models to interpret the content of the image and generate a relevant response based on both the visual and textual input.

##### Workflow
1. **Authorization Check**: Ensures an authorization header with a valid API key is present.
2. **Validate Inputs**: Confirms that both an image file and a question are provided.
3. **Image Processing**:
   - The image file is asynchronously read and encoded into a base64 string.
4. **Request Setup**:
   - Prepares a payload that includes the question and the encoded image, formatted for AI processing.
5. **AI Processing**:
   - Sends a request to the OpenAI API with the question and image data.
   - Receives the AI's response to the query based on the combined interpretation of the text and image.
6. **Return Response**: Delivers the AI-generated answer as a JSON response.

##### Parameters
- `authorization` (Header): Required. Bearer token for API access.
- `image_file` (UploadFile): Required. Image file related to the question.
- `question` (String): Required. Textual question about the image.

##### Response Format
- **Success** (Returns JSONResponse): Delivers the answer along with the status code:
  ```json
  {
    "answer": "Here is the answer based on the image analysis.",
    "status_code": 200
  }
  ```
- **Failure**:
  - If authorization is missing (Status Code: 401):
    ```json
    {
      "message": "Authorization header not provided.",
      "status_code": 401
    }
    ```
  - If the question is missing (Status Code: 400):
    ```json
    {
      "message": "Question not provided.",
      "status_code": 400
    }
    ```

---

#### Endpoint: POST /answer_question

This endpoint allows users to submit a question about a specific car model and year using a structured format, and retrieves an answer from a knowledge base. It is designed to handle queries related to automotive information that has been stored and processed in the system's knowledge base.

##### Workflow
1. **Authorization Check**: Validates the presence of an authorization header containing a valid API key.
2. **Validate Parameters**: Ensures that all necessary parameters (brand, model, year, question) are included.
3. **Generate Answer**:
   - Uses the provided parameters to query the knowledge base.
   - Leverages previously integrated data to generate a comprehensive response.
4. **Return Response**: Provides the generated answer as part of the response body.

##### Parameters
- `params` (QuestionParams): A data structure that includes `brand`, `model`, `year`, and `question`. All fields are required to tailor the query to the user's specific needs.
- `authorization` (Header): Required. Bearer token for API access.

##### Response Format
- **Success** (Status Code: 200): Returns the generated answer:
  ```json
  {
    "response_content": "Here is the detailed answer based on the knowledge base.",
    "status_code": 200
  }
  ```
- **Failure**:
  - If the authorization header is missing (Status Code: 401):
    ```json
    {
      "message": "Authorization header not provided.",
      "status_code": 401
    }
    ```

### License
This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details.