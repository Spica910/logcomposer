import os

def create_default_setup_file(setup_file_path, log_save_path):
    try:
        with open(setup_file_path, 'w', encoding='utf-8') as file:
            file.write(f"{log_save_path}\n")
            for i in range(1, 11):
                file.write(f"{i:02d}:Button {i}\n")
        return {f"{i:02d}": f"Button {i}" for i in range(1, 11)}
    except Exception as e:
        return None, str(e)

def load_custom_commands(setup_file_path):
    try:
        with open(setup_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
            log_save_path = lines[0].strip()
            custom_commands = {}
            for line in lines[1:]:
                parts = line.strip().split(':', 1)
                if len(parts) == 2:
                    number, command = parts
                    custom_commands[number.strip()] = command.strip()
        return log_save_path, custom_commands
    except Exception as e:
        return None, None, str(e)

def update_setup_file(setup_file_path, log_save_path):
    try:
        with open(setup_file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        lines[0] = log_save_path + '\n'
        
        with open(setup_file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        return True, None
    except Exception as e:
        return False, str(e)
