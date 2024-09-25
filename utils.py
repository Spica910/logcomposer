import os
import sys
import datetime
import ctypes

def get_script_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_timestamp():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def prevent_screen_sleep():
    if sys.platform == 'win32':
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000002)
    # 다른 운영 체제에 대한 처리를 추가할 수 있습니다.

def allow_screen_sleep():
    if sys.platform == 'win32':
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000)
    # 다른 운영 체제에 대한 처리를 추가할 수 있습니다.
