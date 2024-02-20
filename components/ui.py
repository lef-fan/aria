import tkinter as tk
import numpy as np
import scipy.fft
from PIL import Image, ImageTk, ImageSequence


class Ui:
    def __init__(self, params=None):
        self.params = params or {}
        self.window_title = self.params.get('window_title', None)
        self.window_size = self.params.get('window_size', None)
        self.icon = self.params.get('assets', None).get('icon', None)
        self.loading_gif = self.params.get('assets', None).get('loading_gif', None)
        self.transition_gif = self.params.get('assets', None).get('transition_gif', None)
        self.muted_mic_gif = self.params.get('assets', None).get('muted_mic_gif', None)
        
        self.root = tk.Tk()
        self.root.title(self.window_title)
        icon_image = tk.PhotoImage(file=self.icon)
        self.root.iconphoto(True, icon_image)
        self.root.geometry(f"{self.window_size}x{self.window_size}")
        self.root.configure(bg="black")
        self.root.resizable(True, True)
        
        self.visual_widget = tk.Canvas(
            self.root, 
            bg="black", 
            width=self.window_size, 
            height=int(int(self.window_size)/2))
        self.visual_widget.pack(expand=True, fill="both", padx=10, pady=10)
        
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
        
        loading_gif = Image.open(self.loading_gif)
        self.loading_frames = [
            ImageTk.PhotoImage(frame.convert("RGBA").resize((250, 250), Image.ANTIALIAS)) 
            for frame in ImageSequence.Iterator(loading_gif)]
        
        transition_gif = Image.open(self.transition_gif)
        self.transition_frames = [
            ImageTk.PhotoImage(frame.convert("RGBA").resize((250, 250), Image.ANTIALIAS)) 
            for frame in ImageSequence.Iterator(transition_gif)]

        muted_mic_gif = Image.open(self.muted_mic_gif)
        self.muted_mic_frames = [
            ImageTk.PhotoImage(frame.convert("RGBA").resize((250, 250), Image.ANTIALIAS)) 
            for frame in ImageSequence.Iterator(muted_mic_gif)]
        
        self.visual_x = int(int(self.window_size)/2)
        self.visual_y = int(int(self.window_size)/4)
        
        self.listening_color = "#FFFFFF"
        self.listening_max_percentage = 0.85
        self.listening_sensitivity_factor = 1000
        self.listening_min_radius = 50
        self.listening_radius = 100
        
        self.speaking_BAR_COUNT = 5
        # self.speaking_MIN_SIZES = [10, 30, 50, 30, 10]
        self.speaking_MIN_SIZES = [0, 2, 5, 2, 0]
        self.speaking_MAX_SIZES = [70, 90, 110, 90, 70]
        self.speaking_BAR_WIDTH = 20
        self.speaking_BAR_SPACING = 10
        
        you_color = '#71CA2C'
        aria_color = "#7441B1"
        code_color = "#2C87CA"
        self.text_widget.tag_configure("user_name_You", foreground=you_color, font=("Arial", 12, "bold"))
        self.text_widget.tag_configure("user_name_Aria", foreground=aria_color, font=("Arial", 12, "bold"))
        self.text_widget.tag_configure("normal_text", foreground="white")
        self.text_widget.tag_configure("code", foreground=code_color)
        
        self.root.bind("<Configure>", self.on_resize)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.kill = False
        
        self.visual_stop = False
        self.load_visual("system_init")
        
    def on_resize(self, event):
        self.visual_x = int(int(self.root.winfo_width())/2)
        self.visual_y = int(int(self.root.winfo_height())/4)
        
    def run_visual(self, frames, frame_num):
        self.visual_widget.coords(self.visual_widget_item, self.visual_x, self.visual_y)
        frame = frames[frame_num]
        self.visual_widget.itemconfig(self.visual_widget_item, image=frame)   
        frame_num = (frame_num + 1) % len(frames)     
        if not self.visual_stop:
            self.visual_after_id = self.root.after(20, self.run_visual, frames, frame_num)
    
    def update_visual(self, user_name, data, time_color_warning=0):
        if user_name == "You":
            spectrum = np.abs(scipy.fft.fft(data))
            amplitude = spectrum.mean()
            max_radius = min(self.visual_widget.winfo_reqwidth(), self.visual_widget.winfo_reqheight()) * self.listening_max_percentage / 2
            scaled_radius = min(amplitude * self.listening_sensitivity_factor, max_radius)
            self.listening_radius = int(0.8 * self.listening_radius + 0.2 * max(scaled_radius, self.listening_min_radius))
            oval_coords = (
                self.visual_x - self.listening_radius,
                self.visual_y - self.listening_radius,
                self.visual_x + self.listening_radius,
                self.visual_y + self.listening_radius
            )
            if 0 < time_color_warning < 0.25:
                self.listening_color = "#FF0000"
            elif 0.25 < time_color_warning < 0.5:
                self.listening_color = "#B93C3C"
            elif 0.5 < time_color_warning < 0.75:
                self.listening_color = "#8A4B4B"
            elif 0.75 < time_color_warning < 1:
                self.listening_color = "#584848"
            else:
                self.listening_color = "#FFFFFF"
            self.visual_widget.coords(self.visual_widget_item, oval_coords)
            self.visual_widget.itemconfig(self.visual_widget_item, outline=self.listening_color , fill=self.listening_color)
        elif user_name == "Aria":
            spectrum = np.abs(scipy.fft.fft(data))
            amplitude = spectrum.mean()
            for i in range(self.speaking_BAR_COUNT):
                height = self.speaking_MIN_SIZES[i] + (self.speaking_MAX_SIZES[i] - self.speaking_MIN_SIZES[i]) * amplitude
                self.visual_widget.coords(self.visual_widget_items[i], 
                            self.visual_x + i * (self.speaking_BAR_WIDTH + self.speaking_BAR_SPACING) - (self.speaking_BAR_WIDTH + self.speaking_BAR_SPACING) * self.speaking_BAR_COUNT / 2, 
                            self.visual_y - self.bar_height / 2 + height / 2 + self.bar_height / 2, 
                            (self.visual_x + i * (self.speaking_BAR_WIDTH + self.speaking_BAR_SPACING) - (self.speaking_BAR_WIDTH + self.speaking_BAR_SPACING) * self.speaking_BAR_COUNT / 2) + self.speaking_BAR_WIDTH, 
                            self.visual_y - self.bar_height / 2 - height / 2 + self.bar_height / 2)
            
    def load_visual(self, user_name):
        self.stop_visual()
        if user_name == "system_init":
            self.visual_widget_item = self.visual_widget.create_image(
                self.visual_x, self.visual_y, image=self.loading_frames[0])
            self.start_visual()
            self.run_visual(self.loading_frames, 0)
        elif user_name == "system_transition":
            self.visual_widget_item = self.visual_widget.create_image(
                self.visual_x, self.visual_y, image=self.transition_frames[0])
            self.start_visual()
            self.run_visual(self.transition_frames, 0)
        elif user_name == "system_muted_mic":
            self.visual_widget_item = self.visual_widget.create_image(
                self.visual_x, self.visual_y, image=self.muted_mic_frames[0])
            self.start_visual()
            self.run_visual(self.muted_mic_frames, 0)
        elif user_name == "You":
            oval_coords = (
                self.visual_x - self.listening_radius,
                self.visual_y - self.listening_radius,
                self.visual_x + self.listening_radius,
                self.visual_y + self.listening_radius
            )
            self.visual_widget_item = self.visual_widget.create_oval(oval_coords, 
                                           outline=self.listening_color, 
                                           width=2, 
                                           fill=self.listening_color)
        elif user_name == "Aria":
            self.bar_height = max(self.speaking_MAX_SIZES) + 20
            self.visual_widget_items = []
            for i in range(self.speaking_BAR_COUNT):
                x0 = self.visual_x + i * (self.speaking_BAR_WIDTH + self.speaking_BAR_SPACING) - (self.speaking_BAR_WIDTH + self.speaking_BAR_SPACING) * self.speaking_BAR_COUNT / 2
                y0 = self.visual_y - self.bar_height / 2 - self.speaking_MIN_SIZES[i] / 2 + self.bar_height / 2
                x1 = x0 + self.speaking_BAR_WIDTH
                y1 = self.visual_y - self.bar_height / 2 + self.speaking_MIN_SIZES[i] / 2 + self.bar_height / 2
                bar = self.visual_widget.create_rectangle(x0, y0, x1, y1, fill='#832DFF')
                self.visual_widget_items.append(bar)
    
    def stop_visual(self):
        self.visual_stop = True
        if hasattr(self, 'visual_after_id'):
            self.root.after_cancel(self.visual_after_id)
        self.visual_widget.delete("all")
    
    def start_visual(self):
        self.visual_stop = False
          
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

    def add_message(self, user_name, text, new_entry=False, color_code_block=False, code_blocks=[]):
        try:
            self.text_widget.config(state="normal")
            if new_entry:
                self.text_widget.insert("end", '\n\n' + user_name + ": ", "user_name_" + user_name)
            if color_code_block:
                if len(code_blocks) > 0:
                    current_pos = 0
                    for block_start, block_end in code_blocks:
                        self.text_widget.insert("end", text[current_pos:block_start], "normal_text")
                        self.text_widget.insert("end", text[block_start + 3:block_end - 2], "code")
                        current_pos = block_end + 1 
                    self.text_widget.insert("end", text[current_pos:], "normal_text")  
                else:    
                    self.text_widget.insert("end", text, "code")
            else:
                self.text_widget.insert("end", text, "normal_text")
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
