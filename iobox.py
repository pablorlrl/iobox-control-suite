import tkinter as tk
from tkinter import ttk
import serial
from serial.tools.list_ports import comports
import threading

class IoBoxGui:
    def __init__(self, master):
        self.master = master
        self.master.title("IoBox Service GUI")

        # Serial port selection
        ttk.Label(master, text="Select Serial Port:").grid(row=0, column=0, padx=10, pady=10)
        self.serial_port_combo = ttk.Combobox(master, values=self.get_serial_ports())
        self.serial_port_combo.grid(row=0, column=1, padx=10, pady=10)
        if self.serial_port_combo['values']:
            self.serial_port_combo.current(0)

        # Operation selection
        ttk.Label(master, text="Select Operation:").grid(row=1, column=0, padx=10, pady=10)
        self.operation_combo = ttk.Combobox(master, values=[
            "ver", "id get", "id set", "relay on", "relay off", "relay read", "relay readall",
            "gpio set", "gpio clear", "gpio read", "gpio readall", "adc read"
        ])
        self.operation_combo.grid(row=1, column=1, padx=10, pady=10)
        self.operation_combo.current(0)

        # IO Number input
        ttk.Label(master, text="IO Number:").grid(row=2, column=0, padx=10, pady=10)
        self.io_number_entry = ttk.Entry(master)
        self.io_number_entry.grid(row=2, column=1, padx=10, pady=10)

        # ID String input
        ttk.Label(master, text="ID String (8 characters):").grid(row=3, column=0, padx=10, pady=10)
        self.id_str_entry = ttk.Entry(master)
        self.id_str_entry.grid(row=3, column=1, padx=10, pady=10)

        # Hex Value input
        ttk.Label(master, text="Hex Value:").grid(row=4, column=0, padx=10, pady=10)
        self.hex_val_entry = ttk.Entry(master)
        self.hex_val_entry.grid(row=4, column=1, padx=10, pady=10)

        # Execute button
        ttk.Button(master, text="Execute", command=self.execute_operation).grid(row=5, column=0, columnspan=2, padx=10, pady=10)

        # Help label showing all valid commands
        help_text = (
            "IOBox Command Reference:\n"
            "• ver\n"
            "• id get\n"
            "• id set {idStr}  →  ID must be exactly 8 characters\n"
            "• relay {on/off/read} {ioNumber}, relay readall, relay writeall {hexval}\n"
            "• gpio {set/clear/read} {ioNumber}, gpio readall, gpio writeall {hexval}\n"
            "• adc read {ioNumber}"
        )
        self.help_label = ttk.Label(master, text=help_text, justify="left", wraplength=400)
        self.help_label.grid(row=6, column=0, columnspan=2, padx=10, pady=(0, 10))

        # Status output
        self.status_text = tk.Text(master, height=4, width=50)
        self.status_text.grid(row=7, column=0, columnspan=2, padx=10, pady=10)

        # Start auto-refresh for COM ports
        self.refresh_ports()

    def get_serial_ports(self):
        return [port.device for port in comports()]

    def refresh_ports(self):
        current_selection = self.serial_port_combo.get()
        ports = self.get_serial_ports()
        if ports != list(self.serial_port_combo['values']):
            self.serial_port_combo['values'] = ports
            if current_selection in ports:
                self.serial_port_combo.set(current_selection)
            elif ports:
                self.serial_port_combo.current(0)
        self.master.after(3000, self.refresh_ports)  # Repeat every 3 seconds

    def execute_operation(self):
        port_name = self.serial_port_combo.get()
        operation = self.operation_combo.get()
        io_number = int(self.io_number_entry.get()) if self.io_number_entry.get() else None
        id_str = self.id_str_entry.get() if self.id_str_entry.get() else None
        hex_val = self.hex_val_entry.get() if self.hex_val_entry.get() else None
        try:
            self.status_text.insert(tk.END, f"Executing operation: {operation}\n")
            threading.Thread(target=self.send_command, args=(port_name, operation, io_number, id_str, hex_val)).start()
        except Exception as e:
            self.status_text.insert(tk.END, f"Error executing operation: {str(e)}\n")

    def send_command(self, port_name, operation, io_number, id_str, hex_val):
        try:
            with serial.Serial(port=port_name, baudrate=19200, timeout=1) as ser:
                cmd = self.construct_command(operation, io_number, id_str, hex_val)
                ser.write(cmd.encode() + b"\r")
                response = ser.readline().decode().strip()
                self.status_text.insert(tk.END, f"Response: {response}\n")
        except serial.SerialException as se:
            self.status_text.insert(tk.END, f"Serial port error: {str(se)}\n")
        except Exception as e:
            self.status_text.insert(tk.END, f"Error: {str(e)}\n")

    def construct_command(self, operation, io_number, id_str, hex_val):
        if operation in ["id set", "id get"]:
            return f"{operation} {id_str}"
        elif operation.startswith(("relay", "gpio")) or operation == "adc read":
            return f"{operation} {io_number}"
        elif operation.endswith("all"):
            return f"{operation} {hex_val}"
        elif operation == "ver":
            return operation
        else:
            raise ValueError(f"Unsupported operation: {operation}")

def main():
    root = tk.Tk()
    app = IoBoxGui(root)
    root.mainloop()

if __name__ == "__main__":
    main()
