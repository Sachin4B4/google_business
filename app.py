import requests
import time
from flask import Flask, request, jsonify, send_file

app = Flask(__name__)

# DeepL API key
DEEPL_API_KEY = '82a64fae-73d4-4739-9935-bbf3cfc15010'

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
    
if __name__ == '__main__':
    # Use the environment variable PORT, or default to port 5000 if not set
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
