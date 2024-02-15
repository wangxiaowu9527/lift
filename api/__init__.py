from flask import Blueprint
from api.views import nodes_base_info, outside, inside, status

node_blue = Blueprint("node", __name__)


# router
node_blue.route("/nodes", methods = ['GET'])(nodes_base_info)
node_blue.route("/out", methods=['POST'])(outside)
node_blue.route("/in", methods=['POST'])(inside)
node_blue.route("/status", methods=['GET'])(status)
