import os
import datetime
import time
import tkinter as tk
from collections import deque

class LogHandler:
    def __init__(self, log_text_widget):
        self.log_text = log_text_widget
        self.is_logging = False
        self.log_file = None
        self.log_save_path = ""
        self.last_color_update = time.time()
        self.color_update_interval = 1
        self.auto_scroll_var = tk.BooleanVar(value=True)  # 추가
        self.log_buffer = deque(maxlen=1000)  # 최대 1000개의 로그 항목 유지

    def start_logging(self, log_save_path, log_name):
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if log_name:
            file_name = f"{log_name}_{current_time}.log"
        else:
            file_name = f"project_name_{current_time}.log"
        
        file_path = os.path.join(log_save_path, file_name)
        
        try:
            self.log_file = open(file_path, 'w', encoding='utf-8')
            self.is_logging = True
            return True, file_path
        except Exception as e:
            return False, str(e)

    def stop_logging(self):
        if self.log_file:
            self.log_file.close()
            self.log_file = None
        self.is_logging = False

    def update_log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert('end', message + "\n")
        self.log_text.config(state='disabled')
        
        if self.is_logging and self.log_file:
            self.log_file.write(message + "\n")
            self.log_file.flush()

    def clear_log(self):
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, 'end')
        self.log_text.config(state='disabled')

    def update_log_batch(self, messages):
        self.log_text.config(state='normal')
        for message in messages:
            self.log_buffer.append(message)
            self.log_text.insert('end', message + "\n")
            if self.is_logging and self.log_file:
                self.log_file.write(message + "\n")
        if self.is_logging and self.log_file:
            self.log_file.flush()
        
        # 로그 텍스트 위젯의 라인 수 제한
        while int(self.log_text.index('end-1c').split('.')[0]) > 1000:
            self.log_text.delete('1.0', '2.0')
        
        if self.auto_scroll_var.get():
            self.log_text.see('end')
        self.log_text.config(state='disabled')

    def update_log_color(self, color_var, search_text):
        if color_var.get() == "on" and search_text:
            self.log_text.config(state='normal')
            self.log_text.tag_remove("highlight", "1.0", 'end')
            start = "1.0"
            while True:
                start = self.log_text.search(search_text, start, stopindex='end')
                if not start:
                    break
                end = f"{start}+{len(search_text)}c"
                self.log_text.tag_add("highlight", start, end)
                start = end
            self.log_text.tag_config("highlight", foreground="blue")
            self.log_text.config(state='disabled')
