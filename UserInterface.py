
import tkinter as tk
from tkinter import ttk, messagebox
import serial
import serial.tools.list_ports
import threading
import time
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tkinter import filedialog
import csv

# ========== Global Variables ==========
ser = None
last_command_time = 0
COMMAND_INTERVAL = 0.1  # seconds
is_graph = True
is_angle_graph = True
live_data = []  # Stores (angle, torque) tuples
serial_connected = False
start_time = None
elapsed_time = 0
stopwatch_running = False

# ========== Serial Communication ==========
def connect_serial():
    global ser, serial_connected
    try:
        ports = list(serial.tools.list_ports.comports())
        if not ports:
            raise serial.SerialException("No serial devices found.")
        port_name = ports[0].device
        ser = serial.Serial(port_name, 9600, timeout=1)
        serial_connected = True
        serial_led.config(bg="green")
        threading.Thread(target=read_serial_data, daemon=True).start()
        print(f"Connected to {port_name}")
    except serial.SerialException as e:
        messagebox.showerror("Serial Error", f"Failed to connect to serial device:\n{e}")
        ser = None
        serial_connected = False
        serial_led.config(bg="red")

def send_serial_command(command):
    global last_command_time
    current_time = time.time()
    if ser and (current_time - last_command_time >= COMMAND_INTERVAL):
        try:
            ser.write((command + '\n').encode())
            last_command_time = current_time
        except serial.SerialException:
            messagebox.showerror("Serial Error", "Serial connection lost.")
            ser.close()
            serial_led.config(bg="red")

def read_serial_data():
    global ser
    while True:
        if ser and ser.in_waiting:
            try:
                line = ser.readline().decode().strip()
                if line.startswith("ANGLE:"):
                    parts = line.split(",")
                    angle_val = float(parts[0].split(":")[1])
                    torque_val = float(parts[1].split(":")[1])
                    update_live_data(angle_val, torque_val)
            except Exception as e:
                print("Serial Read Error:", e)
        time.sleep(0.05)

# ========== Data Handling ==========
def update_live_data(angle, torque):
    if stopwatch_running:
        time_stamp = time.time() - start_time
    else:
        time_stamp = elapsed_time  # fallback

    live_data.append((angle, torque, time_stamp))

    measured_twist.config(text=f"{angle:.2f} °")
    measured_torque.config(text=f"{torque:.5f} Nm")

    if is_angle_graph:
        ax.cla()
        ax.set_xlabel("Angle (degrees)")
        ax.set_ylabel("Torque (Nm)")
        angles, torques = zip(*[(a, t) for a, t, _ in live_data])
        ax.plot(angles, torques, marker="o", color="blue")
    else:
        ax.cla()
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Torque (Nm)")
        times, torques = zip(*[(_, t) for a, t, _ in live_data])
        ax.plot(times, torques, marker="o", color="blue")
    canvas.draw()

    # update table
    row_id = table.insert("", "end", values=(f"{angle:.2f}", f"{torque:.5f}", f"{time_stamp:.2f}"))
    table.see(row_id)


def start_stopwatch():
    global start_time, stopwatch_running
    start_time = time.time()
    stopwatch_running = True
    update_stopwatch()

def stop_stopwatch():
    global stopwatch_running
    stopwatch_running = False

def update_stopwatch():
    if stopwatch_running:
        global elapsed_time
        elapsed_time = time.time() - start_time
        time_elapsed_label.config(text=f"{elapsed_time:.2f} s")
        root.after(100, update_stopwatch)

# ========== GUI Functions ==========
def start_machine():
    send_serial_command("START")
    start_stopwatch()

def stop_machine():
    send_serial_command("STOP")
    stop_stopwatch()

def cw_set():
    send_serial_command("DIRECTION CW")
    direction_status.config(text="Clockwise")

def ccw_set():
    send_serial_command("DIRECTION CCW")
    direction_status.config(text="Counter-clockwise")

def set_target_angle():
    val = angle_entry.get()
    try:
        angle = float(val)
        send_serial_command(f"SET ANGLE {angle}")
        target_angle_label.config(text=f"{angle:.2f} °")
    except ValueError:
        messagebox.showwarning("Invalid Input", "Enter a valid angle.")

def set_target_speed():
    val = speed_entry.get()
    try:
        speed = float(val)
        send_serial_command(f"SET SPEED {speed}")
        target_speed_label.config(text=f"{speed:.2f} °/min")
    except ValueError:
        messagebox.showwarning("Invalid Input", "Enter a valid speed.")

def tare_torque():
    send_serial_command("TARE")

def set_calibration_factor():
    val = calibration_entry.get()
    try:
        factor = float(val)
        send_serial_command(f"SET CALIBRATION {factor}")
    except ValueError:
        messagebox.showwarning("Invalid Input", "Enter a valid number.")

def toggle_view():
    global is_graph
    if is_graph:
        canvas_widget.pack_forget()
        table.pack(fill=tk.BOTH, expand=True)
        toggle_button.config(text="Switch To Graph")
    else:
        table.pack_forget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        toggle_button.config(text="Switch To Table")
    is_graph = not is_graph

def toggle_graph_type():
    global is_angle_graph
    if is_graph:
        if is_angle_graph:
            toggle_graph_button.config(text="(Graph) Angle/Torque")
        else:
            toggle_graph_button.config(text="(Graph) Time/Torque")
        is_angle_graph = not is_angle_graph
    else:
        messagebox.showinfo("Graph Not Active", "Switch to graph to change graph type.")

def erase_graph_and_table():
    global live_data
    live_data.clear()
    ax.cla()
    if is_angle_graph:
        ax.set_xlabel("Angle (degrees)")
        ax.set_ylabel("Torque (Nm)")
    else:
        ax.set_xlabel("Time (seconds)")
        ax.set_ylabel("Torque (Nm)")
    canvas.draw()
    for row in table.get_children():
        table.delete(row)

def save_data_to_csv():
    if not live_data:
        messagebox.showinfo("No Data", "There is no data to save.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        title="Save data as..."
    )
    if file_path:
        try:
            with open(file_path, mode='w', newline='') as file:
                writer = csv.writer(file)
                writer.writerow(["Angle (°)", "Torque (Nm)", "Time (s)"])
                writer.writerows(live_data)
            messagebox.showinfo("Success", f"Data saved to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save file:\n{e}")

# ========== GUI Setup ==========
root = tk.Tk()
root.title("Torsional Testing Machine Control System")
root.geometry("1284x864")
root.configure(bg="black")
label_style = {"bg": "black", "fg": "white", "font": ("Arial", 12)}
button_style = {"bg": "white", "fg": "black", "font": ("Arial", 12, "bold")}
entry_style = {"bg": "white", "fg": "black", "font": ("Arial", 12), "width": 25}

# Title
tk.Label(root, text="Torsional Testing Machine Control System", bg="black", fg="white", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=4, pady=10)

# Serial LED
tk.Label(root, text="Arduino Status:", **label_style).grid(row=1, column=0, sticky="w", padx=20)
serial_led = tk.Label(root, bg="red", width=2, height=1)
serial_led.grid(row=1, column=1, sticky="w", pady=5)

# Direction Controls
tk.Label(root, text="Direction of Twist:", **label_style).grid(row=2, column=0, sticky="w", padx=20)
direction_frame = tk.Frame(root, bg="black")
direction_frame.grid(row=2, column=1, pady=5)
tk.Button(direction_frame, text="Clockwise", command=cw_set, **button_style).pack(side=tk.LEFT, padx=5)
tk.Button(direction_frame, text="Counter-Clockwise", command=ccw_set, **button_style).pack(side=tk.LEFT, padx=5)

# Input Controls
tk.Label(root, text="Target Angle (°):", **label_style).grid(row=3, column=0, sticky="w", padx=20)
angle_entry = tk.Entry(root, **entry_style)
angle_entry.grid(row=3, column=1)
tk.Button(root, text="Set", command=set_target_angle, **button_style).grid(row=3, column=2, padx=10, pady=(0,5))

tk.Label(root, text="Speed (°/min):", **label_style).grid(row=4, column=0, sticky="w", padx=20)
speed_entry = tk.Entry(root, **entry_style)
speed_entry.grid(row=4, column=1)
tk.Button(root, text="Set", command=set_target_speed, **button_style).grid(row=4, column=2, padx=10, pady=(0,5))

tk.Label(root, text="Calibration Factor:", **label_style).grid(row=5, column=0, sticky="w", padx=20)
calibration_entry = tk.Entry(root, **entry_style)
calibration_entry.grid(row=5, column=1)
tk.Button(root, text="Set", command=set_calibration_factor, **button_style).grid(row=5, column=2, padx=10, pady=(0,5))

tk.Button(root, text="Tare Torque", command=tare_torque, **button_style).grid(row=6, column=1, pady=10)

# Start/Stop/Clear
start_stop_frame = tk.Frame(root, bg="black")
start_stop_frame.grid(row=7, column=0, columnspan=3, pady=10)
tk.Button(start_stop_frame, text="Start Test", command=start_machine, **button_style).pack(side=tk.LEFT, padx=5)
tk.Button(start_stop_frame, text="Stop Test", command=stop_machine, **button_style).pack(side=tk.LEFT, padx=5)
tk.Button(start_stop_frame, text="Erase Graph/Table", command=erase_graph_and_table, **button_style).pack(side=tk.LEFT, padx=5)

# Live Data
info_frame = tk.Frame(root, bg="black")
info_frame.grid(row=8, column=0, columnspan=2, sticky="w", padx=30)
tk.Label(info_frame, text="Measured Angle of Twist:", **label_style).grid(row=0, column=0, sticky="w")
measured_twist = tk.Label(info_frame, text="0.00 °", **label_style)
measured_twist.grid(row=0, column=1, sticky="w")

tk.Label(info_frame, text="Measured Torque:", **label_style).grid(row=1, column=0, sticky="w")
measured_torque = tk.Label(info_frame, text="0.00000 Nm", **label_style)
measured_torque.grid(row=1, column=1, sticky="w")

tk.Label(info_frame, text="Time Elapsed:", **label_style).grid(row=2, column=0, sticky="w")
time_elapsed_label = tk.Label(info_frame, text="0.00 s", **label_style)
time_elapsed_label.grid(row=2, column=1, sticky="w")

tk.Label(info_frame, text="Target Angle:", **label_style).grid(row=3, column=0, sticky="w")
target_angle_label = tk.Label(info_frame, text="0.00 °", **label_style)
target_angle_label.grid(row=3, column=1, sticky="w")

tk.Label(info_frame, text="Set Speed:", **label_style).grid(row=4, column=0, sticky="w")
target_speed_label = tk.Label(info_frame, text="0.00 °/min", **label_style)
target_speed_label.grid(row=4, column=1, sticky="w")

tk.Label(info_frame, text="Direction: ", **label_style).grid(row=5, column=0, sticky="w")
direction_status = tk.Label(info_frame, text="Not Set", **label_style)
direction_status.grid(row=5, column=1, sticky="w")

# Plot/Table Frame
graph_frame = tk.Frame(root, bg="gray", width=400, height=300)
graph_frame.grid(row=1, column=3, rowspan=10, padx=20, sticky="n")

fig = Figure(figsize=(5, 4), dpi=100)
ax = fig.add_subplot(111)
ax.set_xlabel("Angle (degrees)")
ax.set_ylabel("Torque (Nm)")
canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill=tk.BOTH, expand=True)

table = ttk.Treeview(graph_frame, columns=("Angle", "Torque", "Time"), show="headings")
table.heading("Angle", text="Angle (°)")
table.heading("Torque", text="Torque (Nm)")
table.heading("Time", text="Time (s)")

# Toggle Button
toggle_button = tk.Button(root, text="Switch To Table", command=toggle_view, **button_style)
toggle_button.grid(row=12, column=3, pady=10)

# Toggle Graph between angle/torque and time/torque
toggle_graph_button = tk.Button(root, text="(Graph) Time/Torque", command=toggle_graph_type, **button_style)
toggle_graph_button.grid(row=13, column=3, pady=10)

# Save Data Button
tk.Button(root, text="Save Data", command=save_data_to_csv, **button_style).grid(row=14, column=3, pady=5)

# Connect and Start GUI
connect_serial()
root.mainloop()
