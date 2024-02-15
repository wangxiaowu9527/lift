import os
import time
import socket
from util import logger, log
from util.nodes import nodes
from conf import RUN_PORT, FLOOR_EACH_RUN_TIME, FLOOR_OPEN_STAY_TIME, TOTAL_FLOORS
from util.nodes import sd
from multiprocessing import Process


def task(node_name_dir: str):
    try:
        agent_log_name = 'agent.log'
        agent_log_path = os.path.join(node_name_dir, agent_log_name)
        if not os.path.isfile(agent_log_path):
            with open(agent_log_path, 'w'):
                pass
        agent_logger = log(agent_log_path)
        out_file = os.path.join(node_name_dir, 'outside.txt')
        out_file_lock = '{}.lock'.format(out_file)
        in_file = os.path.join(node_name_dir, 'inside.txt')
        in_file_lock = '{}.lock'.format(in_file)
        status_file = os.path.join(node_name_dir, 'status.txt')
        status_file_lock = '{}.lock'.format(status_file)
        while True:
            agent_logger.info('{}> Circle start, node_name_dir: {} <{}'.format('=' * 10, node_name_dir, '=' * 10))
            # 此处休眠仅为了降低循环速度, 方便调试和查看日志, 非必须
            time.sleep(1)
            # 第一次读取所有文件
            with open(status_file, 'r') as f_status:
                status_str = f_status.read()
                flag, status_d = sd.str_to_dict(status_str)
                if not flag:
                    continue
            floor_id = status_d['floor_id']
            direct = status_d['direct']
            agent_logger.info('First status.txt => floor_id: {}, direct: {}.'.format(floor_id, direct))
            with open(out_file, 'r') as f_out:
                out_str = f_out.read()
                flag, out_d = sd.str_to_dict(out_str)
                if not flag:
                    continue
            out_up = out_d['up']
            out_down = out_d['down']
            agent_logger.info('First outside.txt => up: {}, down: {}.'.format(out_up, out_down))
            with open(in_file, 'r') as f_in:
                in_str = f_in.read()
                flag, in_d = sd.str_to_dict(in_str)
                if not flag:
                    continue
            in_floor_ids = in_d['floor_ids']
            agent_logger.info('First inside.txt => floor_ids: {}.'.format(in_floor_ids))
            # 核心流程
            if direct == 'up':
                agent_logger.info('Sleep {} seconds for run.'.format(FLOOR_EACH_RUN_TIME))
                time.sleep(FLOOR_EACH_RUN_TIME) # 模拟运行
                floor_id += 1
                # 处理特殊0号楼层
                if floor_id == 0:
                    floor_id = 1
                agent_logger.info('Current floor_id: {}.'.format(floor_id))
                if (floor_id in out_up) or (floor_id in in_floor_ids):
                    # 移除outside.txt中up关联的此楼层
                    if floor_id in out_up:
                        agent_logger.info('Creating tmp lock file: {}.'.format(out_file_lock))
                        with open(out_file_lock, 'w'):
                            pass
                        out_up.remove(floor_id)
                        out_d.update({'up': out_up})
                        agent_logger.info('New out_d: {}.'.format(out_d))
                        with open(out_file, 'w') as f_out_w:
                            f_out_w.write(str(out_d))
                        if os.path.isfile(out_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(out_file_lock))
                            os.remove(out_file_lock)
                    # 移除inside.txt中floor_ids关联的此楼层
                    if floor_id in in_floor_ids:
                        agent_logger.info('Creating tmp lock file: {}.'.format(in_file_lock))
                        with open(in_file_lock, 'w'):
                            pass
                        in_floor_ids.remove(floor_id)
                        in_d.update({'floor_ids': in_floor_ids})
                        logger.info('New in_d: {}.'.format(in_d))
                        with open(in_file, 'w') as f_in_w:
                            f_in_w.write(str(in_d))
                        if os.path.isfile(in_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(in_file_lock))
                            os.remove(in_file_lock)
                    agent_logger.info('Sleep {} seconds for stay.'.format(FLOOR_OPEN_STAY_TIME))
                    time.sleep(FLOOR_OPEN_STAY_TIME)  # 模拟开门
                # 更新status.txt中floor_id值
                agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                with open(status_file_lock, 'w'):
                    pass
                status_d.update({'floor_id': floor_id})
                agent_logger.info('New status_d: {}.'.format(status_d))
                with open(status_file, 'w') as f_status_w:
                    f_status_w.write(str(status_d))
                if os.path.isfile(status_file_lock):
                    agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                    os.remove(status_file_lock)
                # 重读所有文件, 判断和更新status.txt中direct值
                with open(status_file, 'r') as f_status:
                    status_str = f_status.read()
                    flag, status_d = sd.str_to_dict(status_str)
                    if not flag:
                        continue
                floor_id = status_d['floor_id']
                direct = status_d['direct']
                agent_logger.info('Second status.txt => floor_id: {}, direct: {}.'.format(floor_id, direct))
                with open(out_file, 'r') as f_out:
                    out_str = f_out.read()
                    flag, out_d = sd.str_to_dict(out_str)
                    if not flag:
                        continue
                out_up = out_d['up']
                out_down = out_d['down']
                agent_logger.info('Second outside.txt => up: {}, down: {}.'.format(out_up, out_down))
                with open(in_file, 'r') as f_in:
                    in_str = f_in.read()
                    flag, in_d = sd.str_to_dict(in_str)
                    if not flag:
                        continue
                in_floor_ids = in_d['floor_ids']
                agent_logger.info('Second inside.txt => floor_ids: {}.'.format(in_floor_ids))

                max_out_up = max(out_d['up']) if out_d['up'] else TOTAL_FLOORS['start'] - 1
                max_out_down = max(out_d['down']) if out_d['down'] else TOTAL_FLOORS['start'] - 1
                max_in_floor_ids = max(in_d['floor_ids']) if in_d['floor_ids'] else TOTAL_FLOORS['start'] - 1
                agent_logger.info('Second max_out_up: {}, max_out_down: {}, max_in_floor_ids: {}.'.format(
                    max_out_up, max_out_down, max_in_floor_ids
                ))
                if (floor_id < max_out_up) or (floor_id < max_out_down) or (floor_id < max_in_floor_ids):
                    # 更新status.txt中direct值为up
                    agent_logger.info('Update direct to "up" in status.txt ...')
                    agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                    with open(status_file_lock, 'w'):
                        pass
                    status_d.update({'direct': 'up'})
                    agent_logger.info('Will write new status_d: {} ...'.format(status_d))
                    with open(status_file, 'w') as f_status_w:
                        f_status_w.write(str(status_d))
                    if os.path.isfile(status_file_lock):
                        agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                        os.remove(status_file_lock)
                    continue
                if len(out_d['up']) == 0 and len(in_d['floor_ids']) == 0:
                    # 更新status.txt中direct值为idle
                    if len(out_d['down']) == 0:
                        agent_logger.info('Update direct to "idle" in status.txt ...')
                        agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                        with open(status_file_lock, 'w'):
                            pass
                        status_d.update({'direct': 'idle'})
                        agent_logger.info('Will write new status_d: {} ...'.format(status_d))
                        with open(status_file, 'w') as f_status_w:
                            f_status_w.write(str(status_d))
                        if os.path.isfile(status_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                            os.remove(status_file_lock)
                        continue
                    # 移除out_d['down']中floor_id的值，开门停留，再更新status.txt中direct值为idle
                    if max_out_down == floor_id:
                        out_d['down'].remove(floor_id)
                        out_d.update({'down': out_d['down']})
                        agent_logger.info(
                            'After second check, will write out_d: {} to outside.txt ...'.format(out_d))
                        agent_logger.info('Creating tmp lock file: {}.'.format(out_file_lock))
                        with open(out_file_lock, 'w'):
                            pass
                        with open(out_file, 'w') as f_out_w:
                            f_out_w.write(str(out_d))
                        if os.path.isfile(out_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(out_file_lock))
                            os.remove(out_file_lock)
                        agent_logger.info('Sleep {} seconds for stay.'.format(FLOOR_OPEN_STAY_TIME))
                        time.sleep(FLOOR_OPEN_STAY_TIME)  # 模拟开门
                        agent_logger.info('Update direct to "idle" in status.txt ...')
                        agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                        with open(status_file_lock, 'w'):
                            pass
                        status_d.update({'direct': 'idle'})
                        agent_logger.info('Will write new status_d: {} ...'.format(status_d))
                        with open(status_file, 'w') as f_status_w:
                            f_status_w.write(str(status_d))
                        if os.path.isfile(status_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                            os.remove(status_file_lock)
                        continue

                # 更新status.txt中direct值为down
                if floor_id in out_d['down']:
                    with open(out_file, 'r') as f_out:
                        out_str = f_out.read()
                        flag, out_d = sd.str_to_dict(out_str)
                        if not flag:
                            continue
                    out_down = out_d['down']
                    agent_logger.info('Third outside.txt => down: {}.'.format(out_down))
                    out_down.remove(floor_id)
                    out_d.update({'down': out_down})
                    agent_logger.info('Update new out_d: {} in outside.txt ...'.format(out_d))
                    agent_logger.info('Creating tmp lock file: {}.'.format(out_file_lock))
                    with open(out_file_lock, 'w'):
                        pass
                    with open(out_file, 'w') as f_out_w:
                        f_out_w.write(str(out_d))
                    if os.path.isfile(out_file_lock):
                        agent_logger.info('Removing tmp lock file: {}.'.format(out_file_lock))
                        os.remove(out_file_lock)
                    agent_logger.info('Sleep {} seconds for stay.'.format(FLOOR_OPEN_STAY_TIME))
                    time.sleep(FLOOR_OPEN_STAY_TIME)  # 模拟开门

                agent_logger.info('Update direct to "down" in status.txt ...')
                agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                with open(status_file_lock, 'w'):
                    pass
                status_d.update({'direct': 'down'})
                agent_logger.info('Will write new status_d: {} ...'.format(status_d))
                with open(status_file, 'w') as f_status_w:
                    f_status_w.write(str(status_d))
                if os.path.isfile(status_file_lock):
                    agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                    os.remove(status_file_lock)
                continue
            if direct == 'down':
                agent_logger.info('Sleep {} seconds for run.'.format(FLOOR_EACH_RUN_TIME))
                time.sleep(FLOOR_EACH_RUN_TIME) # 模拟运行
                floor_id -= 1
                # 处理特殊0号楼层
                if floor_id == 0:
                    floor_id = -1
                agent_logger.info('Current floor_id: {}.'.format(floor_id))
                if (floor_id in out_down) or (floor_id in in_floor_ids):
                    # 移除outside.txt中down关联的此楼层
                    if floor_id in out_down:
                        agent_logger.info('Creating tmp lock file: {}.'.format(out_file_lock))
                        with open(out_file_lock, 'w'):
                            pass
                        out_down.remove(floor_id)
                        out_d.update({'down': out_down})
                        agent_logger.info('New out_d: {}.'.format(out_d))
                        with open(out_file, 'w') as f_out_w:
                            f_out_w.write(str(out_d))
                        if os.path.isfile(out_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(out_file_lock))
                            os.remove(out_file_lock)
                    # 移除inside.txt中floor_ids关联的此楼层
                    if floor_id in in_floor_ids:
                        agent_logger.info('Creating tmp lock file: {}.'.format(in_file_lock))
                        with open(in_file_lock, 'w'):
                            pass
                        in_floor_ids.remove(floor_id)
                        in_d.update({'floor_ids': in_floor_ids})
                        agent_logger.info('New in_d: {}.'.format(in_d))
                        with open(in_file, 'w') as f_in_w:
                            f_in_w.write(str(in_d))
                        if os.path.isfile(in_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(in_file_lock))
                            os.remove(in_file_lock)
                    agent_logger.info('Sleep {} seconds for stay.'.format(FLOOR_OPEN_STAY_TIME))
                    time.sleep(FLOOR_OPEN_STAY_TIME)  # 模拟开门
                # 更新status.txt中floor_id值
                agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                with open(status_file_lock, 'w'):
                    pass
                status_d.update({'floor_id': floor_id})
                agent_logger.info('New status_d: {}.'.format(status_d))
                with open(status_file, 'w') as f_status_w:
                    f_status_w.write(str(status_d))
                if os.path.isfile(status_file_lock):
                    agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                    os.remove(status_file_lock)
                # 重读所有文件, 判断和更新status.txt中direct值
                with open(status_file, 'r') as f_status:
                    status_str = f_status.read()
                    flag, status_d = sd.str_to_dict(status_str)
                    if not flag:
                        continue
                floor_id = status_d['floor_id']
                direct = status_d['direct']
                agent_logger.info('Second status.txt => floor_id: {}, direct: {}.'.format(floor_id, direct))
                with open(out_file, 'r') as f_out:
                    out_str = f_out.read()
                    flag, out_d = sd.str_to_dict(out_str)
                    if not flag:
                        continue
                out_up = out_d['up']
                out_down = out_d['down']
                agent_logger.info('Second outside.txt => up: {}, down: {}.'.format(out_up, out_down))
                with open(in_file, 'r') as f_in:
                    in_str = f_in.read()
                    flag, in_d = sd.str_to_dict(in_str)
                    if not flag:
                        continue
                in_floor_ids = in_d['floor_ids']
                agent_logger.info('Second inside.txt => floor_ids: {}.'.format(in_floor_ids))

                min_out_up = min(out_d['up']) if out_d['up'] else TOTAL_FLOORS['end'] + 1
                min_out_down = min(out_d['down']) if out_d['down'] else TOTAL_FLOORS['end'] + 1
                min_in_floor_ids = min(in_d['floor_ids']) if in_d['floor_ids'] else TOTAL_FLOORS['end'] + 1
                agent_logger.info('Second min_out_up: {}, min_out_down: {}, min_in_floor_ids: {}.'.format(
                    min_out_up, min_out_down, min_in_floor_ids
                ))
                if (floor_id > min_out_up) or (floor_id > min_out_down) or (floor_id > min_in_floor_ids):
                    # 更新status.txt中direct值为down
                    agent_logger.info('Update direct to "down" in status.txt ...')
                    agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                    with open(status_file_lock, 'w'):
                        pass
                    status_d.update({'direct': 'down'})
                    agent_logger.info('Will write new status_d: {} ...'.format(status_d))
                    with open(status_file, 'w') as f_status_w:
                        f_status_w.write(str(status_d))
                    if os.path.isfile(status_file_lock):
                        agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                        os.remove(status_file_lock)
                    continue
                if len(out_d['down']) == 0 and len(in_d['floor_ids']) == 0:
                    # 更新status.txt中direct值为idle
                    if len(out_d['up']) == 0:
                        agent_logger.info('Update direct to "idle" in status.txt ...')
                        agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                        with open(status_file_lock, 'w'):
                            pass
                        status_d.update({'direct': 'idle'})
                        agent_logger.info('Will write new status_d: {} ...'.format(status_d))
                        with open(status_file, 'w') as f_status_w:
                            f_status_w.write(str(status_d))
                        if os.path.isfile(status_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                            os.remove(status_file_lock)
                        continue
                    # 移除out_d['up']中floor_id的值，开门停留，再更新status.txt中direct值为idle
                    if min_out_up == floor_id:
                        out_d['up'].remove(floor_id)
                        out_d.update({'up': out_d['up']})
                        agent_logger.info('After second check, will write out_d: {} to outside.txt ...'.format(out_d))
                        agent_logger.info('Creating tmp lock file: {}.'.format(out_file_lock))
                        with open(out_file_lock, 'w'):
                            pass
                        with open(out_file, 'w') as f_out_w:
                            f_out_w.write(str(out_d))
                        if os.path.isfile(out_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(out_file_lock))
                            os.remove(out_file_lock)
                        agent_logger.info('Sleep {} seconds for stay.'.format(FLOOR_OPEN_STAY_TIME))
                        time.sleep(FLOOR_OPEN_STAY_TIME) # 模拟开门
                        agent_logger.info('Update direct to "idle" in status.txt ...')
                        agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                        with open(status_file_lock, 'w'):
                            pass
                        status_d.update({'direct': 'idle'})
                        agent_logger.info('Will write new status_d: {} ...'.format(status_d))
                        with open(status_file, 'w') as f_status_w:
                            f_status_w.write(str(status_d))
                        if os.path.isfile(status_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                            os.remove(status_file_lock)
                        continue
                # 更新status.txt中direct值为up
                if floor_id in out_d['up']:
                    with open(out_file, 'r') as f_out:
                        out_str = f_out.read()
                        flag, out_d = sd.str_to_dict(out_str)
                        if not flag:
                            continue
                    out_up = out_d['up']
                    agent_logger.info('Third outside.txt => up: {}.'.format(out_up))
                    out_up.remove(floor_id)
                    out_d.update({'up': out_up})
                    agent_logger.info('Update new out_d: {} in outside.txt ...'.format(out_d))
                    agent_logger.info('Creating tmp lock file: {}.'.format(out_file_lock))
                    with open(out_file_lock, 'w'):
                        pass
                    with open(out_file, 'w') as f_out_w:
                        f_out_w.write(str(out_d))
                    if os.path.isfile(out_file_lock):
                        agent_logger.info('Removing tmp lock file: {}.'.format(out_file_lock))
                        os.remove(out_file_lock)
                    agent_logger.info('Sleep {} seconds for stay.'.format(FLOOR_OPEN_STAY_TIME))
                    time.sleep(FLOOR_OPEN_STAY_TIME)  # 模拟开门

                agent_logger.info('Update direct to "up" in status.txt ...')
                agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                with open(status_file_lock, 'w'):
                    pass
                status_d.update({'direct': 'up'})
                agent_logger.info('Will write new status_d: {} ...'.format(status_d))
                with open(status_file, 'w') as f_status_w:
                    f_status_w.write(str(status_d))
                if os.path.isfile(status_file_lock):
                    agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                    os.remove(status_file_lock)
                continue
            if direct == 'idle':
                if out_up and not out_down:
                    agent_logger.info('In outside.txt, out_up is not empty, and out_down is empty, '
                                'updating direct in status.txt ...')
                    if out_up[0] > floor_id: # direct => up
                        agent_logger.info('The first value in out_up is greater than floor_id, setting direct to "up" ...')
                        agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                        with open(status_file_lock, 'w'):
                            pass
                        status_d.update({'direct': 'up'})
                        agent_logger.info('New status_d: {}.'.format(status_d))
                        with open(status_file, 'w') as f_status_w:
                            f_status_w.write(str(status_d))
                        if os.path.isfile(status_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                            os.remove(status_file_lock)
                        continue
                    if out_up[0] == floor_id: # direct => idle
                        agent_logger.info('The first value in out_up is equal to floor_id.')
                        # 先移除outside.txt中up方向floor_id
                        agent_logger.info('Creating tmp lock file: {}.'.format(out_file_lock))
                        with open(out_file_lock, 'w'):
                            pass
                        out_up.remove(floor_id)
                        out_d.update({'up': out_up})
                        agent_logger.info('Write new out_d: {} to outside.txt ...'.format(out_d))
                        with open(out_file, 'w') as f_out_w:
                            f_out_w.write(str(out_d))
                        if os.path.isfile(out_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(out_file_lock))
                            os.remove(out_file_lock)
                        agent_logger.info('Sleep {} seconds for stay.'.format(FLOOR_OPEN_STAY_TIME))
                        time.sleep(FLOOR_OPEN_STAY_TIME)
                        continue
                    # direct => down
                    agent_logger.info('Setting direct to "down" ...')
                    agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                    with open(status_file_lock, 'w'):
                        pass
                    status_d.update({'direct': 'down'})
                    agent_logger.info('New status_d: {}.'.format(status_d))
                    with open(status_file, 'w') as f_status_w:
                        f_status_w.write(str(status_d))
                    if os.path.isfile(status_file_lock):
                        agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                        os.remove(status_file_lock)
                    continue
                if out_down and not out_up:
                    agent_logger.info('In outside.txt, out_down is not empty, and out_up is empty, '
                                'updating direct in status.txt ...')
                    if out_down[0] < floor_id: # direct => down
                        agent_logger.info('The first value in out_down is littler equal than floor_id, '
                                    'setting direct to "down" ...')
                        agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                        with open(status_file_lock, 'w'):
                            pass
                        status_d.update({'direct': 'down'})
                        agent_logger.info('New status_d: {}.'.format(status_d))
                        with open(status_file, 'w') as f_status_w:
                            f_status_w.write(str(status_d))
                        if os.path.isfile(status_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                            os.remove(status_file_lock)
                        continue
                    if out_down[0] == floor_id: # direct => idle
                        agent_logger.info('The first value in out_down is equal to floor_id.')
                        # 先移除outside.txt中down方向floor_id
                        agent_logger.info('Creating tmp lock file: {}.'.format(out_file_lock))
                        with open(out_file_lock, 'w'):
                            pass
                        out_down.remove(floor_id)
                        out_d.update({'down': out_down})
                        agent_logger.info('Write new out_d: {} to outside.txt ...'.format(out_d))
                        with open(out_file, 'w') as f_out_w:
                            f_out_w.write(str(out_d))
                        if os.path.isfile(out_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(out_file_lock))
                            os.remove(out_file_lock)
                        agent_logger.info('Sleep {} seconds for stay.'.format(FLOOR_OPEN_STAY_TIME))
                        time.sleep(FLOOR_OPEN_STAY_TIME)
                        continue
                    # direct => up
                    agent_logger.info('Setting direct to "up" ...')
                    agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                    with open(status_file_lock, 'w'):
                        pass
                    status_d.update({'direct': 'up'})
                    agent_logger.info('New status_d: {}.'.format(status_d))
                    with open(status_file, 'w') as f_status_w:
                        f_status_w.write(str(status_d))
                    if os.path.isfile(status_file_lock):
                        agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                        os.remove(status_file_lock)
                    continue
                if (not out_up) and (not out_down) and in_floor_ids:
                    agent_logger.info('Outside.txt is empty, and inside.txt is not empty, setting direct in status.txt ...')
                    in_floor_id_0 = in_floor_ids[0]
                    agent_logger.info('In_floor_id_0: {}.'.format(in_floor_id_0))
                    if floor_id > in_floor_id_0:
                        agent_logger.info('Floor_id is greater than in_floor_id_0, set direct to "down".')
                        agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                        with open(status_file_lock, 'w'):
                            pass
                        status_d.update({'direct': 'down'})
                        agent_logger.info('New status_d: {}.'.format(status_d))
                        with open(status_file, 'w') as f_status_w:
                            f_status_w.write(str(status_d))
                        if os.path.isfile(status_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                            os.remove(status_file_lock)
                        continue
                    if floor_id < in_floor_id_0:
                        agent_logger.info('Floor_id is litter than in_floor_id_0, set direct to "up".')
                        agent_logger.info('Creating tmp lock file: {}.'.format(status_file_lock))
                        with open(status_file_lock, 'w'):
                            pass
                        status_d.update({'direct': 'up'})
                        agent_logger.info('New status_d: {}.'.format(status_d))
                        with open(status_file, 'w') as f_status_w:
                            f_status_w.write(str(status_d))
                        if os.path.isfile(status_file_lock):
                            agent_logger.info('Removing tmp lock file: {}.'.format(status_file_lock))
                            os.remove(status_file_lock)
                        continue
                    # floor_id == in_floor_ids[0], 在inside.txt移除floor_id
                    agent_logger.info('Floor_id is equal to in_floor_id_0.')
                    agent_logger.info('Creating tmp lock file: {}.'.format(in_file_lock))
                    with open(in_file_lock, 'w'):
                        pass
                    in_floor_ids.remove(floor_id)
                    in_d.update({'floor_ids': in_floor_ids})
                    agent_logger.info('New in_d: {}.'.format(in_d))
                    with open(in_file, 'w') as f_in_w:
                        f_in_w.write(str(in_d))
                    if os.path.isfile(in_file_lock):
                        agent_logger.info('Removing tmp lock file: {}.'.format(in_file_lock))
                        os.remove(in_file_lock)
                    agent_logger.info('Sleep {} seconds for stay.'.format(FLOOR_OPEN_STAY_TIME))
                    time.sleep(FLOOR_OPEN_STAY_TIME)  # 模拟开门

    except KeyboardInterrupt:
        logger.info('Node_name_dir: {}, bye ~'.format(node_name_dir))
    except Exception as e:
        logger.error(str(e))

def agent():
    current_dir = os.path.dirname(__file__)
    logger.info('Project_dir: {}'.format(current_dir))
    status_dir = os.path.join(current_dir, 'status')
    logger.info('Status_dir: {}'.format(status_dir))
    if not os.path.isdir(status_dir):
        logger.info('Cannot find status_dir, creating it ...')
        try:
            os.mkdir(status_dir)
            logger.info('Create status_dir is ok.')
        except Exception as e:
            logger.error('Create status_dir faild, detail is:')
            logger.error(str(e))
            return
    # 获取可用所有节点, 做初始化检查和配置
    logger.info('Getting all nodes with "is_on" is "True" ...')
    flag, res = nodes.base_info()
    if not flag:
        return
    logger.info('Doing init check about nodes ...')
    counter = 0
    for r in res:
        if r.get('is_on'):
            counter += 1
            break
    if counter == 0:
        logger.error('Cannot get at least one node with "is_on" is "True", please try again later.')
        return
    for r in res:
        if r.get('is_on'):
            node_name = r.get('name')
            node_name_dir = os.path.join(status_dir, node_name)
            out_file = os.path.join(node_name_dir, 'outside.txt')
            out_file_lock = '{}.lock'.format(out_file)
            in_file = os.path.join(node_name_dir, 'inside.txt')
            in_file_lock = '{}.lock'.format(in_file)
            status_file = os.path.join(node_name_dir, 'status.txt')
            status_file_lock = '{}.lock'.format(status_file)
            node_files = [out_file, in_file, status_file]
            node_files_lock = [out_file_lock, in_file_lock, status_file_lock]
            try:
                if not os.path.isdir(node_name_dir):
                    os.mkdir(node_name_dir)
                    logger.info('Create node_name_dir: {} is ok.'.format(node_name_dir))
                for node_file in node_files:
                    if not os.path.isfile(node_file):
                        with open(node_file, 'w') as f:
                            if node_file.endswith('status.txt'):
                                init_msg = {'floor_id': 1, 'direct': 'idle'}
                            if node_file.endswith('outside.txt'):
                                init_msg = {'up': [], 'down': []}
                            if node_file.endswith('inside.txt'):
                                init_msg = {'floor_ids': []}
                            f.write(str(init_msg))
                            logger.info('Init msg: {} is written in {}.'.format(init_msg, node_file))
                            logger.info('Create node_file: {} is ok.'.format(node_file))
                for node_file_lock in node_files_lock:
                    if os.path.isfile(node_file_lock):
                        logger.info('Removing node_file_lock: {} ...'.format(node_file_lock))
                        os.remove(node_file_lock)
            except Exception as e:
                logger.error(str(e))
                return
    logger.info('Init check about nodes is ok.')
    # 开启agent端口, 多进程任务模拟各节点每到达一层后更新文件
    listenSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    agent_ip = 'localhost'
    agent_port = RUN_PORT + 1
    try:
        listenSocket.bind((agent_ip, agent_port))
        listenSocket.listen(5)
        logger.info('Agent started on {}:{}.'.format(agent_ip, agent_port))
        tasks = []
        for r in res:
            if r.get('is_on'):
                node_name = r.get('name')
                node_name_dir = os.path.join(status_dir, node_name)
                tasks.append(Process(target=task,args=(node_name_dir,)))
        for t in tasks:
            t.start()
        for t in tasks:
            t.join()
    except KeyboardInterrupt:
        logger.info('Agent bye ~')
    except Exception as e:
        logger.error(str(e))
    finally:
        listenSocket.close()
        logger.info('Agent closed.')


if __name__ == '__main__':
    agent()
