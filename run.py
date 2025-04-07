from app import create_app
import os

app = create_app()

if __name__ == '__main__':
    # Port 5000 is common for Flask dev, but can be changed
    port = int(os.environ.get('PORT', 5000))
    # Debug=True is helpful for development, but should be False in production
    # Use 0.0.0.0 to make it accessible on the network
    app.run(host='0.0.0.0', port=port, debug=True)
