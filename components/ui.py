import tkinter as tk
import numpy as np
import scipy.fft


class Ui:
    def __init__(self, params=None):
        self.params = params or {}
        self.window_title = self.params.get('window_title', None)
        self.window_size = self.params.get('window_size', None)
        self.icon = self.params.get('assets', None).get('icon', None)
        
        self.root = tk.Tk()
        self.root.title(self.window_title)
        icon_image = tk.PhotoImage(file=self.icon)
        self.root.iconphoto(True, icon_image)
        self.root.geometry(f"{self.window_size}x{self.window_size}")
        self.root.configure(bg="black")
        self.root.resizable(True, True)
        
        self.spectrum_widget = tk.Canvas(self.root, bg="black", width=self.window_size, height=int(int(self.window_size)/2))
        self.spectrum_widget.pack(expand=True, fill="both", padx=10, pady=10)
        
        self.center_x, self.center_y = int(int(self.window_size)/2), int(int(self.window_size)/4)
        self.radius = 100
        self.min_radius = 50
        self.circle = self.spectrum_widget.create_oval(self.center_x - self.radius,
                                              self.center_y - self.radius,
                                              self.center_x + self.radius,
                                              self.center_y + self.radius,
                                              outline="white", width=2, fill="white")
        
        self.scrollbar = tk.Scrollbar(self.root, bg="black")
        self.scrollbar.pack(side="right", fill="y")                        
        self.text_widget = tk.Text(self.root, 
                                   bg="black", 
                                   fg="white", 
                                   wrap="word",
                                   yscrollcommand=self.scrollbar.set, 
                                   state="disabled")
        self.text_widget.pack(expand=True, fill="both", padx=10, pady=10)
        self.scrollbar.configure(command=self.text_widget.yview)
        
        self.context_menu = tk.Menu(self.root, tearoff=0, fg="white", bg="black")
        self.context_menu.add_command(label="Copy", command=self.copy_text, state="disabled")
        self.text_widget.bind("<Button-3>", self.show_context_menu)
        self.text_widget.bind("<Button-1>", self.close_context_menu)
        
        self.update_spectrum_viz("system", None)
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.kill = False
        
    def show_context_menu(self, event):
        self.context_menu.post(event.x_root, event.y_root)
        if self.text_widget.tag_ranges(tk.SEL):
            self.context_menu.entryconfig("Copy", state="normal")
        else:
            self.context_menu.entryconfig("Copy", state="disabled")
        self.context_menu.post(event.x_root, event.y_root)
    
    def close_context_menu(self, event):
        self.context_menu.unpost()
        
    def copy_text(self):
        if self.text_widget.tag_ranges(tk.SEL):
            selected_text = self.text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
            self.text_widget.clipboard_clear()
            self.text_widget.clipboard_append(selected_text)
        
    def update_spectrum_viz(self, user_name, data, time_color_warning=0):
        if user_name == "You":
            spectrum = np.abs(scipy.fft.fft(data))
            amplitude = spectrum.mean()
            max_percentage = 0.85
            max_radius = min(self.spectrum_widget.winfo_reqwidth(), self.spectrum_widget.winfo_reqheight()) * max_percentage / 2
            sensitivity_factor = 1500
            scaled_radius = min(amplitude * sensitivity_factor, max_radius)
            self.radius = int(0.8 * self.radius + 0.2 * max(scaled_radius, self.min_radius))
            self.spectrum_widget.delete("all")
            current_window_width = self.root.winfo_width()
            current_window_height = self.root.winfo_height()
            self.center_x, self.center_y = int(int(current_window_width)/2), int(int(current_window_height)/4)
            oval_coords = (
                self.center_x - self.radius,
                self.center_y - self.radius,
                self.center_x + self.radius,
                self.center_y + self.radius
            )
            if 0 < time_color_warning < 0.5:
                color = "#FF0000"
            elif 0.5 < time_color_warning < 1:
                color = "#B93C3C"
            elif 1 < time_color_warning < 1.5:
                color = "#8A4B4B"
            elif 1.5 < time_color_warning < 2:
                color = "#584848"
            else:
                color = "#FFFFFF"
            self.spectrum_widget.create_oval(oval_coords, outline=color, width=2, fill=color)
            self.spectrum_widget.update()
        elif user_name == "Aria":
            self.spectrum_widget.delete("all")
            self.spectrum_widget.update()
        elif user_name == "system":
            self.spectrum_widget.delete("all")
            self.spectrum_widget.update()

    def add_message(self, user_name, text, new_entry=False, color_code_block=False):
        color = "white"
        if "You" in user_name:
            color = '#71CA2C'
        elif "Aria" in user_name:
            color = "#7441B1"
        try:
            self.text_widget.config(state="normal")
            if new_entry:
                self.text_widget.insert("end", '\n\n' + user_name + ": ", (color, "bold"))
            if color_code_block:
                color = "#2C87CA"
                self.text_widget.insert("end", text, (color))
            else:
                self.text_widget.insert("end", text, "normal")        
            self.text_widget.tag_configure(color, foreground=color)
            self.text_widget.tag_configure("bold", font=("Arial", 12, "bold"))
            self.text_widget.config(state="disabled")
            self.text_widget.update()
            self.text_widget.see("end")
        except:
            pass
    
    def on_closing(self):
        self.root.destroy()
        self.kill = True
        
    def start(self):
        try:
            self.root.mainloop()
        except:
            pass
