"Code for the Streamlit app for the Automotive Chatbot"
import os
import requests
from io import BytesIO
import base64
import streamlit as st
from pymilvus import connections, utility

from reportlab.lib.units import inch
from reportlab.platypus.flowables import Image

from PIL import Image as PilImage
from utils.logger import setup_logger

BASE_URL = "http://api:8000/chat"
MILVUS_HOST = "milvus-standalone01"
MILVUS_PORT = "19530"
COLLECTION_NAME = "api"

def initialize_session_state() -> None:
    """Initialize Streamlit session state variables."""
    if 'pdfs_processed' not in st.session_state:
        st.session_state.pdfs_processed = False
    if 'knowledge_base' not in st.session_state:
        st.session_state.knowledge_base = None
    if 'all_messages' not in st.session_state:
        st.session_state.all_messages = []
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if 'brand' not in st.session_state:
        st.session_state.brand = ''
    if 'model' not in st.session_state:
        st.session_state.model = ''
    if 'year' not in st.session_state:
        st.session_state.year = ''

def export_chat_to_pdf() -> BytesIO:
    """
    Export the chat history to a PDF file.

    Returns:
        BytesIO: PDF file as a BytesIO object or None if an error occurs.
    """
    url = f"{BASE_URL}/export_chat_to_pdf"
    print('Exporting chat history to a PDF file...')
    print(st.session_state.all_messages)
    data = {"all_messages": st.session_state.all_messages} 
    response = requests.post(url, json=data)

    if response.status_code == 200:
        base64_pdf = response.json().get("pdf_bytes")
        if base64_pdf:
            pdf_data = base64.b64decode(base64_pdf)
            pdf_buffer = BytesIO(pdf_data)
            return pdf_buffer
        else:
            st.error('No PDF data found in the response.')
            return None
    else:
        st.error(f'An error occurred while exporting the chat history to a PDF file. Status code: {response.status_code}')
        return None

def process_pdfs(pdfs) -> None:
    """
    Process the uploaded PDF files using the API.

    Args:
        pdfs (List[UploadedFile]): List of uploaded PDF files.
    """
    api_key = st.session_state.api_key
    with st.spinner('Processing PDFs...'):
        url = f"{BASE_URL}/process_pdf"
        files = [("pdfs", (pdf.name, pdf, "application/pdf")) for pdf in pdfs]
        headers = {
            'Authorization': f'Bearer {api_key}',
        }
        try:
            response = requests.post(url, files=files, headers=headers)
            if response.status_code == 200:
                # print(response.json())
                st.session_state.knowledge_base = response.json().get("knowledge_base")
                st.success("PDF sent successfully to the API.")
            else:
                st.error("Error sending PDF to the API. Status code: {}".format(response.status_code))
        except Exception as e:
            st.error("Error sending PDF to the API: {}".format(e))

def answer_question(question, brand=None, model=None, year=None) -> str:
    """
    Generate an answer to a question using the knowledge base.
    
    Args:
        question (str): Question.
        brand (str): Brand of the car.
        model (str): Model of the car.
        year (str): Year of the car.
    
    Returns:
        str: Answer to the question.
    """
    api_key = st.session_state.api_key
    with st.spinner('Thinking...'):
        url = f"{BASE_URL}/answer_question"
        params = {"question": question, "brand": brand, "model": model, "year": year}

        headers = {
            'Authorization': f'Bearer {api_key}',
        }

        response = requests.post(url, json=params, headers=headers)
        if response.status_code == 200:
            result = response.json()
            return result.get("response_content")
        else:
            st.error("Error answering the question. Status code: {}".format(response.status_code))
            return None

def answer_question_image(question, image_file) -> str:
    """
    Generate an answer to a question using the knowledge base and an image.

    Args:
        question (str): Question.
        image_file (UploadedFile): Image file uploaded by the user.

    Returns:
        str: Answer to the question.
    """
    api_key = st.session_state.api_key
    with st.spinner('Thinking...'):
        url = f"{BASE_URL}/answer_question_image?question={question}"

        if not question:
            st.error("Please provide a question.")
            return None
        
        # Reset the file pointer to the beginning of the file
        image_file.seek(0)
        # Preparing the request
        files = {'image_file': (image_file.name, image_file, 'multipart/form-data')}
        data = {'question': question}
        
        headers = {
            'Authorization': f'Bearer {api_key}',
        }

        # Send the request to the API
        response = requests.post(url, files=files, data=data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('choices'):
                response_content = result['choices'][0]['message']['content']
                return response_content
            else:
                st.error("No response content found in the API response.")
        else:
            st.error("Error answering the question. Status code: {}".format(response.status_code))
            return None


def process_transcription_as_input(transcribed_text, answer) -> None:
    """
    Process the transcribed text as user input and generate a response.
    
    Args:
        transcribed_text (str): Transcribed text.
        brand (str): Brand of the car.
        model (str): Model of the car.
        year (str): Year of the car.
    """

    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "all_messages" not in st.session_state:
        st.session_state.all_messages = []

    # Add the transcribed text to the session state
    st.session_state.messages.append({"role": "user", "message": transcribed_text})
    st.session_state.all_messages.append({"role": "user", "message": transcribed_text})

    # Generate a response to the transcribed text
    # response = answer_question(transcribed_text, brand=brand, model=model, year=year)

    # Check if the response is not None
    if answer:
        st.session_state.messages.append({"role": "assistant", "message": answer})
        st.session_state.all_messages.append({"role": "assistant", "message": answer})


def convert_audio_to_text(audio_file, api_key, brand, model, year) -> None:
    """
    Send the audio file to FastAPI for conversion to text.
    
    Args:
        audio_file (UploadedFile): Audio file uploaded by the user.
        brand (str): Brand of the car.
        model (str): Model of the car.
        year (str): Year of the car.
    """
    if st.session_state.get('processed_audio') == audio_file.name:
        print("Audio already processed.")
        return

    print("Converting audio to text...")

    files = {"audio_file": (audio_file.name, audio_file, "audio/mpeg")}
    headers = {"Authorization": f"Bearer {api_key}"}

    query_params = f"?brand={brand}&model={model}&year={year}"

    try:
        response = requests.post(f"{BASE_URL}/answer_question_audio{query_params}", 
                                #  params=params, 
                                 headers=headers, 
                                 files=files
                                 )
        response.raise_for_status()
    except requests.RequestException as e:
        st.error(f"Error converting audio to text: {e}")
        return
    
    text = response.json().get("text")
    answer = response.json().get("response_content")
    if text and answer:
        process_transcription_as_input(text, answer)
        st.session_state['processed_audio'] = audio_file.name

def clear_chat_history() -> None:
    """Clear the chat history."""
    st.session_state.messages = [{"role": "assistant",
                                  "message": "How can I help you with your automotive manual inquiries today?"}]
    st.session_state.all_messages = []

def setup_sidebar() -> None:
    """Setup the sidebar."""
    # Sidebar
    with st.sidebar:
        st.title('PDF Insights')
        st.write("\n")

        # Autentication section
        st.subheader("🔑 Authentication")
        openai_key = st.text_input('Enter your OpenAI API key:', type='password', key='openai_key')

        # Verify if the key is valid
        if openai_key and openai_key.startswith('sk-'):
            os.environ['OPENAI_API_KEY'] = openai_key
            st.session_state.api_key = openai_key
            st.success('API key provided ✅')

            # Verify if the initial message was displayed
            if not st.session_state.get('initial_message_displayed', False):
                st.session_state.messages = [{"role": "assistant",
                                              "message": "How can I help you with your automotive manual inquiries today?"}]
                st.session_state.initial_message_displayed = True
        else:
            st.warning('Please enter your OpenAI API key ⚠️')

            # Stop the app if the key is invalid
            st.stop()

        st.write("\n")

        # if collection not exists, display a message to the user
        if not check_collection_exists(COLLECTION_NAME):
            st.warning('⚠️ The collection is empty. Please upload PDF files to start the chat.')

        # PDF processing section
        st.subheader("📄 PDF Processing Actions")
        pdfs = st.file_uploader('Choose PDF files', type=['pdf'], accept_multiple_files=True)
        process_pdfs_button = st.button('🔄 Process PDFs')

        
        st.write("\n")

        # Process PDFs if the button is clicked and PDFs are uploaded
        if process_pdfs_button and pdfs:
            process_pdfs(pdfs)

        # Image section
        st.subheader("🖼️ Image Processing Actions")
        image = st.file_uploader('Choose image files', type=['jpg', 'jpeg', 'png'], accept_multiple_files=False)

        if image:
            st.session_state['uploaded_image'] = image
            st.image(image, caption='Uploaded Image.', use_column_width=True)
        
        if st.button('🗑️ Remove Image'):
            st.session_state['uploaded_image'] = None
            st.experimental_rerun()  # Re-run the app to update the UI

        st.write('\n')


def display_chat(brand=None, model=None, year=None) -> None:
    """
    Display the chat.

    Args:
        brand (str): Brand of the car.
        model (str): Model of the car.
        year (str): Year of the car.
    """

    # For each message in the session state, display the message
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["message"])
    
    # Input field for the user for the chat
    if prompt := st.chat_input():
        # Add the user message to the session state
        st.session_state.messages.append({"role": "user", "message": prompt})
        st.session_state.all_messages.append({"role": "user", "message": prompt})

        # Generate a response to the user's question
        response = answer_question(prompt, brand=brand, model=model, year=year)

        # Add the response of the assistant to the session state
        st.session_state.messages.append({"role": "assistant", "message": response})
        st.session_state.all_messages.append({"role": "assistant", "message": response})

        # Show the user's question and the assistant's response
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            st.write(response)

def display_chat_image() -> None:
    """
    Display the chat with an image.
    """
    # For each message in the session state, display the message
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["message"])
    
    # Input field for the user for the chat
    if prompt := st.chat_input():
        # Add the user message to the session state
        st.session_state.messages.append({"role": "user", "message": prompt})
        st.session_state.all_messages.append({"role": "user", "message": prompt})

        # Generate a response to the user's question
        response = answer_question_image(prompt, st.session_state['uploaded_image'])


        # Add the response of the assistant to the session state
        st.session_state.messages.append({"role": "assistant", "message": response})
        st.session_state.all_messages.append({"role": "assistant", "message": response})

        # Show the user's question and the assistant's response
        with st.chat_message("user"):
            st.write(prompt)
        with st.chat_message("assistant"):
            st.write(response)

    st.write("\n")


def check_collection_exists(collection_name) -> bool:
    """
    Check if a collection exists in Milvus.

    Args:
        collection_name (str): Collection name.

    Returns:
        bool: True if the collection exists, False otherwise.
    """
    url = f"{BASE_URL}/collection_exists"
    try:
        response = requests.get(url, params={"collection_name": collection_name})
        if response.status_code == 200:
            data = response.json()
            exists = data.get("exists")
            return exists
        else:
            st.error("Error checking if the collection exists. Status code: {}".format(response.status_code))
            return None
    except Exception as e:
        st.error("Error checking if the collection exists: {}".format(e))
        return None

def actions() -> None:
    """
    Display the actions section.
    """
    # Chat actions section
    st.subheader("💬 Chat Actions")
    st.button('🧹 Clear Chat History', on_click=clear_chat_history)
    export_chat_button = st.button('📥 Export Chat')

    # Export the chat to PDF if the quantity of
    # messages is greater than 0 and the button is clicked
    if len(st.session_state.all_messages) > 0:
        if export_chat_button:
            pdf_buffer = export_chat_to_pdf()
            if pdf_buffer:

                pdf_bytes = pdf_buffer.getvalue()

                b64 = base64.b64encode(pdf_bytes).decode('utf-8')
                linko = f'<a href="data:application/octet-stream;base64,{b64}" download="chat_history.pdf">Click Here to download your PDF file</a>'
                st.markdown(linko, unsafe_allow_html=True)
            else:
                st.error('Failed to retrieve PDF data.')

    st.write("\n")

    # Collection actions section
    st.subheader("📚 Collection Actions")

    # Drop collection if the button is clicked
    if st.button('🧹 Clear Collection'):
        # utility.drop_collection(COLLECTION_NAME)
        # st.markdown('<meta http-equiv="refresh" content="1">', unsafe_allow_html=True)
        url = f"{BASE_URL}/clear_collection"
        response = requests.post(url, json=COLLECTION_NAME)
        if response.status_code == 200:
            st.success("Collection cleared successfully.")
            st.markdown('<meta http-equiv="refresh" content="1">', unsafe_allow_html=True)
        else:
            st.error("Error clearing collection. Status code: {}".format(response.status_code))


def main():
    """Main function. This function is the entry point of the Streamlit app."""

    # Initialize session state variables
    initialize_session_state()

    if 'processed_audio' not in st.session_state:
        st.session_state['processed_audio'] = None

    # Setup sidebar
    setup_sidebar()

    collection_exists = check_collection_exists(COLLECTION_NAME)

    # Condictions to display the chat, the filters section and some buttons
    if collection_exists or st.session_state.pdfs_processed:
        api_key = st.session_state.api_key
        headers = { 'Authorization': f'Bearer {api_key}' }

        response = requests.post(f"{BASE_URL}/knowledge_base", headers=headers)

        if 'uploaded_image' in st.session_state and st.session_state['uploaded_image'] is not None:
            display_chat_image()
            with st.sidebar:
                actions()
        else:
            st.session_state.knowledge_base = response.json().get("knowledge_base")
            with st.sidebar:
                response = requests.get(f"{BASE_URL}/get_stored_cars")
                data = response.json()

                # Check if the response is successful and get the car brands
                if response.status_code == 200 and 'message' in data:
                    car_brands = list(data['message'].keys())
                else:
                    car_brands = []
                    st.error("Failed to fetch car data from the API.")

                # Section for filters
                brand = st.selectbox('Brand', car_brands, key='brand')

                if brand:
                    models = data['message'][brand]
                    model = st.selectbox('Model', list(models.keys()), key='model')
                    if model:
                        years = models[model]
                        year = st.selectbox('Year', years, key='year')

                st.write("\n")

            # Verify if the filters are filled
            is_input = brand and model and year

            # Display the chat if the filters are filled
            if is_input:

                with st.sidebar:
                    # Section for audio processing
                    st.subheader("🎙️ Audio Processing Actions")
                    audio_file = st.file_uploader("Choose an audio file", type=['mp3', 'wav', 'ogg'], accept_multiple_files=False)

                    if audio_file is not None:
                    
                        # Convert audio to text
                        convert_audio_to_text(audio_file, api_key, brand=brand, model=model, year=year)

                    actions()
                # Display the chat
                display_chat(brand=brand,
                            model=model,
                            year=year)
            else:
                st.warning('⚠️ Please enter the filters to activate the chat feature or upload an image.')

if __name__ == '__main__':
    main()
