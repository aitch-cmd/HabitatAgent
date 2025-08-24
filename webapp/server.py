import datetime
import os
from pathlib import Path
from dotenv import load_dotenv
from flask import Flask, jsonify
from datetime import datetime
from webapp.controllers.whatsapp import whatsapp_bp


load_dotenv(dotenv_path=Path(".env"))
app = Flask(__name__)

app.register_blueprint(whatsapp_bp)
@app.route("/ping", methods=['GET'])
def ping():
    today = datetime.now()
    return jsonify({"date": today})




if __name__ == "__main__":
    print(os.environ.get("PORT"))
    app.run(port=int(os.environ.get("PORT", 8080)))