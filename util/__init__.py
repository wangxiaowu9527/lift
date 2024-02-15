import logging
import os

def log(log_path=None):
    try:
        # 配置日志格式
        log_format = "%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s"
        date_format = "%Y-%m-%d %H:%M:%S"
        formatter = logging.Formatter(fmt=log_format, datefmt=date_format)

        # 创建logger对象
        logger = logging.getLogger()
        logger.setLevel(logging.INFO)

        # 创建控制台处理器
        if log_path == None:
            proj_dir = os.path.dirname(os.path.dirname(__file__))
            print('Proj_dir:', proj_dir)
            log_dir = os.path.join(proj_dir, 'logs')
            log_name = 'app.log'
            log_path = os.path.join(log_dir, log_name)
            print('Cannot find log_path, set default: {}.'.format(log_path))
        else:
            log_dir = os.path.dirname(log_path)
        if not os.path.isdir(log_dir):
            os.makedirs(log_dir)
        if not os.path.isfile(log_path):
            with open(log_path, 'w'):
                pass
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)

        # 创建文件处理器
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)

        # 添加处理器到logger对象
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        return logger
    except Exception as e:
        print('Init log error: {}.'.format(str(e)))
        exit(1)

logger = log()