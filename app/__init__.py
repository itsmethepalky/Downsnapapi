from flask import Flask
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

from app import routes  # Import API routes