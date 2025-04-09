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
            profile_name = os.environ.get("AWS_PROFILE", None)
            
            # Log which profile we're using
            if profile_name:
                current_app.logger.info(f"Using AWS profile: {profile_name}")
            else:
                current_app.logger.info("No AWS profile specified, using default credential chain")
            
            # Create a session with the profile if specified
            if profile_name:
                session = boto3.Session(profile_name=profile_name)
                bedrock_runtime = session.client(service_name='bedrock-runtime', region_name=aws_region)
            else:
                # Credentials should be handled by boto3's standard chain 
                # (environment vars, shared credential file, IAM role, etc.)
                bedrock_runtime = boto3.client(service_name='bedrock-runtime', region_name=aws_region)
                
            current_app.logger.info(f"Bedrock client initialized for region: {aws_region}")
            
            # Debug: Check if we have valid credentials
            try:
                sts = boto3.client('sts')
                identity = sts.get_caller_identity()
                current_app.logger.info(f"AWS Identity: {identity['Arn']}")
            except Exception as e:
                current_app.logger.warning(f"Could not verify AWS identity: {e}")
                
        except Exception as e:
            current_app.logger.error(f"Error initializing Bedrock client: {e}")
            # Raise the exception to be caught by the route handler
            raise RuntimeError(f"Could not initialize Bedrock client: {e}")
    return bedrock_runtime

# Available Bedrock models
AVAILABLE_MODELS = {
    'claude-3-5-sonnet': 'anthropic.claude-3-5-sonnet-20240620-v1:0',
    'claude-3-5-haiku': 'anthropic.claude-3-5-haiku-20240620-v1:0',
    'claude-3-opus': 'anthropic.claude-3-opus-20240229-v1:0',
    'claude-3-sonnet': 'anthropic.claude-3-sonnet-20240229-v1:0',
    'claude-3-haiku': 'anthropic.claude-3-haiku-20240307-v1:0',
    'claude-instant': 'anthropic.claude-instant-v1',
    'titan-text': 'amazon.titan-text-express-v1',
    'llama2-70b': 'meta.llama2-70b-chat-v1'
}

# Default model
DEFAULT_MODEL_ID = AVAILABLE_MODELS['claude-3-5-sonnet']

def get_available_models():
    """Returns a list of available models with their display names and IDs."""
    return [{'name': key, 'id': value} for key, value in AVAILABLE_MODELS.items()]

def invoke_claude(prompt, model_id=None):
    """Sends a prompt to a Bedrock model and returns the response text.
    
    Args:
        prompt: The user's input text
        model_id: The specific model ID to use, defaults to DEFAULT_MODEL_ID if None
    """
    client = get_bedrock_client()
    
    # Use the specified model or fall back to default
    model_id = model_id if model_id else DEFAULT_MODEL_ID
    
    # Log which model is being used
    current_app.logger.info(f"Using model: {model_id}")
    
    try:
        # Check if it's an Anthropic model
        if 'anthropic' in model_id:
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
        # Amazon Titan model
        elif 'amazon.titan' in model_id:
            body = json.dumps({
                "inputText": prompt,
                "textGenerationConfig": {
                    "maxTokenCount": 1000,
                    "temperature": 0.7,
                    "topP": 0.9
                }
            })
        # Meta Llama model
        elif 'meta.llama' in model_id:
            body = json.dumps({
                "prompt": f"<s>[INST] {prompt} [/INST]",
                "max_gen_len": 1000,
                "temperature": 0.7,
                "top_p": 0.9
            })
        # Default to Claude format if unknown
        else:
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
            modelId=model_id,
            accept='application/json',
            contentType='application/json'
        )

        response_body = json.loads(response.get('body').read())
        
        # Different models have different response formats
        if 'anthropic' in model_id:
            # Claude models format
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
        # Amazon Titan model format
        elif 'amazon.titan' in model_id:
            if "results" in response_body and len(response_body["results"]) > 0:
                return response_body["results"][0].get("outputText", "[No output text received]")
            else:
                current_app.logger.warning(f"No valid results found in Titan response: {response_body}")
                return "[No text content received from model]"
        # Meta Llama model format
        elif 'meta.llama' in model_id:
            if "generation" in response_body:
                return response_body.get("generation", "[No generation received]")
            else:
                current_app.logger.warning(f"No valid generation found in Llama response: {response_body}")
                return "[No text content received from model]"
        # Generic fallback
        else:
            # Try to extract text from common response formats
            if "content" in response_body:
                return str(response_body["content"])
            elif "text" in response_body:
                return response_body["text"]
            elif "response" in response_body:
                return response_body["response"]
            else:
                current_app.logger.warning(f"Unknown response format: {response_body}")
                return f"[Response received but format unknown: {str(response_body)[:100]}...]"

    except Exception as e:
        current_app.logger.error(f"Error invoking Bedrock model {model_id}: {e}")
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
