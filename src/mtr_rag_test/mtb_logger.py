from loguru import logger as lg
from tqdm import tqdm
import os
import sys

class TqdmToLoguru:
    """Wrapper to redirect tqdm output to loguru."""
    def __init__(self, logger, level="INFO"):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message.strip():  # 过滤空消息
            self.logger.log(self.level, message.strip())

    def flush(self):
        pass  # tqdm 会调用 flush，这里可以忽略

class PrintToLoguru:
    """Wrapper to redirect print output to loguru."""
    def __init__(self, logger, level="INFO"):
        self.logger = logger
        self.level = level

    def write(self, message):
        if message.strip():  # 过滤空消息
            self.logger.log(self.level, message.strip())

    def flush(self):
        pass  # 保持 flush 的接口兼容性

class MatToolBenLogger:
    def __init__(self):
        self.mtb_logger = lg
        self.tqdm_wrapper = None  # 初始化为 None
        
    def __str__(self):
        return "MatToolBenLogger: A logger for the MatToolBen project."

    def set_logger(self, file_path, filename, filter_type=None, level='DEBUG', batch_mode=False):
        """
        :param file_path: 日志文件路径
        :param filename: 日志文件名
        :param filter_type: 日志过滤类型
        :param level: 日志级别
        :param batch_mode: 是否启用批处理模式
        :return: 日志 ID
        """
        # 确保日志目录存在
        os.makedirs(file_path, exist_ok=True)
        
        dic = dict(
            sink=os.path.join(file_path, filename.replace('.log', '_{time}.log')),
            rotation='500 MB',
            format="{time}|{level}|{message}",
            encoding='utf-8',
            level=level,
            enqueue=True,
        )
        if filter_type:
            dic["filter"] = lambda x: filter_type in str(x['level']).upper()
        id = self.mtb_logger.add(**dic)
        
        # 初始化 tqdm 包装器
        if not batch_mode:
            self.tqdm_wrapper = TqdmToLoguru(self.mtb_logger)

        # 重定向 print 到日志
        sys.stdout = PrintToLoguru(self.mtb_logger)

        return id

    @property
    def get_logger(self):
        return self.mtb_logger
    
    def remove_logger(self, id):
        self.mtb_logger.remove(id)
    
    def get_tqdm_logger(self):
        """返回 tqdm 兼容的日志包装器。"""
        if not self.tqdm_wrapper:
            raise ValueError("Logger is not initialized. Call set_logger first.")
        return self.tqdm_wrapper

    # 包装 Loguru 的日志方法
    def trace(self, msg):
        self.mtb_logger.trace(msg)

    def debug(self, msg):
        self.mtb_logger.debug(msg)

    def info(self, msg):
        self.mtb_logger.info(msg)

    def success(self, msg):
        self.mtb_logger.success(msg)

    def warning(self, msg):
        self.mtb_logger.warning(msg)

    def error(self, msg):
        self.mtb_logger.error(msg)

    def critical(self, msg):
        self.mtb_logger.critical(msg)

# 使用示例
if __name__ == "__main__":
    # 初始化自定义日志
    logger = MatToolBenLogger()
    logger.set_logger(file_path="./logs", filename="example.log", level="INFO")

    # 使用 tqdm 并将其输出重定向到日志
    tqdm_logger = logger.get_tqdm_logger()

    with tqdm(total=100, file=tqdm_logger) as pbar:
        for i in range(10):
            pbar.update(10)
            print(f"Progress: {i + 1}/10 completed.")
            logger.info(f"Processed {i + 1} iterations.")

    print("This is a test print statement!")