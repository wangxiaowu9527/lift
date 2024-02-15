from conf import NODES
from util import logger
import os
import ast
import json
import random



class StrDict:

    def str_to_dict(self, src_str):
        ''' src_str eg: '{"name":"n1", "age": 20}' '''

        try:
            d = ast.literal_eval(src_str)
        except Exception as e:
            logger.error(str(e))
            return False, {}
        return True, d

    def dict_to_str(self, src_dict):
        try:
            s = json.dumps(src_dict)
        except Exception as e:
            logger.error(str(e))
            return False, ''
        return True, s

sd = StrDict()

class Nodes:

    def __init__(self):
        self.proj_dir = os.path.dirname(os.path.dirname(__file__))
        self.status_dir = os.path.join(self.proj_dir, 'status')

    def base_info(self):
        nodes = []
        try:
            for node in NODES:
                d = {}
                d['name'] = node.get('name')
                d['is_on'] = node.get('is_on')
                src_floors = [f for f in range(node.get('start'), node.get('end') + 1)]
                reach_floors = []
                if node.get('mode') == 1:
                    reach_floors = src_floors
                if node.get('mode') == 2:
                    for f in src_floors:
                        if f%2 == 0:
                            reach_floors.append(f)
                if node.get('mode') == 3:
                    for f in src_floors:
                        if f%2 == 1:
                            reach_floors.append(f)

                if 1 not in reach_floors:
                    reach_floors.append(1)
                if 0 in reach_floors:
                    reach_floors.remove(0)
                d['reach_floors'] = reach_floors
                nodes.append(d)
            return True, nodes
        except Exception as e:
            msg_err = 'Get node base info failed.'
            logger.error(str(e))
            return False, msg_err

    def get_node_names_by_floor_id(self, floor_id: int):
        try:
            flag, res = self.base_info()
            if not flag:
                return False, res
            node_names = []
            if res:
                for d in res:
                    if d['is_on'] and floor_id in d['reach_floors']:
                        node_names.append(d['name'])
            return True, node_names
        except Exception as e:
            logger.error('Get node names by floor_id failed, detail is:')
            logger.error(str(e))
            return False, str(e)

    def get_status_by_node_name(self, node_name: str):
        try:
            node_dir = os.path.join(self.status_dir, node_name)
            node_status_file = os.path.join(node_dir, 'status.txt')
            if not os.path.isfile(node_status_file):
                logger.error('Cannot find node_status_file: {}.'.format(node_status_file))
                return False, ''
            with open(node_status_file, 'r') as f:
                node_status_str = f.read()
                logger.info('Node_name: {}, node_status_str: {}.'.format(node_name, node_status_str))
                flag, node_status_dict = sd.str_to_dict(node_status_str)
                if not flag:
                    return False, ''
                return True, node_status_dict
        except Exception as e:
            logger.error(str(e))
            return False, ''

    def get_total_number_to_target_floor(self, node_names: str, target_floor: int, direct: str):
        '''As following situations
        1. node_direct:up, target_floor<=node_floor, direct:up => abs(max_task_up_floor-node_floor)+abs(min_task_down_floor-max_task_up_floor)+abs(target_floor-min_task_down_floor)
        2. node_direct:up, target_floor>node_floor, direct:up => abs(target_floor-node_floor)
        3. node_direct:up, target_floor<=node_floor, direct:down => abs(max_task_up_floor-node_floor)+abs(target_floor-max_task_up_floor)
        4. node_direct:up, target_floor>node_floor, direct:down => abs(max_task_up_floor-node_floor)+abs(target_floor-max_task_up_floor)
        5. node_direct:down, target_floor<=node_floor, direct:up => abs(node_floor-min_task_down_floor)+abs(target_floor-min_task_down_floor)
        6. node_direct:down, target_floor>node_floor, direct:up => abs(node_floor-min_task_down_floor)+abs(target_floor-min_task_down_floor)
        7. node_direct:down, target_floor<node_floor, direct:down => abs(target_floor-node_floor)
        8. node_direct:down, target_floor>=node_floor, direct:down => abs(node_floor-min_task_down_floor)+abs(min_task_down_floor-max_task_up_floor)+abs(target_floor-max_task_up_floor)
        9. node_direct:idle => abs(target_floor-node_floor)
        :return list, eg: [{'node_name': 'A', 'total_number': 2}, {'node_name': 'B', 'total_number': 0}, ...]
        '''
        try:
            node_total_numbers = []
            for node_name in node_names:
                d = {}
                d['node_name'] = node_name
                node_dir = os.path.join(self.status_dir, node_name)
                node_status_file = os.path.join(node_dir, 'status.txt')
                node_out_file = os.path.join(node_dir, 'outside.txt')
                node_in_file = os.path.join(node_dir, 'inside.txt')
                with open(node_status_file, 'r') as f_status:
                    status_str = f_status.read()
                    flag, status_d = sd.str_to_dict(status_str)
                    if not flag:
                        return False, ''
                node_direct = status_d['direct']
                node_floor = status_d['floor_id']
                logger.info('Node_name: {}, node_direct: {}, node_floor: {}; target_floor: {}, direct: {}.'.format(
                    node_name, node_direct, node_floor, target_floor, direct
                ))
                with open(node_out_file, 'r') as f_out:
                    out_str = f_out.read()
                    flag, out_d = sd.str_to_dict(out_str)
                    if not flag:
                        return False, ''
                with open(node_in_file, 'r') as f_in:
                    in_str = f_in.read()
                    flag, in_d = sd.str_to_dict(in_str)
                    if not flag:
                        return False, ''
                # get max_task_up_floor
                max_out_up_floor = max(out_d['up']) if out_d['up'] else node_floor
                logger.info('Max_out_up_floor: {}.'.format(max_out_up_floor))
                max_in_up_floor = max(in_d['floor_ids']) if in_d['floor_ids'] else node_floor
                logger.info('Max_in_up_floor: {}.'.format(max_in_up_floor))
                max_up_floor = max_out_up_floor if max_out_up_floor >= max_in_up_floor else max_in_up_floor
                max_task_up_floor = max_up_floor if max_up_floor > node_floor else node_floor
                logger.info('Max_task_up_floor: {}.'.format(max_task_up_floor))
                # get min_task_down_floor
                min_out_down_floor = min(out_d['down']) if out_d['down'] else node_floor
                logger.info('Min_out_down_floor: {}.'.format(min_out_down_floor))
                min_in_down_floor = min(in_d['floor_ids']) if in_d['floor_ids'] else node_floor
                logger.info('Min_in_down_floor: {}.'.format(min_in_down_floor))
                min_down_floor = min_out_down_floor if min_out_down_floor <= min_in_down_floor else min_in_down_floor
                min_task_down_floor = min_down_floor if min_down_floor < node_floor else node_floor
                logger.info('Min_task_down_floor: {}.'.format(min_task_down_floor))
                # situations 2 7 9
                if (node_direct == 'up' and target_floor <= node_floor and direct == 'up') or \
                        (node_direct =='down' and target_floor < node_floor and direct == 'down') or \
                        (node_direct == 'idle'):
                    logger.info('Total_number: situations 2 7 9.')
                    # d['total_number'] = abs(target_floor - node_floor)
                    # Special floor 0 need to be consided
                    # Example：when from floor -1 to floor 2, situation is -1->1->2，not -1->0->1->2
                    abs_node_floor_to_target_floor = abs(target_floor - node_floor)
                    d['total_number'] = abs_node_floor_to_target_floor
                    if target_floor * node_floor < 0:
                        d['total_number'] = abs_node_floor_to_target_floor - 1
                # situations 3 4
                if node_direct == 'up' and direct == 'down':
                    logger.info('Total_number: situations 3 4.')
                    # d['total_number'] = abs(max_task_up_floor - node_floor) + abs(target_floor - max_task_up_floor)
                    abs_node_floor_to_task_up_floor = abs(max_task_up_floor - node_floor)
                    if max_task_up_floor * node_floor < 0:
                        abs_node_floor_to_task_up_floor -= 1
                    abs_max_task_up_floor_to_target_floor = abs(target_floor - max_task_up_floor)
                    if target_floor * max_task_up_floor < 0:
                        abs_max_task_up_floor_to_target_floor -= 1
                    d['total_number'] = abs_node_floor_to_task_up_floor + abs_max_task_up_floor_to_target_floor
                # situations 5 6
                if node_direct == 'down' and direct == 'up':
                    logger.info('Total_number: situations 5 6.')
                    # d['total_number'] = abs(node_floor - min_task_down_floor) + abs(target_floor - min_task_down_floor)
                    abs_node_floor_to_min_task_down_floor = abs(node_floor - min_task_down_floor)
                    if node_floor * min_task_down_floor < 0:
                        abs_node_floor_to_min_task_down_floor -= 1
                    abs_min_task_down_floor_to_target_floor = abs(target_floor - min_task_down_floor)
                    if target_floor * min_task_down_floor < 0:
                        abs_min_task_down_floor_to_target_floor -= 1
                    d['total_number'] = abs_node_floor_to_min_task_down_floor + abs_min_task_down_floor_to_target_floor
                # situation 1
                if node_direct == 'up' and target_floor <= node_floor and direct == 'up':
                    logger.info('Total_number: situation 1.')
                    # d['total_number'] = abs(max_task_up_floor - node_floor) + abs(min_task_down_floor - max_task_up_floor) \
                    #                     + abs(target_floor - min_task_down_floor)
                    abs_node_floor_to_max_task_up_floor = abs(max_task_up_floor - node_floor)
                    if max_task_up_floor * node_floor < 0:
                        abs_node_floor_to_max_task_up_floor -= 1
                    abs_max_task_up_floor_to_min_task_down_floor = abs(min_task_down_floor - max_task_up_floor)
                    if min_task_down_floor * max_task_up_floor < 0:
                        abs_max_task_up_floor_to_min_task_down_floor -= 1
                    abs_min_task_down_floor_to_target_floor = abs(target_floor - min_task_down_floor)
                    if target_floor * min_task_down_floor < 0:
                        abs_min_task_down_floor_to_target_floor -= 1
                    d['total_number'] = abs_node_floor_to_max_task_up_floor + abs_max_task_up_floor_to_min_task_down_floor \
                                        + abs_min_task_down_floor_to_target_floor
                # situation 8
                if node_direct == 'down' and target_floor >= node_floor and direct == 'down':
                    logger.info('Total_number: situation 8.')
                    # d['total_number'] = abs(node_floor - min_task_down_floor) + abs(min_task_down_floor - max_task_up_floor) \
                    #                      + abs(target_floor - max_task_up_floor)
                    abs_node_floor_to_min_task_down_floor = abs(node_floor - min_task_down_floor)
                    if node_floor * min_task_down_floor < 0:
                        abs_node_floor_to_min_task_down_floor -= 1
                    abs_min_task_down_floor_to_max_task_up_floor = abs(min_task_down_floor - max_task_up_floor)
                    if min_task_down_floor * max_task_up_floor < 0:
                        abs_min_task_down_floor_to_max_task_up_floor -= 1
                    abs_max_task_up_floor_to_target_floor = abs(target_floor - max_task_up_floor)
                    if target_floor * max_task_up_floor < 0:
                        abs_max_task_up_floor_to_target_floor -= 1
                    d['total_number'] = abs_node_floor_to_min_task_down_floor + abs_min_task_down_floor_to_max_task_up_floor \
                                        + abs_max_task_up_floor_to_target_floor
                node_total_numbers.append(d)
            logger.info('Node_total_numbers: {}.'.format(node_total_numbers))
            return True, node_total_numbers
        except Exception as e:
            logger.error(str(e))
            return False, ''

    def get_min_node_by_num(self, node_nums: list):
        '''
        :param node_nums: list,  result from self.get_total_number_to_target_floor()
        '''
        try:
            if not node_nums:
                logger.error('Param node_nums: {} is empty, which is invalid.'.format(node_nums))
                return False, ''
            if len(node_nums) == 1:
                logger.info('The length of node_nums is 1, so return the first value.')
                return True, node_nums[0]
            tmp_total_numbers = []
            for n in node_nums:
                tmp_total_numbers.append(n['total_number'])
            min_total_number = min(tmp_total_numbers)
            logger.info('Tmp_total_numbers: {}, min_total_number: {}.'.format(tmp_total_numbers, min_total_number))
            tmp_list = []
            for n in node_nums:
                if n['total_number'] == min_total_number:
                    tmp_list.append(n)
            logger.info('Tmp_list: {}.'.format(tmp_list))
            if len(tmp_list) == 1:
                logger.info('The length of tmp_list is 1, so return the first value.')
                return True, tmp_list[0]
            # multiple same value with total_number, take random
            random_index = random.randint(0, len(tmp_list) - 1)
            lucky_node = tmp_list[random_index]
            logger.info('The lucky node selected is: {}.'.format(lucky_node))
            return True, lucky_node
        except Exception as e:
            logger.error(str(e))
            return False, ''

    def write_out_task(self, node_name: str, floor_id: int, direct: str):
        try:
            node_dir = os.path.join(self.status_dir, node_name)
            node_out_file = os.path.join(node_dir, 'outside.txt')
            node_out_file_lock = '{}.lock'.format(node_out_file)
            if os.path.isfile(node_out_file_lock):
                logger.error('Find node_out_file_lock: {}, cannot write.')
                return
            with open(node_out_file, 'r') as f_r:
                out_str = f_r.read()
                flag, out_d = sd.str_to_dict(out_str)
                if not flag:
                    return
            logger.info('Before write, old outside task info: {}.'.format(out_d))
            logger.info('Creating node_out_file_lock: {}.'.format(node_out_file_lock))
            with open(node_out_file_lock, 'w'):
                pass
            if direct == 'up':
                out_d_up = out_d['up']
                if floor_id not in out_d_up:
                    out_d_up.append(floor_id)
                    out_d.update({'up': out_d_up})
            if direct == 'down':
                out_d_down = out_d['down']
                if floor_id not in out_d_down:
                    out_d_down.append(floor_id)
                    out_d.update({'down': out_d_down})
            with open(node_out_file, 'w') as f_w:
                f_w.write(str(out_d))
            logger.info('After write, new outside task info: {}.'.format(out_d))
            if os.path.isfile(node_out_file_lock):
                logger.info('Removing node_out_file_lock.')
                os.remove(node_out_file_lock)
            logger.info('Write outside task to node_name: {} is ok.'.format(node_name))
            return True
        except Exception as e:
            logger.error(str(e))
            return

    def write_in_task(self, node_name: str, floor_id: int):
        try:
            node_dir = os.path.join(self.status_dir, node_name)
            node_in_file = os.path.join(node_dir, 'inside.txt')
            node_in_file_lock = '{}.lock'.format(node_in_file)
            if os.path.isfile(node_in_file_lock):
                logger.error('Find node_in_file_lock: {}, cannot write.')
                return
            with open(node_in_file, 'r') as f_r:
                in_str = f_r.read()
                flag, in_d = sd.str_to_dict(in_str)
                if not flag:
                    return
            logger.info('Before write, old inside task info: {}.'.format(in_d))
            logger.info('Creating node_in_file_lock: {}.'.format(node_in_file_lock))
            with open(node_in_file_lock, 'w'):
                pass
            in_floor_ids = in_d['floor_ids']
            if floor_id not in in_floor_ids:
                in_floor_ids.append(floor_id)
                in_d.update({'floor_ids': in_floor_ids})
            with open(node_in_file, 'w') as f_w:
                f_w.write(str(in_d))
            logger.info('After write, new inside task info: {}.'.format(in_str))
            if os.path.isfile(node_in_file_lock):
                logger.info('Removing node_in_file_lock.')
                os.remove(node_in_file_lock)
            logger.info('Write inside task to node_name: {} is ok.'.format(node_name))
            return True
        except Exception as e:
            logger.error(str(e))
            return

nodes = Nodes()
