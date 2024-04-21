import os
import base64
from base64 import b64encode
import requests
from io import BytesIO
from fastapi import APIRouter, File, UploadFile, HTTPException, Header
from fastapi.responses import JSONResponse
from typing import List, Optional
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings.openai import OpenAIEmbeddings
from reportlab.lib.styles import getSampleStyleSheet
from langchain.vectorstores import Milvus
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus.flowables import Image
from reportlab.platypus import Spacer
from PIL import Image as PilImage
from reportlab.platypus import SimpleDocTemplate, Paragraph
from langchain.chat_models import ChatOpenAI
from langchain.callbacks import get_openai_callback
from langchain.chains.question_answering import load_qa_chain
from pymilvus import connections, utility, MilvusClient, Collection
from utils_api import QuestionParams, extract_text_from_pdf, KnowledgeBaseRequest
from faster_whisper import WhisperModel
from moviepy.editor import AudioFileClip
from langchain.schema.messages import HumanMessage
import logging
from fastapi import Request

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

# Logg

MILVUS_HOST = "milvus-standalone01"
MILVUS_PORT = "19530"
COLLECTION_NAME = "api"

pdfs_processed = False
collection_exists = False
global knowledge_base
all_messages = []
messages = []
brand = ''
model = ''
year = ''

def on_page(canvas, doc) -> None:
    """
    Add a logo to the top of each page.

    Args:
        canvas (reportlab.pdfgen.canvas.Canvas): Canvas object that can be used to draw on the page.
        doc (reportlab.platypus.doctemplate.BaseDocTemplate): Doc object that contains information about the document.
    """
    # This function will be called for each page during the PDF creation process.
    # It receives a `canvas` object that can be used to draw on the page,
    # and a `doc` object that contains information about the document.

    # Add your image file
    img_path = '/api/routers/application/img/logo.png'
    # Load your image file with PIL
    pil_image = PilImage.open(img_path)

    # Get the original width and height of the image
    orig_width, orig_height = pil_image.size

    # Define the width you want for the image in the PDF
    img_width = 1.0 * inch

    # Calculate the height based on the original image's aspect ratio
    img_height = img_width * orig_height / orig_width

    img = Image(img_path, width=img_width, height=img_height)

    # Draw image at the top of the page
    x_position = 1.09 * inch
    img.drawOn(canvas, x_position, doc.height + 1 * inch)


@router.get("/get_stored_cars")
async def get_stored_cars():
    """
    Get the stored cars.

    Returns:
        dict: Stored cars
    """
    client = MilvusClient(uri=f"http://{MILVUS_HOST}:19530")

    # verify if the collection exists
    collection_exists = utility.has_collection(COLLECTION_NAME)

    if not collection_exists:
        return {"message": f"Collection {COLLECTION_NAME} does not exist",
                "status_code": 400}

    collection = Collection(COLLECTION_NAME)

    expr = "brand != ''"
    result = collection.query(expr, output_fields=["brand", "model", "year"])

    result_formatted = {}

    for item in result:
        brand = item["brand"]
        model = item["model"]
        year = item["year"]
        if brand not in result_formatted:
            result_formatted[brand] = {}
        if model not in result_formatted[brand]:
            result_formatted[brand][model] = []
        if year not in result_formatted[brand][model]:
            result_formatted[brand][model].append(year)

    return {"message": result_formatted,
            "status_code": 200}


def speech_to_text(audio_byte, audio_filename) -> str:
    """
    Transform audio in to text.

    Args:
        audio_byte (bytes): Audio in bytes
        audio_filename (str): Audio filename
    
    Returns:
        str: Transcribed text
    """
    # Write two temporary audio files
    audio_mp3 = "audio_temporary_file_" + audio_filename + ".mp3"
    audio_source = audio_filename 
    audio_content = audio_byte
    open(audio_source, "wb").write(audio_content)
    audio = AudioFileClip(audio_source)
    audio.write_audiofile(audio_mp3, codec="mp3")
    
    # Transcribe audio to text
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_mp3, beam_size=5)
    
    # Delete the temporary files
    os.remove(audio_source)
    os.remove(audio_mp3)
    
    # Extract the result
    for segment in segments:
        result = segment.text
    return result


def answer_question_text(brand: str, model: str, year: str, question: str, openai_api_key: str) -> dict:
    """
    Generate an answer to a question using the knowledge base.

    Args:
        brand (str): Brand of the car
        model (str): Model of the car
        year (str): Year of the car
        question (str): Question
        authorization (str): Authorization header

    Returns:
        dict: Answer to the question
    """
    
    # Create filter query
    filter_query = []
    if brand is not None:
        filter_query.append(f'brand == "{brand}"')
    if model is not None:
        filter_query.append(f'model == "{model}"')
    if year is not None:
        filter_query.append(f'year == "{year}"')

    # Join the filter conditions with '&&'
    filter_query = ' &&'.join(filter_query)

    # Create embeddings
    embeddings = OpenAIEmbeddings(chunk_size=500, openai_api_key=openai_api_key)

    # Get the knowledge base if the collection exists
    knowledge_base = Milvus(collection_name=COLLECTION_NAME,
                                            embedding_function=embeddings,
                                            connection_args={"host": MILVUS_HOST,
                                                                "port": MILVUS_PORT})

    # Use similarity_search instead of similarity_search_by_vector
    docs = knowledge_base.similarity_search(
        query=question,
        k=10,
        param=None,
        expr=filter_query
    )

    # st.write(docs)

    # QA chain using GPT-4
    llm = ChatOpenAI(model_name='gpt-4', temperature=0, openai_api_key=openai_api_key)
    # print(llm)
    chain = load_qa_chain(llm, chain_type="stuff")
    with get_openai_callback() as callback:
        response_content = chain.run(input_documents=docs, question=question)
        print(callback)

    return {"response_content": response_content,
            "status_code": 200}


@router.post("/answer_question_audio")
async def convert_audio_to_text(
                                brand: str, 
                                model: str, 
                                year: str,
                                audio_file: UploadFile = File(...),
                                authorization: str = Header(None)
                                ) -> dict:
    """
    Convert audio to text.

    Args:
        audio_file (UploadFile): Audio file

    Returns:
        dict: Transcribed text
    """

    openai_api_key = authorization.split(' ')[1]

    try:
        print("Reading content of the file")
        # Read the content of the file
        content = await audio_file.read()

        # Call the function to convert audio to text
        question = speech_to_text(content, audio_file.filename)
        print("Text: ", question)
        print("brand: ", brand)
        print("model: ", model)
        print("year: ", year)

        print("Answering question")
        response = answer_question_text(brand, model, year, question, openai_api_key)
        response_content = response["response_content"]
        # Return the result
        return {"text": question, "response_content": response_content, "status_code": 200}
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": str(e)})


@router.post("/knowledge_base")
async def get_knowledge_base(authorization: str = Header(None)) -> dict:
    """
    Get the knowledge base.

    Args:
        authorization (str): Authorization header

    Returns:
        dict: Knowledge base
    """
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header not provided.")
    
    openai_api_key = authorization.split(' ')[1]

    # Verify if the collection exists
    collection_exists = utility.has_collection(COLLECTION_NAME)

    # print(f"Collection {COLLECTION_NAME} exists: {collection_exists}")

    # Create embeddings
    embeddings = OpenAIEmbeddings(chunk_size=500, openai_api_key=openai_api_key)
    # print(embeddings)

    # Create a knowledge base if the collection exists
    if collection_exists:
        knowledge_base = Milvus(collection_name=COLLECTION_NAME,
                                                embedding_function=embeddings,
                                                connection_args={"host": MILVUS_HOST,
                                                                 "port": MILVUS_PORT})
        pdfs_processed = True
    else:
        knowledge_base = None

    return {"knowledge_base": "knowledge_base",
            "status_code": 200}


@router.get("/collection_exists")
async def has_collection(collection_name: str) -> dict:
    """
    Check if a collection exists in the Milvus server.

    Args:
        collection_name (str): Collection name

    Returns:
        dict: Collection exists or not
    """
    exists = utility.has_collection(collection_name)
    return {"exists": exists,
            "status_code": 200}


@router.post("/clear_collection")
async def clear_collection() -> dict:
    """
    Clear the collection in the Milvus server.

    Returns:
        dict: Collection cleared
    """
    collection_name = COLLECTION_NAME
    utility.drop_collection(collection_name)

    return {"message": f"Collection {collection_name} cleared",
            "status_code": 200}


async def encode_image(image_file: UploadFile) -> str:
    """
    Encode an image file in base64 format.

    Args:
        image_file (UploadFile): Image file

    Returns:
        str: Base64 encoded image file
    """
    # Read the content of the file
    content = await image_file.read()
    # Encode the content in base64 format
    base64_encoded = base64.b64encode(content).decode('utf-8')
    return base64_encoded


@router.post("/export_chat_to_pdf")
async def export_chat_to_pdf(data: dict) -> dict:
    """
    Export the chat history to a PDF file.

    Args:
        data (dict): Dictionary containing the list of chat messages under the key 'all_messages'

    Returns:
        dict: Base64 encoded PDF file
    """
    all_messages = data.get('all_messages', [])
    print("Received messages:", all_messages) 
    buffer = BytesIO()

    doc = SimpleDocTemplate(buffer, pagesize=letter)

    story = []
    styles = getSampleStyleSheet()
    style = styles['BodyText']
    style.alignment = 4  # Justify text

    # Add a space after the image
    story.append(Spacer(1, 0.5*inch))

    # Add chat messages in pairs, separated by a Spacer
    for i in range(0, len(all_messages), 2):
        user_msg = all_messages[i]
        user_text = f"{user_msg.get('role', 'User').capitalize()}: {user_msg.get('message', 'No message')}"
        para = Paragraph(user_text, style)
        story.append(para)

        if i + 1 < len(all_messages):
            bot_msg = all_messages[i+1]
            bot_text = f"{bot_msg.get('role', 'Assistant').capitalize()}: {bot_msg.get('message', 'No message')}"
            para = Paragraph(bot_text, style)
            story.append(para)

        # Add a Spacer after each user-bot pair
        story.append(Spacer(1, 0.2*inch))

    # The function `on_page` will be called for each page
    doc.build(story, onFirstPage=on_page, onLaterPages=on_page)

    pdf_bytes = buffer.getvalue()
    buffer.close()

    base64_pdf = b64encode(pdf_bytes).decode('utf-8')

    return {"pdf_bytes": base64_pdf,
            "all_messages": all_messages,
            "status_code": 200}


@router.post("/process_pdf")
async def process_pdf(authorization: str = Header(None), pdfs: List[UploadFile] = File(...)) -> dict:
    """
    Process the PDF files and create a knowledge base.

    Args:
        authorization (str): Authorization header
        pdfs (List[UploadFile]): List of PDF files

    Returns:
        dict: Message indicating that the PDFs have been processed
    """

    # Verify if the authorization header is provided
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header not provided.")
    
    openai_api_key = authorization.split(' ')[1]

    # Verify if PDF files are provided
    if not pdfs:
        raise HTTPException(status_code=400, detail="No PDF files provided.")
    
    # Path to save the PDF files temporarily
    temp_dir = "temp_pdfs"
    os.makedirs(temp_dir, exist_ok=True)

    for pdf in pdfs:
        # Save the PDF file temporarily
        file_path = os.path.join(temp_dir, pdf.filename)
        with open(file_path, "wb") as f:
            f.write(await pdf.read())

        # Extract text from the PDF file
        text = extract_text_from_pdf(file_path)

        # Extract metadata from filename (brand_model_year.pdf)
        filename = file_path.split('/')[-1]
        brand, model, year = filename.rstrip('.pdf').split('_')

        print(f"Brand: {brand}, Model: {model}, Year: {year}")

        # Split text into chunks
        text_splitter = CharacterTextSplitter(
            separator='\n',
            chunk_size=500,
            chunk_overlap=20,
            length_function=len
        )

        chunks = text_splitter.split_text(text)

        # Create embeddings
        embeddings = OpenAIEmbeddings(chunk_size=500, openai_api_key=openai_api_key)

        # Create metadata for each chunk
        metadata = [{'brand': brand, 'model': model, 'year': year} for _ in chunks]

        knowledge_base = globals().get('knowledge_base')

        if knowledge_base is not None:
            # If a knowledge base is provided,
            # insert the new texts and their metadata into
            # the existing knowledge base

            knowledge_base.add_texts(chunks, metadata)

        else:
            # If no knowledge base is provided, create a new one
            knowledge_base = Milvus.from_texts(chunks,
                                                embeddings,
                                                metadata,
                                                connection_args={"host": MILVUS_HOST,
                                                                    "port": MILVUS_PORT},
                                                collection_name=COLLECTION_NAME,
                                                search_params = {"metric_type": "L2",
                                                                        "params": {"nprobe": 10},
                                                                        "offset": 5})

        # Update session state variables
        pdfs_processed = True
        # st.success('PDFs processed. You may now ask questions.')

    return {"message": "PDFs processed. You may now ask questions.",
            "knowledge_base": "knowledge_base",
            "pdfs_processed": pdfs_processed,
            "messages": messages,
            "status_code": 200}


@router.post("/answer_question_image")
async def answer_question_image(authorization: str = Header(None), image_file: UploadFile = File(...), question: str = None) -> JSONResponse:
    """
    Generate an answer to a question using the knowledge base and an image.

    Args:
        authorization (str): Authorization header
        image_file (UploadFile): Image file
        question (str): Question
    
    Returns:
        JSONResponse: Contains the answer and status code
    """

    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header not provided.")

    if not question:
        raise HTTPException(status_code=400, detail="Question not provided.")

    openai_api_key = authorization.split(' ')[1]

    # Asynchronously read and encode the image file
    base64_image = await encode_image(image_file)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    payload = {
        "model": "gpt-4-turbo",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": question
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 300
    }

    # Send the request to OpenAI
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)

    # Return the response content and status code
    return JSONResponse(content=response.json(), status_code=response.status_code)


@router.post("/answer_question")
async def answer_question(params: QuestionParams, authorization: str = Header(None)) -> dict:
    """
    Generate an answer to a question using the knowledge base.

    Args:
        params (QuestionParams): Question parameters
        authorization (str): Authorization header
    
    Returns:
        dict: Answer to the question
    """
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header not provided.")
    
    openai_api_key = authorization.split(' ')[1]

    question = params.question
    brand = params.brand
    model = params.model
    year = params.year

    response = answer_question_text(brand, model, year, question, openai_api_key)
    response_content = response["response_content"]

    return {"response_content": response_content,
            "status_code": 200}