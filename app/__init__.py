from flask import Flask
from flask_cors import CORS
import os
from dotenv import load_dotenv

def create_app():
    app = Flask(__name__)
    
    # Load environment variables from .env file
    load_dotenv(dotenv_path='../.env') # Look for .env in the parent directory
    
    # Configure CORS
    # In production, you might want to restrict the origins:
    # origins = ["http://localhost:3000", "https://your-frontend-domain.com"]
    # For development, allowing all origins is often convenient
    CORS(app) 
    # Or, for more control:
    # CORS(app, resources={r"/api/*": {"origins": origins}})

    # Register Blueprints (routes)
    with app.app_context():
        from . import routes
        # If you had multiple route files (Blueprints), register them here
        # app.register_blueprint(routes.bp)

    @app.route('/') # Simple health check route
    def health_check():
        return "API is running!"

    return app
