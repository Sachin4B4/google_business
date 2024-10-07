import os
import deepl
from flask import Flask, request, jsonify

# Initialize Flask app
app = Flask(__name__)

# Replace with your DeepL API auth key
auth_key = "82a64fae-73d4-4739-9935-bbf3cfc15010"
translator = deepl.Translator(auth_key)

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





def get_settings(admin_id):
    try:
        # Get connection details from environment variables
        host = os.getenv('DB_HOST')
        database = os.getenv('DB_NAME')
        user = os.getenv('DB_USER')
        password = os.getenv('DB_PASSWORD')
        port_str = os.getenv('DB_PORT')

        # Ensure all variables are set
        if not all([host, database, user, password, port_str]):
            return {"error": "Database connection details are not set properly."}, 500
        
        # Convert port to integer
        try:
            port = int(port_str)
        except (ValueError, TypeError) as e:
            logging.error(f"Port conversion error: {e}")
            return {"error": "Invalid port number."}, 500

        # Connect to PostgreSQL
        connection = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            port=port
        )
        cursor = connection.cursor()
        
        # Query the database for the settings associated with the given Admin_id
        query = """
        SELECT key, text_translation_endpoint, document_translation_endpoint, region, storage_connection_string
        FROM settings
        WHERE admin_id = %s;
        """
        
        cursor.execute(query, (admin_id,))
        result = cursor.fetchone()
        
        if not result:
            return {"error": f"No settings found for Admin_id {admin_id}."}, 404
        
        # Prepare the response
        settings = {
            'key': result[0],
            'text_translation_endpoint': result[1],
            'document_translation_endpoint': result[2],
            'region': result[3],
            'storage_connection_string': result[4]
        }
        
        # Close the connection
        cursor.close()
        connection.close()
        
        return settings, 200
    
    except Exception as e:
        logging.error(f"Error: {e}")
        return {"error": "An error occurred while retrieving the settings."}, 500










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
