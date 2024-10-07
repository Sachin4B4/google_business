import os
import deepl
from flask import Flask, request, jsonify
import requests
import time
import logging

# Initialize Flask app
app = Flask(__name__)

# Replace with your DeepL API auth key
auth_key = "82a64fae-73d4-4739-9935-bbf3cfc15010"
translator = deepl.Translator(auth_key)
# Setup logging
logging.basicConfig(level=logging.INFO)

# DeepL API constants
DEEPL_ENDPOINT = "https://api.deepl.com/v2/document"
DEEPL_API_KEY = "82a64fae-73d4-4739-9935-bbf3cfc15010"  # Replace with your actual API key

# Comprehensive language mapping
language_mapping = {
    "Arabic": "AR",
    "Bulgarian": "BG",
    "Czech": "CS",
    "Danish": "DA",
    "German": "DE",
    "Greek": "EL",
    "English": "EN",  # General English
    "English (British)": "EN-GB",
    "English (American)": "EN-US",
    "Spanish": "ES",
    "Estonian": "ET",
    "Finnish": "FI",
    "French": "FR",
    "Hungarian": "HU",
    "Indonesian": "ID",
    "Italian": "IT",
    "Japanese": "JA",
    "Korean": "KO",
    "Lithuanian": "LT",
    "Latvian": "LV",
    "Norwegian Bokmål": "NB",
    "Dutch": "NL",
    "Polish": "PL",
    "Portuguese": "PT",  # General Portuguese
    "Portuguese (Brazilian)": "PT-BR",
    "Portuguese (European)": "PT-PT",
    "Romanian": "RO",
    "Russian": "RU",
    "Slovak": "SK",
    "Slovenian": "SL",
    "Swedish": "SV",
    "Turkish": "TR",
    "Ukrainian": "UK",
    "Chinese": "ZH",  # General Chinese
    "Chinese (Simplified)": "ZH-HANS",
    "Chinese (Traditional)": "ZH-HANT"
}

def translate_text(text, target_lang_name, source_lang_name=None, formality='default', preserve_formatting=True):
    # Validate required parameters
    if not text or not target_lang_name:
        raise ValueError("Missing required parameters: 'text' and 'target_lang'.")

    # Convert language names to codes
    source_lang = language_mapping.get(source_lang_name) if source_lang_name else None
    target_lang = language_mapping.get(target_lang_name)

    if target_lang is None:
        raise ValueError(f"Invalid target language: '{target_lang_name}'. Please provide a valid language name.")

    try:
        # Perform the translation
        result = translator.translate_text(
            text,
            source_lang=source_lang,
            target_lang=target_lang,
            formality=formality,
            preserve_formatting=preserve_formatting
        )

        # Return the translated text
        return result.text

    except Exception as e:
        raise RuntimeError(f"Translation failed: {str(e)}")

def translate_document(file_obj, source_lang, target_lang):
    try:
        # Get the original file name from the file object
        original_filename = os.path.basename(file_obj.name)
        file_name, file_extension = os.path.splitext(original_filename)

        # Step 1: Upload document for translation
        files = {'file': file_obj}
        data = {
            'auth_key': DEEPL_API_KEY,
            'source_lang': source_lang,  # e.g., 'EN'
            'target_lang': target_lang   # e.g., 'DE'
        }
        logging.info("Uploading document for translation...")
        upload_response = requests.post(f"{DEEPL_ENDPOINT}", files=files, data=data)
        upload_response.raise_for_status()
        upload_result = upload_response.json()

        document_id = upload_result['document_id']
        document_key = upload_result['document_key']

        logging.info(f"Document uploaded successfully with document_id: {document_id}")

        # Step 2: Poll for translation status
        status_url = f"{DEEPL_ENDPOINT}/{document_id}"
        params = {
            'auth_key': DEEPL_API_KEY,
            'document_key': document_key
        }

        while True:
            status_response = requests.get(status_url, params=params)
            status_response.raise_for_status()
            status_data = status_response.json()

            if status_data['status'] == 'done':
                logging.info("Translation completed.")
                break
            elif status_data['status'] == 'error':
                logging.error(f"Error in translation: {status_data['message']}")
                return None
            else:
                logging.info(f"Translation status: {status_data['status']}... retrying in 5 seconds")
                time.sleep(5)

        # Step 3: Download the translated document
        download_url = f"{DEEPL_ENDPOINT}/{document_id}/result"
        translated_doc_response = requests.get(download_url, params=params)
        translated_doc_response.raise_for_status()

        # Save the translated document with the target language code appended to the name
        translated_file_name = f"{file_name}_{target_lang}{file_extension}"
        with open(translated_file_name, 'wb') as output_file:
            output_file.write(translated_doc_response.content)

        logging.info(f"Translated document saved as: {translated_file_name}")
        return translated_file_name

    except requests.exceptions.RequestException as e:
        logging.error(f"An error occurred: {e}")
        return None

@app.route('/document-translate', methods=['POST'])
def document_translate():
    # Check if the request contains the file and required form data
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    if 'source_lang' not in request.form or 'target_lang' not in request.form:
        return jsonify({'error': 'Please provide source_lang and target_lang'}), 400

    # Get the file and languages from the request
    file_obj = request.files['file']
    source_lang = request.form['source_lang']
    target_lang = request.form['target_lang']

    # Perform the document translation
    translated_file_name = translate_document(file_obj, source_lang, target_lang)

    if translated_file_name:
        return jsonify({'message': f'Document translated successfully. Saved as {translated_file_name}'}), 200
    else:
        return jsonify({'error': 'Document translation failed'}), 500












# Route for addition service
@app.route('/')
def say_hi():
    return 'Hi! This is a service that offers both addition and translation. Use /add for addition and /translate for translation.'

@app.route('/add', methods=['POST'])
def add_numbers():
    # Get JSON data from the request
    data = request.get_json()
    
    # Extract numbers from the JSON data
    num1 = data.get('num1')
    num2 = data.get('num2')
    
    # Check if both numbers are provided and are valid
    if num1 is None or num2 is None:
        return jsonify({'error': 'Please provide both num1 and num2'}), 400
    if not isinstance(num1, (int, float)) or not isinstance(num2, (int, float)):
        return jsonify({'error': 'Both num1 and num2 must be numbers'}), 400

    # Perform addition
    result = num1 + num2

    # Return the result as JSON
    return jsonify({'result': result})

# Route for translation service
@app.route('/translate', methods=['POST'])
def translate():
    # Get JSON data from the request
    data = request.get_json()

    # Extract text and languages from the JSON data
    text = data.get('text')
    target_language = data.get('target_language')
    source_language = data.get('source_language', None)

    if not text or not target_language:
        return jsonify({'error': 'Please provide text and target_language'}), 400

    # Optional formality and formatting preservation flags
    formality = data.get('formality', 'default')
    preserve_formatting = data.get('preserve_formatting', True)

    try:
        # Perform translation
        translated_text = translate_text(text, target_language, source_language, formality, preserve_formatting)
        return jsonify({'translated_text': translated_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500





# Route for retrieving settings
@app.route('/get_settings', methods=['GET'])
def retrieve_settings():
    # Extract Admin_id from the request parameters
    admin_id = request.args.get('admin_id')
    
    if not admin_id:
        return jsonify({"error": "Please provide an 'admin_id'."}), 400

    # Call the get_settings function
    settings, status_code = get_settings(admin_id)

    return jsonify(settings), status_code














if __name__ == '__main__':
    # Use the environment variable PORT, or default to port 5000 if not set
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
