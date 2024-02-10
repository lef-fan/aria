import tkinter as tk


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
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.kill = False

    def add_message(self, user_name, text, new_entry=False):
        if "user" in user_name:
            color = 'red'
        elif "aria" in user_name:
            color = "green"
        try:
            self.text_widget.config(state="normal")
            if new_entry:
                self.text_widget.insert("end", '\n\n' + user_name + ": ", (color, "bold"))
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
