from flask import Flask
from .routes.agent import agent_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(agent_bp)
    return app
