import os
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def say_hi():
    return 'Hi! This is the addition service.'

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

if __name__ == '__main__':
    # Use the environment variable PORT, or default to port 5000 if not set
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
