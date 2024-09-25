import tkinter as tk
from tkinter import ttk, scrolledtext

class TopFrame:
    def __init__(self, parent, refresh_ports, toggle_connection, toggle_prevent_sleep):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(self.frame, text="COM 포트:").pack(side=tk.LEFT, padx=(0, 5))
        self.port_combo = ttk.Combobox(self.frame, width=15)
        self.port_combo.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(self.frame, text="새로고침", command=refresh_ports).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(self.frame, text="Baudrate:").pack(side=tk.LEFT, padx=(0, 5))
        self.baud_combo = ttk.Combobox(self.frame, values=[9600, 19200, 38400, 57600, 115200], width=10)
        self.baud_combo.set(115200)
        self.baud_combo.pack(side=tk.LEFT, padx=(0, 5))

        self.connect_button = ttk.Button(self.frame, text="연결", command=toggle_connection)
        self.connect_button.pack(side=tk.LEFT, padx=(0, 5))

        self.prevent_sleep_var = tk.BooleanVar()  # IntVar에서 BooleanVar로 변경
        self.prevent_sleep_check = tk.Checkbutton(self.frame, text="화면 꺼짐 방지", 
                                                  variable=self.prevent_sleep_var, 
                                                  command=toggle_prevent_sleep)
        self.prevent_sleep_check.pack(side=tk.LEFT)

class LogFrame:
    def __init__(self, parent, change_log_path, toggle_logging, clear_log, update_log_color):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(self.frame, text="저장 경로:").pack(side=tk.LEFT, padx=(0, 5))
        self.log_path_entry = ttk.Entry(self.frame, width=45)
        self.log_path_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(self.frame, text="변경", command=change_log_path).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(self.frame, text="파일명:").pack(side=tk.LEFT, padx=(0, 5))
        self.log_name_entry = ttk.Entry(self.frame, width=20)
        self.log_name_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.log_name_entry.insert(0, "project_name")

        self.save_button = ttk.Button(self.frame, text="저장 시작", command=toggle_logging)
        self.save_button.pack(side=tk.LEFT, padx=(5, 0))

        self.clear_log_button = tk.Button(self.frame, text="Log Clear", command=clear_log)
        self.clear_log_button.pack(side=tk.LEFT, padx=(5, 0))

        self.color_var = tk.StringVar(value="off")
        self.color_check = tk.Checkbutton(self.frame, text="Color", variable=self.color_var, 
                                          onvalue="on", offvalue="off", command=update_log_color)
        self.color_check.pack(side=tk.LEFT, padx=(5, 0))
        
        self.color_entry = tk.Entry(self.frame)
        self.color_entry.pack(side=tk.LEFT, padx=(0, 5))

class LogDisplay:
    def __init__(self, parent):
        self.log_text = scrolledtext.ScrolledText(parent, tabs=("1c", "2c", "3c", "4c"))
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.log_text.config(state=tk.DISABLED)

        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(parent, text="자동 스크롤", variable=self.auto_scroll_var).pack(anchor=tk.W, padx=5)

class CommandFrame:
    def __init__(self, parent, send_command, toggle_repeat):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.X, padx=5, pady=5)

        self.cmd_entry = ttk.Entry(self.frame, width=30)
        self.cmd_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.cmd_entry.bind("<Return>", send_command)

        self.repeat_var = tk.BooleanVar()
        ttk.Checkbutton(self.frame, text="반복", variable=self.repeat_var, command=toggle_repeat).pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(self.frame, text="주기(초):").pack(side=tk.LEFT, padx=(5, 0))
        self.repeat_interval_entry = ttk.Entry(self.frame, width=5)
        self.repeat_interval_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.repeat_interval_entry.insert(0, "1")

        self.repeat_count_label = ttk.Label(self.frame, text="반복 횟수: 0")
        self.repeat_count_label.pack(side=tk.LEFT, padx=(5, 0))

        ttk.Button(self.frame, text="입력", command=send_command).pack(side=tk.RIGHT, padx=(5, 0))

class CustomButtonsFrame:
    def __init__(self, parent):
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill=tk.X, padx=5, pady=5)
