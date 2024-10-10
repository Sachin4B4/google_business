import requests
import time
import os
import deepl
import psycopg2
from flask import Flask, request, jsonify, send_file
import json



app = Flask(__name__)

# DeepL API key
DEEPL_API_KEY = '82a64fae-73d4-4739-9935-bbf3cfc15010'

# Replace with your DeepL API auth key
auth_key = "82a64fae-73d4-4739-9935-bbf3cfc15010"
translator = deepl.Translator(auth_key)



# Database connection details
DB_CONFIG = {
    'dbname': 'settings_db',
    'user': 'citus',
    'password': 'password@123',
    'host': 'c-settings-details.4frco7jk32qfsk.postgres.cosmos.azure.com',
    'port': '5432'
}




# Language mapping
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

def store_feedback(user_id, feedback_text, source_language, target_language, 
                   document_name=None, source_text=None, translated_text=None):
    try:
        # Establish connection to the PostgreSQL database
        conn = psycopg2.connect(
            dbname='settings_db',
            user='citus',
            password='password@123',
            host='c-settings-details.4frco7jk32qfsk.postgres.cosmos.azure.com',
            port='5432'
        )
        cursor = conn.cursor()

        # SQL query to insert feedback data into the database
        cursor.execute(
            """
            INSERT INTO user_feedback (user_id, feedback_text, source_language, target_language, 
                                       document_name, source_text, translated_text) 
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (user_id, feedback_text, source_language, target_language, document_name, source_text, translated_text)
        )

        # Commit the transaction to save the data
        conn.commit()
        cursor.close()
        conn.close()
        
        return "Feedback stored successfully"
    except Exception as e:
        print(f"Error storing feedback: {e}")
        return "Error storing feedback"


def translate_document(file, source_lang, target_lang):
    # Convert language names to language codes
    source_lang_code = language_mapping.get(source_lang, 'EN')  # Default to English if not found
    target_lang_code = language_mapping.get(target_lang, 'FR')  # Default to French if not found

    # Step 1: Submit the document to DeepL for translation
    url = "https://api.deepl.com/v2/document"
    data = {
        'auth_key': DEEPL_API_KEY,
        'source_lang': source_lang_code,
        'target_lang': target_lang_code
    }
    files = {
        'file': (file.filename, file.stream, file.content_type)
    }

    response = requests.post(url, data=data, files=files)

    if response.status_code != 200:
        return None, None, f"Error submitting document: {response.status_code}, {response.text}"

    # Extract document_id and document_key
    json_response = response.json()
    document_id = json_response.get('document_id')
    document_key = json_response.get('document_key')

    if not document_id or not document_key:
        return None, None, "Error: document_id or document_key missing in response"

    # Step 2: Check the translation status until it's done
    status_url = f"https://api.deepl.com/v2/document/{document_id}"
    status_params = {
        'auth_key': DEEPL_API_KEY,
        'document_key': document_key
    }

    while True:
        status_response = requests.get(status_url, params=status_params)
        if status_response.status_code == 200:
            status_data = status_response.json()
            if status_data['status'] == 'done':
                break  # Translation is complete!
            elif status_data['status'] == 'error':
                return None, None, "Error during translation"
        else:
            return None, None, f"Error checking status: {status_response.status_code}, {status_response.text}"

        time.sleep(5)  # Wait before checking again

    # Step 3: Download the translated document
    download_url = f"https://api.deepl.com/v2/document/{document_id}/result"
    download_params = {
        'auth_key': DEEPL_API_KEY,
        'document_key': document_key
    }
    download_response = requests.get(download_url, params=download_params)

    if download_response.status_code == 200:
        translated_file_name = f"translated_{document_id}.docx"
        with open(translated_file_name, 'wb') as f:
            f.write(download_response.content)
        return translated_file_name, download_response.content, None
    else:
        return None, None, f"Error downloading document: {download_response.status_code}, {download_response.text}"


# Function to connect to the database
def get_db_connection():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None








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
    formality = data.get('formality', 'prefer_more')
    preserve_formatting = data.get('preserve_formatting', True)

    try:
        # Perform translation
        translated_text = translate_text(text, target_language, source_language, formality, preserve_formatting)
        return jsonify({'translated_text': translated_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/document-translate', methods=['POST'])
def document_translate():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']
    source_lang = request.form.get('source_lang', 'English')  # Default source language to English
    target_lang = request.form.get('target_lang', 'French')  # Default target language to French

    # Call the function to translate the document
    translated_file_name, translated_content, error = translate_document(file, source_lang, target_lang)

    if error:
        return jsonify({'error': error}), 500

    # Send the translated file to the user
    return send_file(translated_file_name, as_attachment=True)
    
@app.route('/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()

    # Extract feedback details from the request
    user_id = data.get('user_id')
    feedback_text = data.get('feedback_text')
    source_language = data.get('source_language')
    target_language = data.get('target_language')
    document_name = data.get('document_name', None)
    source_text = data.get('source_text', None)
    translated_text = data.get('translated_text', None)

    if not user_id or not feedback_text or not source_language or not target_language:
        return jsonify({'error': 'Please provide all required fields: user_id, feedback_text, source_language, target_language'}), 400

    # Store feedback in the database
    result = store_feedback(user_id, feedback_text, source_language, target_language, document_name, source_text, translated_text)

    if "Error" in result:
        return jsonify({'error': result}), 500

    return jsonify({'message': result}), 200


@app.route('/save_settings_deepl', methods=['POST'])
def save_settings_deepl():
    # Check if the required form data is present
    if 'admin_id' not in request.form or 'api_key' not in request.form:
        return jsonify({"error": "Missing admin_id or api_key"}), 400

    admin_id = request.form['admin_id']
    api_key = request.form['api_key']

    # Insert data into the database
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        cursor = conn.cursor()

        # SQL query to insert admin_id and api_key into the deepl_settings table
        query = """
        INSERT INTO deepl_settings (admin_id, api_key)
        VALUES (%s, %s)
        ON CONFLICT (admin_id) DO UPDATE
        SET api_key = EXCLUDED.api_key;
        """

        cursor.execute(query, (admin_id, api_key))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Settings saved successfully!"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/test_translation', methods=['POST'])
def test_translation():
    # Get the inputs from form-data or query parameters
    key = request.form.get('key')  # Azure Translator API key
    text_translation_endpoint = request.form.get('endpoint')  # Translator service endpoint URL
    region = request.form.get('region')  # Azure region

    # Hardcoded values for translation
    source_language_code = "en"  # English as source language
    target_language_code = "es"  # Spanish as target language
    text_to_translate = "This is a test"  # Text to translate

    # Check if key, endpoint, and region are provided
    if not key or not text_translation_endpoint or not region:
        return jsonify({"error": "API key, endpoint, and region are required."}), 400

    # Construct the Azure Translator API URL
    path = 'translate'
    constructed_url = f"{text_translation_endpoint}/{path}"

    # Setup the query parameters and headers
    params = {
        'api-version': '3.0',
        'from': source_language_code,
        'to': target_language_code
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': region,
        'Content-Type': 'application/json'
    }

    # Body of the request with the hardcoded text to be translated
    body = [{'text': text_to_translate}]

    try:
        # Make the request to the Azure Translator API
        response = requests.post(constructed_url, params=params, headers=headers, json=body)
        response.raise_for_status()  # Raises an HTTPError for bad responses

        # Parse the response JSON
        response_json = response.json()

        # Return the JSON response from the API
        return jsonify(response_json), 200

    except requests.exceptions.HTTPError as http_err:
        # Catch HTTP errors from the API call
        return jsonify({"error": f"HTTP error occurred: {http_err}"}), 500
    except Exception as e:
        # Catch any other errors
        return jsonify({"error": f"An unexpected error occurred: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)









    
if __name__ == '__main__':
    # Use the environment variable PORT, or default to port 5000 if not set
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
