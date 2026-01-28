"""
Logger类：
    一个简单的日志类，支持五种日志级别：DEBUG、INFO、WARNING、ERROR、CRITICAL。
    每个日志消息都包含时间戳、日志级别、调用位置和日志消息本身。
"""


import inspect
import os
import sys
from datetime import datetime
import traceback

# 是否开启DEBUG模式
DEBUG = os.getenv("DEBUG_MODE", "false").lower() == "true"

# 输出硬上限
MAX_LOG_LENGTH = 1000


# Windows 终端颜色支持
if os.name == "nt":
    os.system("")

class Logger:
    # ANSI 颜色码
    COLORS = {
        "DEBUG": "\033[90m",     # 灰色
        "INFO": "\033[32m",      # 绿色
        "SUCCESS": "\033[1;32m",   # 深绿色
        "WARNING": "\033[33m",   # 黄色
        "ERROR": "\033[31m",     # 红色
        "CRITICAL": "\033[1;31m",  # 深红色字体（加粗）
        "RESET": "\033[0m",
    }

    def _timestamp(self):
        now = datetime.now()
        return now.strftime("%Y-%m-%d | %H:%M:%S") + f".{int(now.microsecond / 1000):03d}"

    def _caller_info(self):
        # 获取调用 logger 的代码位置
        frame = inspect.stack()[3]
        filename = os.path.basename(frame.filename)
        line = frame.lineno
        return f"{filename}:{line}"

    def _log(self, level, message):
        time_str = self._timestamp()
        location = self._caller_info()
        color = self.COLORS.get(level, "")
        reset = self.COLORS["RESET"]

        # 对消息进行截断
        if len(message) > MAX_LOG_LENGTH:
            message = message[:MAX_LOG_LENGTH] + "..."

        log_line = f"[{time_str}] [{level:<8}] [{location}]：{message}"

        print(f"{color}{log_line}{reset}", file=sys.stdout)

    # 五种日志方法
    def debug(self, message):
        if DEBUG:
            self._log("DEBUG", message)

    def info(self, message):
        self._log("INFO", message)

    def success(self, message):
        self._log("SUCCESS", message)

    def warning(self, message):
        self._log("WARNING", message)

    def error(self, message, e: Exception = None):
        self._log("ERROR", message)
        if e:
            self._print_exception(e)

    def critical(self, message, e: Exception = None):
        self._log("CRITICAL", message)
        if e:
            self._print_exception(e)

    # 打印异常
    def _print_exception(self, e: Exception):
        color = self.COLORS.get("CRITICAL", "")
        reset = self.COLORS["RESET"]

        stack_lines = traceback.format_exception(type(e), e, e.__traceback__)
        # 逐行原样打印
        for line in "".join(stack_lines).rstrip().split("\n"):
            print(f"{color}{line}{reset}", file=sys.stdout)




# 对外暴露的全局 logger 实例
logger = Logger()


# 示例使用
if __name__ == "__main__":
    logger.debug("这是一个调试信息")
    logger.info("这是一个普通信息")
    logger.warning("这是一个警告信息")
    logger.error("这是一个错误信息")
    logger.critical("这是一个严重错误信息")

    # 测试异常日志
    try:
        raise ValueError("这是一个测试异常")
    except ValueError as e:
        logger.critical("捕获到 ValueError 异常", e)