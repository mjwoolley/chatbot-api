from flask import current_app, request, jsonify, make_response
from . import bedrock  # Import bedrock functions
from flask_cors import cross_origin  # Import cross_origin for CORS support

# Note: Since we are not using Flask Blueprints in this simple setup,
# we decorate functions directly on the app instance created in __init__.py
# This requires the app context.

# A simple example endpoint
@current_app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hello from the API!"})

# Endpoint to get available models
@current_app.route('/api/models', methods=['GET'])
@cross_origin()  # Allow cross-origin requests for this endpoint
def get_models():
    try:
        models = bedrock.get_available_models()
        return jsonify({"models": models})
    except Exception as e:
        current_app.logger.error(f"Error getting available models: {e}")
        return jsonify({"error": "Failed to retrieve available models"}), 500

# The main chat endpoint
@current_app.route('/api/chat', methods=['POST'])
@cross_origin()  # Allow cross-origin requests for this endpoint
def chat():
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "Missing 'prompt' in request body"}), 400

    prompt = data['prompt']
    model_id = data.get('model_id', None)  # Get model_id if provided, otherwise None
    
    # Call the bedrock function with the selected model
    try:
        response = bedrock.invoke_claude(prompt, model_id)
        return jsonify({"response": response})
    except Exception as e:
        current_app.logger.error(f"Error calling Bedrock: {e}")
        return jsonify({"error": "Failed to get response from Bedrock"}), 500

# Add other API endpoints here as needed
