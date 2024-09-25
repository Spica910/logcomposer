import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import os
import sys
import queue
import time
import threading
from ui_components import TopFrame, LogFrame, LogDisplay, CommandFrame, CustomButtonsFrame
from log_handler import LogHandler
from uart_handler import UARTHandler
from utils import get_script_dir, get_timestamp, prevent_screen_sleep, allow_screen_sleep
from setup import create_default_setup_file, load_custom_commands, update_setup_file

class UARTLogViewer:
    def __init__(self, master):
        self.master = master
        master.title("UART 로그 뷰어")
        self.setup_ui()
        self.initialize_variables()
        self.load_custom_commands()
        self.create_custom_buttons()
        self.refresh_ports()
        
        self.log_queue = queue.Queue()
        self.log_thread = threading.Thread(target=self.process_log_queue, daemon=True)
        self.log_thread.start()
        
        self.command_queue = queue.Queue()
        self.command_thread = threading.Thread(target=self.process_command_queue, daemon=True)
        self.command_thread.start()
        
        self.uart_thread = threading.Thread(target=self.read_uart_loop, daemon=True)
        self.uart_thread.start()

    def setup_ui(self):
        self.top_frame = TopFrame(self.master, self.refresh_ports, self.toggle_connection, self.toggle_prevent_sleep)
        self.log_frame = LogFrame(self.master, self.change_log_path, self.toggle_logging, self.clear_log, self.update_log_color)
        self.log_display = LogDisplay(self.master)
        self.command_frame = CommandFrame(self.master, self.send_command, self.toggle_repeat)
        self.custom_buttons_frame = CustomButtonsFrame(self.master)

    def initialize_variables(self):
        self.uart_handler = UARTHandler()
        self.log_handler = LogHandler(self.log_display.log_text)
        self.is_repeating = False
        self.repeat_count = 0
        self.custom_commands = {}
        self.log_save_path = get_script_dir()
        self.setup_file_path = os.path.join(self.log_save_path, 'setup.txt')

    def refresh_ports(self):
        ports = self.uart_handler.get_ports()
        self.top_frame.port_combo['values'] = ports
        if ports:
            self.top_frame.port_combo.set(ports[0])

    def toggle_connection(self):
        if self.uart_handler.is_connected():
            self.uart_handler.disconnect()
            self.top_frame.connect_button.config(text="연결")
        else:
            port = self.top_frame.port_combo.get()
            baud = int(self.top_frame.baud_combo.get())
            success, message = self.uart_handler.connect(port, baud)
            if success:
                self.top_frame.connect_button.config(text="연결 끊기")
                # self.master.after(10, self.read_uart)  # 이 줄을 제거하거나 주석 처리
            else:
                self.log_handler.update_log(f"연결 오류: {message}")

    def read_uart_loop(self):
        while True:
            if self.uart_handler.is_connected():
                data = self.uart_handler.read_data()
                if data == "COM_PORT_DISCONNECTED":
                    self.handle_com_port_disconnection()
                elif data:
                    timestamp = get_timestamp()
                    self.log_queue.put(f"{timestamp} - {data}")
                else:
                    time.sleep(0.001)
            else:
                time.sleep(0.1)

    def handle_com_port_disconnection(self):
        self.log_queue.put("COM 포트 연결이 끊어졌습니다.")
        self.master.after_idle(self.update_ui_after_disconnection)

    def update_ui_after_disconnection(self):
        self.top_frame.connect_button.config(text="연결")
        messagebox.showwarning("연결 해제", "COM 포트 연결이 끊어졌습니다.")

    def process_log_queue(self):
        while True:
            try:
                messages = []
                for _ in range(100):  # 최대 100개의 메시지를 한 번에 처리
                    messages.append(self.log_queue.get_nowait())
            except queue.Empty:
                pass
            
            if messages:
                self.log_handler.update_log_batch(messages)
            
            time.sleep(0.01)  # 10ms 대기

    def send_command(self, event=None):
        if self.uart_handler.is_connected():
            command = self.command_frame.cmd_entry.get()
            if command:
                success, message = self.uart_handler.write_data(command)
                if success:
                    self.log_queue.put(f"전송: {command}")
                    if not self.command_frame.repeat_var.get():
                        self.command_frame.cmd_entry.delete(0, tk.END)
                elif message == "COM_PORT_DISCONNECTED":
                    self.handle_com_port_disconnection()
                else:
                    self.log_queue.put(f"전송 실패: {message}")

    def process_command_queue(self):
        while True:
            try:
                command = self.command_queue.get(timeout=0.1)
                success, message = self.uart_handler.write_data(command)
                if success:
                    self.log_queue.put(f"전송: {command}")
                    self.master.after_idle(self.update_repeat_count)
                elif message == "COM_PORT_DISCONNECTED":
                    self.handle_com_port_disconnection()
                else:
                    self.log_queue.put(f"전송 실패: {message}")
            except queue.Empty:
                continue

    def update_repeat_count(self):
        if self.is_repeating:
            self.repeat_count += 1
            self.master.after_idle(lambda: self.command_frame.repeat_count_label.config(text=f"반복 횟수: {self.repeat_count}"))

    def toggle_logging(self):
        if self.log_handler.is_logging:
            self.log_handler.stop_logging()
            self.master.after_idle(lambda: self.log_frame.save_button.config(text="저장 시작"))
        else:
            success, file_path = self.log_handler.start_logging(
                self.log_save_path, 
                self.log_frame.log_name_entry.get()
            )
            if success:
                self.master.after_idle(lambda: self.log_frame.save_button.config(text="저장 중지"))
            else:
                self.master.after_idle(lambda: messagebox.showerror("로그 저장 오류", f"로그 파일을 생성할 수 없습니다: {file_path}"))

    def toggle_repeat(self):
        if self.command_frame.repeat_var.get():
            self.start_repeat()
        else:
            self.stop_repeat()

    def start_repeat(self):
        self.is_repeating = True
        self.repeat_count = 0
        self.command_frame.repeat_count_label.config(text="반복 횟수: 0")
        self.repeat_command()

    def stop_repeat(self):
        self.is_repeating = False

    def repeat_command(self):
        if self.is_repeating:
            self.send_command()
            try:
                interval = int(float(self.command_frame.repeat_interval_entry.get()) * 1000)
            except ValueError:
                interval = 1000
            self.master.after(interval, self.repeat_command)

    def clear_log(self):
        self.log_handler.clear_log()

    def update_log_color(self):
        self.log_handler.update_log_color(self.log_frame.color_var, self.log_frame.color_entry.get())

    def toggle_prevent_sleep(self):
        if self.top_frame.prevent_sleep_var.get():
            prevent_screen_sleep()
        else:
            allow_screen_sleep()

    def load_custom_commands(self):
        if not os.path.exists(self.setup_file_path):
            self.custom_commands = create_default_setup_file(self.setup_file_path, self.log_save_path)
        else:
            self.log_save_path, self.custom_commands = load_custom_commands(self.setup_file_path)

        self.log_frame.log_path_entry.delete(0, tk.END)
        self.log_frame.log_path_entry.insert(0, self.log_save_path)

    def create_custom_buttons(self):
        for i in range(1, 11):
            number = f"{i:02d}"
            command = self.custom_commands.get(number, f"Button {i}")
            btn = ttk.Button(self.custom_buttons_frame.frame, text=command, 
                             command=lambda cmd=command: self.send_custom_command(cmd))
            btn.pack(side=tk.LEFT, padx=2, pady=2)

    def send_custom_command(self, command):
        if command != f"Button {command.split()[-1]}":
            self.command_frame.cmd_entry.delete(0, tk.END)
            self.command_frame.cmd_entry.insert(0, command)
            self.send_command()

    def change_log_path(self):
        new_path = filedialog.askdirectory()
        if new_path:
            self.log_save_path = new_path
            self.log_frame.log_path_entry.delete(0, tk.END)
            self.log_frame.log_path_entry.insert(0, self.log_save_path)
            success, error = update_setup_file(self.setup_file_path, self.log_save_path)
            if success:
                messagebox.showinfo("설정 업데이트", "저장 경로가 setup.txt 파일에 업데이트되었습니다.")
            else:
                messagebox.showerror("설정 파일 업데이트 오류", f"setup.txt 파일 업데이트 중 오류가 발생했습니다: {error}")

    def on_closing(self):
        self.stop_repeat()
        self.log_handler.stop_logging()
        self.uart_handler.disconnect()
        self.master.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = UARTLogViewer(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()