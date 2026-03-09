import os
from flask import Flask

from .routes.agent import agent_bp
from .routes.cpdm import cpdm_bp
from .routes.ctv import ctv_bp
from .routes.segment import segment_bp
from segmentation.segmenter import _ensure_model
from utils import logger


def create_app():
    app = Flask(__name__)
    app.register_blueprint(agent_bp)
    app.register_blueprint(segment_bp)
    app.register_blueprint(ctv_bp)
    app.register_blueprint(cpdm_bp)
    # Preload segmentation model at startup to avoid per-request load
    try:
        _ensure_model()
    except Exception as exc:
        logger.error(f"[seg] preload failed: {exc}")
        raise
    return app


app = create_app()

# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=int(os.getenv("MODEL_PORT", "5001")), debug=True)
