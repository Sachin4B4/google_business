import os
import json
import logging
import requests
import uuid
from flask import Flask, request, jsonify
from urllib.parse import urlencode

# Initialize Flask app
app = Flask(__name__)

# Replace with your DeepL API auth key
auth_key = "82a64fae-73d4-4739-9935-bbf3cfc15010"
translator = deepl.Translator(auth_key)

# Azure Translator specific configuration (hardcoded)
azure_api_key = "5a10adc632be48f6af4ae09723d318d4"
azure_translation_endpoint = "https://api.cognitive.microsofttranslator.com/"
azure_region = "eastus2"

# Function to get supported languages from Azure Translator API
def get_supported_languages(endpoint, api_key):
    try:
        url = f"{endpoint.rstrip('/')}/languages?api-version=3.0"
        headers = {
            'Ocp-Apim-Subscription-Key': api_key,
            'Content-Type': 'application/json'
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to retrieve supported languages: {str(e)}")
        raise e

# Function to convert language name to language code
def get_language_code(language_name, supported_languages):
    if supported_languages['translation'] is not None:
        for key, value in supported_languages['translation'].items():
            if value['name'].lower() == language_name.lower() or value['nativeName'].lower() == language_name.lower():
                return key
    return None  # Return None if the language is not supported

# Azure Translation Function
def translate_text_azure(target_language_name, text_to_translate, api_key, text_translation_endpoint, region, source_language_name=None):
    if not text_to_translate or not target_language_name:
        raise ValueError("Both 'target_language' and 'text' must be provided")

    # Get supported languages
    supported_languages = get_supported_languages(text_translation_endpoint, api_key)

    # Convert target language name to language code
    target_language_code = get_language_code(target_language_name, supported_languages)
    if not target_language_code:
        raise ValueError(f"Target language '{target_language_name}' is not supported")

    # Convert source language name to language code, if provided
    source_language_code = None
    if source_language_name:
        source_language_code = get_language_code(source_language_name, supported_languages)
        if not source_language_code:
            raise ValueError(f"Source language '{source_language_name}' is not supported")

    # Azure Translator API configuration
    path = '/translate'
    constructed_url = f"{text_translation_endpoint.rstrip('/')}{path}"

    params = {
        'api-version': '3.0',
        'to': [target_language_code]  # Use the converted language code
    }

    # If source_language_code is provided, add it to the params
    if source_language_code:
        params['from'] = source_language_code

    headers = {
        'Ocp-Apim-Subscription-Key': api_key,
        'Ocp-Apim-Subscription-Region': region,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{'text': text_to_translate}]

    try:
        # Make the request to the Azure Translator API
        response = requests.post(constructed_url, params=params, headers=headers, json=body)
        response.raise_for_status()  # Raise an error for HTTP error responses
        response_json = response.json()

        # Return the response in JSON format
        return json.dumps(response_json, sort_keys=True, ensure_ascii=False, indent=4, separators=(',', ': '))

    except requests.exceptions.HTTPError as http_err:
        logging.error(f"HTTP error occurred: {http_err}", exc_info=True)
        raise http_err
    except requests.exceptions.RequestException as req_err:
        logging.error(f"Request error occurred: {req_err}", exc_info=True)
        raise req_err

# Route for Azure translation service
@app.route('/translate_azure', methods=['POST'])
def translate_azure():
    # Get JSON data from the request
    data = request.get_json()

    # Extract text and languages from the JSON data
    text = data.get('text')
    target_language = data.get('target_language')
    source_language = data.get('source_language', None)

    if not text or not target_language:
        return jsonify({'error': 'Please provide text and target_language'}), 400

    try:
        # Perform translation using Azure Translator API
        translated_text = translate_text_azure(target_language, text, azure_api_key, azure_translation_endpoint, azure_region, source_language)
        return jsonify({'translated_text': translated_text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# (Other routes like /add, /translate (DeepL), etc.)

if __name__ == '__main__':
    # Use the environment variable PORT, or default to port 5000 if not set
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
