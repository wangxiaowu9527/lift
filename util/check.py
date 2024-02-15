import string
from conf import RUN_PORT, TOTAL_FLOORS, NODES, FLOOR_EACH_RUN_TIME, FLOOR_OPEN_STAY_TIME
from util import logger
import socket

def check():

    # RUN_PORT
    if not isinstance(RUN_PORT, int):
        logger.error('RUN_PORT must be int.')
        return
    if not 1 <= RUN_PORT <= 65535:
        logger.error('RUN_PORT must in 1~65535.')
        return

    # TOTAL_FLOORS
    if not isinstance(TOTAL_FLOORS, dict):
        logger.error('TOTAL_FLOORS must be dict.')
        return
    start = TOTAL_FLOORS.get('start')
    end = TOTAL_FLOORS.get('end')
    if start == None or end == None:
        logger.error('Keys in TOTAL_FLOORS must include "start" and "end".')
        return
    if not isinstance(start, int) or not isinstance(end, int):
        logger.error('Values of "start" or "end" in TOTAL_FLOORS must be int.')
        return
    if start > 1 or start == 0:
        logger.error('Values of "start" must littler equal than 1 and not be 0 in TOTAL_FLOORS.')
        return
    if end <= start or end < 1:
        logger.error('Values of "end" must greater equal than 1, and greater than "start" in TOTAL_FLOORS.')
        return

    # NODES
    if not isinstance(NODES, list) or len(NODES) == 0:
        logger.error('NODES must be list and not empty.')
        return
    names = []
    for n in NODES:
        if not isinstance(n, dict) or not n:
            logger.error('Members in NODES must be dict and not empty.')
            return
        name = n.get('name')
        if not name or not isinstance(name, str) or len(name) != 1 or name not in string.ascii_uppercase:
            logger.error('The value of key "name" in NODES members must exist and be single string in A~Z.')
            return
        names.append(name)
        mode = n.get('mode')
        if not mode or mode not in [1,2,3]:
            logger.error('The value of key "mode" in NODES members must exist and in [1,2,3].')
            return
        is_on = n.get('is_on')
        if is_on == None or is_on not in [True, False]:
            logger.error('The value of key "is_on" in NODES members must exist and be bool.')
            return
        # start and end
        start = n.get('start')
        end = n.get('end')
        if not start or not isinstance(start, int) or start < TOTAL_FLOORS.get('start'):
            logger.error('The value of key "start" in NODES members must exist,'
                         'and be int and greater equal than the value of key "start" in TOTAL_FLOORS.')
            return
        if not end or not isinstance(end, int) or end > TOTAL_FLOORS.get('end') or end <= start or end < 1:
            logger.error('The value of key "end" in NODES members must exist, and be int,'
                         'and littler equal than the value of key "end" in TOTAL_FLOORS, and greater than "start",'
                         'and greater equal than 1.')
            return
    if names:
        names_set = set(names)
        if len(names_set) != len(names):
            logger.error('The value of key "name" in NODES members must be unique.')
            return

    # FLOOR_EACH_RUN_TIME
    if not isinstance(FLOOR_EACH_RUN_TIME, int) or FLOOR_EACH_RUN_TIME <= 0:
        logger.error('FLOOR_EACH_RUN_TIME must be int and greater than 0.')
        return

    # FLOOR_OPEN_STAY_TIME
    if not isinstance(FLOOR_OPEN_STAY_TIME, int) or FLOOR_OPEN_STAY_TIME <= 0:
        logger.error('FLOOR_OPEN_STAY_TIME must be int and greater than 0.')
        return

    # Agent check
    sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sk.settimeout(5)
    try:
        agent_ip = 'localhost'
        agent_port = RUN_PORT + 1
        res = sk.connect_ex((agent_ip, agent_port))
        if res != 0:
            logger.error('Cannot connect to agent => {}:{}, please start agent first.'.format(agent_ip, agent_port))
            return
    except Exception as e:
        logger.error(str(e))
        return
    finally:
        sk.close()

    return True

ck = check()