import boto3
import json
import os
from flask import current_app # Import current_app to access logger

# Initialize Bedrock client globally or within a function as needed
bedrock_runtime = None

def get_bedrock_client():
    """Initializes and returns the Bedrock runtime client."""
    global bedrock_runtime
    if bedrock_runtime is None:
        try:
            # Use environment variables loaded by Flask app
            aws_region = os.environ.get("AWS_REGION_NAME", "us-east-1") 
            # Credentials should be handled by boto3's standard chain 
            # (environment vars, shared credential file, IAM role, etc.)
            bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name=aws_region)
            current_app.logger.info(f"Bedrock client initialized for region: {aws_region}")
        except Exception as e:
            current_app.logger.error(f"Error initializing Bedrock client: {e}")
            # Raise the exception to be caught by the route handler
            raise RuntimeError(f"Could not initialize Bedrock client: {e}")
    return bedrock_runtime

# Model ID for Claude 3.5 Sonnet (Ensure this is correct)
MODEL_ID = 'anthropic.claude-3-5-sonnet-20240620-v1:0'

def invoke_claude(prompt):
    """Sends a prompt to Claude 3.5 Sonnet via Bedrock and returns the response text."""
    client = get_bedrock_client()
    
    try:
        body = json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        })

        response = client.invoke_model(
            body=body,
            modelId=MODEL_ID,
            accept='application/json',
            contentType='application/json'
        )

        response_body = json.loads(response.get('body').read())
        
        # Enhanced error handling and content extraction
        if "content" in response_body and isinstance(response_body["content"], list) and len(response_body["content"]) > 0:
            first_content_block = response_body["content"][0]
            if isinstance(first_content_block, dict) and first_content_block.get("type") == "text":
                return first_content_block.get('text', "[Empty text content]")
            else:
                 current_app.logger.warning(f"Received non-text or unexpected content block format: {first_content_block}")
                 return "[Received non-text or improperly formatted content]"
        else:
             current_app.logger.warning(f"No valid content block found in response: {response_body}")
             return "[No text content received from model]"

    except Exception as e:
        current_app.logger.error(f"Error invoking Bedrock model {MODEL_ID}: {e}")
        # Re-raise the exception to be handled by the route
        raise ConnectionError(f"Failed to communicate with Bedrock model: {e}")

# --- Add functions for other Bedrock interactions (Agents, etc.) below --- 

# Example placeholder for an agent call
# def invoke_agent(agent_id, session_id, prompt):
#     client = get_bedrock_client() # Use the same client or bedrock-agent-runtime
#     try:
#         # ... logic to call invoke_agent ...
#         pass
#     except Exception as e:
#         current_app.logger.error(f"Error invoking agent {agent_id}: {e}")
#         raise ConnectionError(f"Failed to communicate with Bedrock agent: {e}")
