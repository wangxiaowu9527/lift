from  flask import request
from util import logger
from conf import NODES, TOTAL_FLOORS
from schema import Schema, And
from util.nodes import nodes

msg_system_timeout = {'code': -1, 'msg': 'System timeout.'}
msg_invalid_params = {'code': -1, 'msg': 'Invalid params'}


def nodes_base_info():
    flag, res = nodes.base_info()
    if not flag:
        return {'code': -1, 'msg': res}
    return {'code': 0, 'data': res}

def outside():
    body_schema = Schema({
        'floor_id': And(int, lambda n: (n != 0) and (TOTAL_FLOORS.get('start') <= n <= TOTAL_FLOORS.get('end')),
                        error='floor_id is required and must in TOTAL_FLOORS'),
        'direct': And(str, lambda n: n in ['up', 'down'], error='direct is required and must in ["up", "down"]'),
    }, ignore_extra_keys=True)
    try:
        body = request.get_json()
        body_schema.validate(body)
    except Exception as e:
        logger.error('Invalid request params, detail is:')
        logger.error(str(e))
        return msg_invalid_params
    floor_id = body.get('floor_id')
    direct = body.get('direct')
    # 特别楼层校验
    if floor_id == TOTAL_FLOORS.get('end') and direct == 'up':
        err_msg = 'You are already on the top floor, no need to up.'
        logger.warning(err_msg)
        return {'code': -1, 'msg': err_msg}
    if floor_id == TOTAL_FLOORS.get('start') and direct == 'down':
        err_msg = 'You are already on the lowest floor, no need to down.'
        logger.error(err_msg)
        return {'code': -1, 'msg': err_msg}
    # 获取支持节点
    logger.info('Stand: outside, floor_id: {}, direct: {}'.format(floor_id, direct))
    flag, node_names = nodes.get_node_names_by_floor_id(floor_id)
    if not flag:
        return {'code': -1, 'msg': node_names}
    logger.info('Support node names: {}'.format(node_names))
    if not node_names:
        warn_msg = 'There are no support nodes yet, please try again later.'
        logger.warning(warn_msg)
        return {'code': -1, 'msg': warn_msg}
    # 在支持节点中获取当前所在层和运行方向, 计算按任务运行到该层所需总层数, 取最小值
    err_msg = 'Cannot get at least one support node, please try again later.'
    flag, nums = nodes.get_total_number_to_target_floor(node_names, floor_id, direct)
    if not flag:
        logger.error(err_msg)
        return {'code': -1, 'msg': err_msg}
    flag, node_num = nodes.get_min_node_by_num(nums)
    if not flag:
        logger.error(err_msg)
        return {'code': -1, 'msg': err_msg}
    # 写入任务
    write_out_task = nodes.write_out_task(node_num['node_name'], floor_id, direct)
    if not write_out_task:
        return msg_system_timeout
    return {'code': 0, 'data': node_num}

def inside():
    body_schema = Schema({
        'floor_id': And(int, lambda n: (n != 0) and (TOTAL_FLOORS.get('start') <= n <= TOTAL_FLOORS.get('end')),
                        error='floor_id is required and must in TOTAL_FLOORS'),
        'node_name': And(str, error='node_name is required')
    }, ignore_extra_keys=True)
    try:
        body = request.get_json()
        body_schema.validate(body)
    except Exception as e:
        logger.error('Invalid request params, detail is:')
        logger.error(str(e))
        return msg_invalid_params
    floor_id = body.get('floor_id')
    node_name = body.get('node_name')
    # 校验
    flag, base_info = nodes.base_info()
    if not flag:
        return msg_system_timeout
    counter = 0
    for n in base_info:
        if node_name == n['name']:
            counter += 1
            if not n['is_on']:
                logger.error('Param is_on about node_name: {} must be true.'.format(node_name))
                return msg_invalid_params
            if floor_id not in n['reach_floors']:
                logger.error('Param floor_id about node_name must in its reach_floors.')
                return msg_invalid_params
            break
    if counter == 0:
        logger.error('Param node_name must in CONF.NODES.')
        return msg_invalid_params
    # 写入任务
    write_in_task = nodes.write_in_task(node_name, floor_id)
    if not write_in_task:
        return msg_system_timeout
    return {'code': 0, 'data': ''}

def status():
    is_on_nodes = []
    data = []
    for n in NODES:
        if n.get('is_on'):
            is_on_nodes.append(n.get('name'))
    for n in is_on_nodes:
        d = {}
        d['name'] = n
        flag, status = nodes.get_status_by_node_name(n)
        if not flag:
            return msg_system_timeout
        d['status'] = status
        data.append(d)
    return {'code': 0, 'data': data}
