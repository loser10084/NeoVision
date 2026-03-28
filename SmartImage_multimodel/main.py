from api_gateway.app import create_app
import os

app = create_app()

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.getenv("MODEL_PORT", "5001")),
        debug=os.getenv("MODEL_DEBUG", "false").lower() == "true",
    )
