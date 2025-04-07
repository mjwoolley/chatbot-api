from flask import current_app, request, jsonify
from . import bedrock  # Import bedrock functions

# Note: Since we are not using Flask Blueprints in this simple setup,
# we decorate functions directly on the app instance created in __init__.py
# This requires the app context.

# A simple example endpoint
@current_app.route('/api/hello', methods=['GET'])
def hello():
    return jsonify({"message": "Hello from the API!"})

# The main chat endpoint
@current_app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()
    if not data or 'prompt' not in data:
        return jsonify({"error": "Missing 'prompt' in request body"}), 400

    prompt = data['prompt']
    
    # Call the bedrock function (to be implemented in bedrock.py)
    try:
        response = bedrock.invoke_claude(prompt)
        return jsonify({"response": response})
    except Exception as e:
        current_app.logger.error(f"Error calling Bedrock: {e}")
        return jsonify({"error": "Failed to get response from Bedrock"}), 500

# Add other API endpoints here as needed
