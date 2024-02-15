# Author: wangxiaowu
# Date: 2023-12-24
# Used for: Lift scheduling simulation

from util.create_app import app
from util.check import ck
from conf import RUN_PORT


if __name__ == '__main__':
    if not ck:
        exit(1)
    app.run(host='0.0.0.0', debug=False, port=RUN_PORT)