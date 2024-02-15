from flask import Flask
from api import node_blue
from util import logger


def create_app():
    app = Flask(__name__)
    app.register_blueprint(node_blue)
    return app

app = create_app()
logger.info('url_map:')
logger.info(str(app.url_map))