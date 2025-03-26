import tkinter as tk
from tkinter import ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import random

# Create main window
root = tk.Tk()
root.title("Torsional Testing Machine Control System")
root.configure(bg="black")
root.geometry("1284x864") #standard 13x9 window

# Label, Button, and Entry styles
label_style = {"bg": "black", "fg": "white", "font": ("Arial", 12)}
button_style = {"bg": "white", "fg": "black", "font": ("Arial", 12, "bold")}
entry_style = {"bg": "white", "fg": "black", "font": ("Arial", 12), "width": 25}

# Title Label
title_label = tk.Label(root, text="Torsional Testing Machine Control System", 
                       bg="black", fg="white", font=("Arial", 16, "bold"))
title_label.grid(row=0, column=0, columnspan=3, pady=10)

# Move Direction of Twist above Angle of Twist
tk.Label(root, text="Direction of Twist (cw/ccw):", **label_style).grid(row=1, column=0, sticky="w", padx=20, pady=5)

# Frame for CW & CCW Buttons (merged appearance)
direction_frame = tk.Frame(root, bg="black")
direction_frame.grid(row=2, column=0, sticky="w", padx=20, pady=5)

cw_button = tk.Button(direction_frame, text="Clockwise", **button_style, borderwidth=4, highlightthickness=0)
cw_button.pack(side=tk.LEFT, ipadx=30)  # Expand width but no space between

ccw_button = tk.Button(direction_frame, text="Counter-clockwise", **button_style, borderwidth=4, highlightthickness=0)
ccw_button.pack(side=tk.LEFT, ipadx=30)  # Matches CW width, no space

# Input Fields with Tare Buttons
labels = [
    "Angle of Twist (degrees):",
    "Speed of Rotation (degrees/second):",
    "Torque Loss % to trigger Breakpoint:",
]
entries = []
for i, text in enumerate(labels):
    tk.Label(root, text=text, **label_style).grid(row=i + 3, column=0, sticky="w", padx=20, pady=5)
    
    entry = tk.Entry(root, **entry_style)
    entry.grid(row=i + 3, column=1, pady=5)
    entries.append(entry)
    
    tare_button = tk.Button(root, text="Tare", **button_style)  
    tare_button.grid(row=i + 3, column=2, padx=10, pady=5)

# Define Home Button Function
def home_machine():
    print("Machine returning to home position...")  # Replace with actual machine reset logic

# Frame for Start, Stop, and Home buttons
start_stop_frame = tk.Frame(root, bg="black")
start_stop_frame.grid(row=6, column=0, columnspan=3, pady=10, padx=20, sticky="w")

start_button = tk.Button(start_stop_frame, text="Start Test", **button_style)
start_button.pack(side=tk.LEFT, padx=5) 

stop_button = tk.Button(start_stop_frame, text="Stop Test", **button_style)
stop_button.pack(side=tk.LEFT, padx=5)  

home_button = tk.Button(start_stop_frame, text="Home", **button_style, command=home_machine)
home_button.pack(side=tk.LEFT, padx=5)

# Spacer row
tk.Label(root, text="", bg="black").grid(row=13, column=0)  # Empty row
tk.Label(root, text="", bg="black").grid(row=14, column=0)  # Another empty row

# Measured Data
tk.Label(root, text="Measured Angle of Twist (Degrees):", **label_style).grid(row=15, column=0, sticky="w", padx=20, pady=5)
measured_twist = tk.Label(root, text="(Real-time data will appear here)", **label_style)
measured_twist.grid(row=15, column=1, sticky="w", pady=5)

tk.Label(root, text="Measured Torque (Nm):", **label_style).grid(row=16, column=0, sticky="w", padx=20, pady=5)
measured_torque = tk.Label(root, text="(Real-time data will appear here)", **label_style)
measured_torque.grid(row=16, column=1, sticky="w", pady=5)

# Save Data Button
save_button = tk.Button(root, text="Save Data", **button_style)
save_button.grid(row=9, column=1, pady=10)

# Graph/Table Toggle Frame
graph_frame = tk.Frame(root, bg="gray", width=250, height=200)
graph_frame.grid(row=1, column=3, rowspan=6, padx=20, sticky="n")

# Create a Figure for Matplotlib Graph
fig = Figure(figsize=(3, 2), dpi=100)
ax = fig.add_subplot(111)
ax.set_xlabel("Angle of Twist (degrees)")
ax.set_ylabel("Torque (Nm)")

# Sample Data for Graph
angles = list(range(0, 100, 10))
torques = [random.uniform(5, 20) for _ in angles]
ax.plot(angles, torques, marker="o", linestyle="-", color="blue")

# Embed the Matplotlib Graph in Tkinter
canvas = FigureCanvasTkAgg(fig, master=graph_frame)
canvas_widget = canvas.get_tk_widget()
canvas_widget.pack(fill=tk.BOTH, expand=True)

# Create a Table (Treeview)
table = ttk.Treeview(graph_frame, columns=("Angle", "Torque"), show="headings")
table.heading("Angle", text="Angle (degrees)")
table.heading("Torque", text="Torque (Nm)")
for angle, torque in zip(angles, torques):
    table.insert("", "end", values=(angle, round(torque, 2)))

# Toggle Function for Graph/Table
def toggle_view():
    global is_graph  # Fixes missing variable reference
    if is_graph:
        canvas_widget.pack_forget()
        table.pack(fill=tk.BOTH, expand=True)
        toggle_button.config(text="Switch To Graph")
    else:
        table.pack_forget()
        canvas_widget.pack(fill=tk.BOTH, expand=True)
        toggle_button.config(text="Switch To Table")
    is_graph = not is_graph

# Toggle Button (Now Centered Below Graph)
is_graph = True  # Default view is graph
toggle_button = tk.Button(root, text="Switch To Table", **button_style, command=toggle_view)
toggle_button.grid(row=8, column=3, pady=10, padx=20)  # Centered below graph

# Run the application
root.mainloop()

