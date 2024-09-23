import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import serial
import serial.tools.list_ports
import datetime
import os
import sys

class UARTLogViewer:
    def __init__(self, master, frame):
        self.master = master
        self.frame = frame
        self.setup_ui()
        self.initialize_variables()
        self.load_custom_commands()
        self.create_custom_buttons()
        self.refresh_ports()

    def setup_ui(self):
        self.setup_top_frame()
        self.setup_log_frame()
        self.setup_log_display()
        self.setup_command_frame()
        self.setup_custom_buttons_frame()

    def setup_top_frame(self):
        top_frame = ttk.Frame(self.frame)
        top_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(top_frame, text="COM 포트:").pack(side=tk.LEFT, padx=(0, 5))
        self.port_combo = ttk.Combobox(top_frame, width=15)
        self.port_combo.pack(side=tk.LEFT, padx=(0, 5))

        ttk.Button(top_frame, text="새로고침", command=self.refresh_ports).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(top_frame, text="Baudrate:").pack(side=tk.LEFT, padx=(0, 5))
        self.baud_combo = ttk.Combobox(top_frame, values=[9600, 19200, 38400, 57600, 115200], width=10)
        self.baud_combo.set(115200)
        self.baud_combo.pack(side=tk.LEFT, padx=(0, 5))

        self.connect_button = ttk.Button(top_frame, text="연결", command=self.toggle_connection)
        self.connect_button.pack(side=tk.LEFT, padx=(0, 5))

    def setup_log_frame(self):
        log_frame = ttk.Frame(self.frame)
        log_frame.pack(fill=tk.X, padx=5, pady=5)

        ttk.Label(log_frame, text="저장 경로:").pack(side=tk.LEFT, padx=(0, 5))
        self.log_path_entry = ttk.Entry(log_frame, width=15)
        self.log_path_entry.pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(log_frame, text="변경", command=self.change_log_path).pack(side=tk.LEFT, padx=(0, 5))

        ttk.Label(log_frame, text="파일명:").pack(side=tk.LEFT, padx=(0, 5))
        self.log_name_entry = ttk.Entry(log_frame, width=20)
        self.log_name_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.log_name_entry.insert(0, "project_name")  # 기본값 설정

        self.save_button = ttk.Button(log_frame, text="저장 시작", command=self.toggle_logging)
        self.save_button.pack(side=tk.LEFT, padx=(5, 0))

    def setup_log_display(self):
        self.log_text = scrolledtext.ScrolledText(self.frame)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.auto_scroll_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self.frame, text="자동 스크롤", variable=self.auto_scroll_var).pack(anchor=tk.W, padx=5)

    def setup_command_frame(self):
        cmd_frame = ttk.Frame(self.frame)
        cmd_frame.pack(fill=tk.X, padx=5, pady=5)

        self.cmd_entry = ttk.Entry(cmd_frame, width=30)
        self.cmd_entry.pack(side=tk.LEFT, expand=True, fill=tk.X)
        self.cmd_entry.bind("<Return>", self.send_command)

        self.repeat_var = tk.BooleanVar()
        ttk.Checkbutton(cmd_frame, text="반복", variable=self.repeat_var, command=self.toggle_repeat).pack(side=tk.LEFT, padx=(5, 0))

        ttk.Label(cmd_frame, text="주기(초):").pack(side=tk.LEFT, padx=(5, 0))
        self.repeat_interval_entry = ttk.Entry(cmd_frame, width=5)
        self.repeat_interval_entry.pack(side=tk.LEFT, padx=(0, 5))
        self.repeat_interval_entry.insert(0, "1")

        self.repeat_count_label = ttk.Label(cmd_frame, text="반복 횟수: 0")
        self.repeat_count_label.pack(side=tk.LEFT, padx=(5, 0))

        ttk.Button(cmd_frame, text="입력", command=self.send_command).pack(side=tk.RIGHT, padx=(5, 0))

    def setup_custom_buttons_frame(self):
        self.custom_buttons_frame = ttk.Frame(self.frame)
        self.custom_buttons_frame.pack(fill=tk.X, padx=5, pady=5)

    def initialize_variables(self):
        self.serial = None
        self.is_logging = False
        self.log_file = None
        self.is_repeating = False
        self.repeat_count = 0
        self.log_save_path = ""
        self.custom_commands = {}

    def refresh_ports(self):
        try:
            ports = [port.device for port in serial.tools.list_ports.comports()]
        except NameError:
            ports = []
            print("COM 포트 목록을 가져올 수 없습니다.")
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.set(ports[0])

    def toggle_connection(self):
        if self.serial and self.serial.is_open:
            self.serial.close()
            self.connect_button.config(text="연결")
        else:
            self.connect_serial()

    def connect_serial(self):
        port = self.port_combo.get()
        baud = int(self.baud_combo.get())
        try:
            self.serial = serial.Serial(port, baud, timeout=1)
            self.connect_button.config(text="연결 끊기")
            self.master.after(10, self.read_uart)
        except serial.SerialException as e:
            self.update_log(f"연결 오류: {str(e)}")

    def read_uart(self):
        if self.serial and self.serial.is_open:
            try:
                data = self.serial.readline().decode('utf-8').strip()
                if data:
                    self.update_log(data)
            except Exception as e:
                self.update_log(f"읽기 오류: {str(e)}")
            finally:
                self.master.after(10, self.read_uart)

    def send_command(self, event=None):
        if self.serial and self.serial.is_open:
            command = self.cmd_entry.get() + '\n'
            self.serial.write(command.encode())
            self.update_log(command.strip())
            self.read_response()

            if not self.repeat_var.get():
                self.cmd_entry.delete(0, tk.END)

            if self.repeat_var.get() and not self.is_repeating:
                self.start_repeat()
            elif self.is_repeating:
                self.repeat_count += 1
                self.repeat_count_label.config(text=f"반복 횟수: {self.repeat_count}")

    def read_response(self):
        if self.serial and self.serial.is_open:
            try:
                while self.serial.in_waiting:
                    data = self.serial.readline().decode('utf-8').strip()
                    if data:
                        self.update_log(data)
            except Exception as e:
                self.update_log(f"읽기 오류: {str(e)}")

    def load_custom_commands(self):
        if getattr(sys, 'frozen', False):
            # 실행 파일로 실행 중인 경우
            script_dir = os.path.dirname(sys.executable)
        else:
            # 스크립트로 실행 중인 경우
            script_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.setup_file_path = os.path.join(script_dir, 'setup.txt')
        
        if not os.path.exists(self.setup_file_path):
            self.create_default_setup_file()
        
        try:
            with open(self.setup_file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                if lines:
                    self.log_save_path = lines[0].strip()
                    for line in lines[1:]:
                        parts = line.strip().split(':', 1)
                        if len(parts) == 2:
                            number, command = parts
                            self.custom_commands[number.strip()] = command.strip()
        except Exception as e:
            messagebox.showerror("파일 읽기 오류", f"setup.txt 파일을 읽는 중 오류가 발생했습니다: {str(e)}")
            self.log_save_path = script_dir
            self.create_default_setup_file()

        self.log_path_entry.delete(0, tk.END)
        self.log_path_entry.insert(0, self.log_save_path)

        if not self.port_combo.get():
            self.port_combo.set("---input COM port---")

    def create_default_setup_file(self):
        if getattr(sys, 'frozen', False):
            # 실행 파일로 실행 중인 경우
            script_dir = os.path.dirname(sys.executable)
        else:
            # 스크립트로 실행 중인 경우
            script_dir = os.path.dirname(os.path.abspath(__file__))
        
        self.log_save_path = script_dir
        
        try:
            with open(self.setup_file_path, 'w', encoding='utf-8') as file:
                file.write(f"{self.log_save_path}\n")
                for i in range(1, 11):
                    file.write(f"{i:02d}:Button {i}\n")
            self.custom_commands = {f"{i:02d}": f"Button {i}" for i in range(1, 11)}
            messagebox.showinfo("파일 생성", f"새로운 setup.txt 파일을 생성했습니다: {self.setup_file_path}")
        except Exception as e:
            messagebox.showerror("파일 생성 오류", f"setup.txt 파일 생성 중 오류가 발생했습니다: {str(e)}")

    def create_custom_buttons(self):
        for i in range(1, 11):
            number = f"{i:02d}"
            command = self.custom_commands.get(number, f"Button {i}")
            btn = ttk.Button(self.custom_buttons_frame, text=command, 
                             command=lambda cmd=command: self.send_custom_command(cmd))
            btn.pack(side=tk.LEFT, padx=2, pady=2)

    def send_custom_command(self, command):
        if command != f"Button {command.split()[-1]}":
            self.cmd_entry.delete(0, tk.END)
            self.cmd_entry.insert(0, command)
            self.send_command()

    def change_log_path(self):
        new_path = filedialog.askdirectory()
        if new_path:
            self.log_save_path = new_path
            self.log_path_entry.delete(0, tk.END)
            self.log_path_entry.insert(0, self.log_save_path)
            self.update_setup_file()

    def update_setup_file(self):
        try:
            with open(self.setup_file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
            
            lines[0] = self.log_save_path + '\n'
            
            with open(self.setup_file_path, 'w', encoding='utf-8') as file:
                file.writelines(lines)
            messagebox.showinfo("설정 업데이트", "저장 경로가 setup.txt 파일에 업데이트되었습니다.")
        except Exception as e:
            messagebox.showerror("설정 파일 업데이트 오류", f"setup.txt 파일 업데이트 중 오류가 발생했습니다: {str(e)}")

    def toggle_logging(self):
        if self.is_logging:
            self.stop_logging()
        else:
            self.start_logging()

    def start_logging(self):
        user_filename = self.log_name_entry.get().strip()
        current_time = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if user_filename:
            file_name = f"{user_filename}_{current_time}.log"
        else:
            file_name = f"project_name_{current_time}.log"
        
        file_path = os.path.join(self.log_save_path, file_name)
        
        try:
            self.log_file = open(file_path, 'w', encoding='utf-8')
            self.is_logging = True
            self.save_button.config(text="저장 중지")
            messagebox.showinfo("로깅 시작", f"로그 저장을 시작합니다: {file_path}")
        except Exception as e:
            messagebox.showerror("저장 오류", f"로그 저장 시작 중 오류가 발생했습니다: {str(e)}")

    def stop_logging(self):
        if self.log_file:
            self.log_file.close()
            self.log_file = None
        self.is_logging = False
        self.save_button.config(text="저장 시작")
        messagebox.showinfo("로깅 중지", "로그 저장을 중지했습니다.")

    def update_log(self, data):
        log_entry = f"[{self.get_timestamp()}] {data}\n"
        self.log_text.insert(tk.END, log_entry)
        if self.is_logging and self.log_file:
            self.log_file.write(log_entry)
            self.log_file.flush()
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)

    def get_timestamp(self):
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def toggle_repeat(self):
        if self.repeat_var.get():
            self.start_repeat()
        else:
            self.stop_repeat()

    def start_repeat(self):
        self.is_repeating = True
        self.repeat_count = 0
        self.repeat_count_label.config(text="반복 횟수: 0")
        self.repeat_command()

    def stop_repeat(self):
        self.is_repeating = False

    def repeat_command(self):
        if self.is_repeating:
            self.send_command()
            try:
                interval = int(float(self.repeat_interval_entry.get()) * 1000)
            except ValueError:
                interval = 1000
            self.master.after(interval, self.repeat_command)

    def on_closing(self):
        self.stop_repeat()
        if self.is_logging:
            self.stop_logging()
        if self.serial and self.serial.is_open:
            self.serial.close()

class DualUARTLogViewer:
    def __init__(self, master):
        self.master = master
        master.title("듀얼 UART 로그 뷰어")
        
        # 화면을 좌우로 분할
        self.left_frame = ttk.Frame(master)
        self.left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.right_frame = ttk.Frame(master)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 각 프레임에 UARTLogViewer 인스턴스 생성
        self.left_viewer = UARTLogViewer(master, self.left_frame)
        self.right_viewer = UARTLogViewer(master, self.right_frame)

    def on_closing(self):
        self.left_viewer.on_closing()
        self.right_viewer.on_closing()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = DualUARTLogViewer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()