import tkinter as tk
from tkinter import ttk, Menu
import json


class LoginUi:
    def __init__(self, params=None, config_file=None, callback=None):
        self.params = params or {}
        self.window_title = self.params.get('window_title', None)
        self.icon = self.params.get('assets', None).get('icon', None)
        self.config_file = config_file
        self.callback = callback
        
        self.config = self.load_config()
        
        self.root = tk.Tk()
        self.root.title(self.window_title)
        icon_image = tk.PhotoImage(file=self.icon)
        self.root.iconphoto(True, icon_image)
        self.root.geometry("400x300")
        self.root.configure(bg="black")
        self.root.resizable(False, False)
        
        self.style = ttk.Style()
        self.style.theme_use('default')
        self.style.configure('TFrame', background='black')
        self.style.configure('TLabel', background='black', foreground='white')
        self.style.configure('TButton', background='white', foreground='black')
        self.style.configure('TEntry', fieldbackground='black', foreground='white')
        
        self.main_frame = ttk.Frame(self.root, padding="20")
        self.main_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.create_input_fields()
        
        self.connect_button = ttk.Button(self.main_frame, text="Connect", command=self.on_connect)
        self.connect_button.grid(row=4, column=0, columnspan=2, pady=10, sticky="ew")
        
        self.status_var = tk.StringVar()
        self.status_label = ttk.Label(self.main_frame, textvariable=self.status_var, foreground="red", background="black")
        self.status_label.grid(row=5, column=0, columnspan=2, pady=5, sticky="ew")
        
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=3)
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.kill = False
        self.connection_status = False
    
    def load_config(self):
        with open(self.config_file, 'r') as f:
            config = json.load(f)
        return config   
    
    def save_config(self):
        with open(self.config_file, 'r') as f:
            config = json.load(f)
            
        config["Nw"]["params"]["client_target_ip"] = self.ip_address_var.get()
        config["Nw"]["params"]["client_target_port"] = int(self.port_var.get())
        config["Nw"]["params"]["username"] = self.username_var.get()
        config["Nw"]["params"]["password"] = self.password_var.get()
        
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def create_input_fields(self):
        nw_params = self.config.get("Nw", {}).get("params", {})
        default_ip = nw_params.get("client_target_ip", "")
        default_port = nw_params.get("client_target_port", "")
        default_username = nw_params.get("username", "")
        default_password = nw_params.get("password", "")
        
        field_data = [
            ("IP Address:", "ip_address", default_ip),
            ("Port:", "port", default_port),
            ("Username:", "username", default_username),
            ("Password:", "password", default_password, True)
        ]
        
        for i, field_info in enumerate(field_data):
            label_text, field_name, default_value = field_info[:3]
            is_password = len(field_info) > 3 and field_info[3]
            
            label = ttk.Label(self.main_frame, text=label_text)
            label.grid(row=i, column=0, sticky="w", pady=5)
            
            var = tk.StringVar(value=default_value)
            entry = tk.Entry(self.main_frame, textvariable=var, background='black', foreground='white', insertbackground="white")
            entry.configure(insertofftime=500, insertontime=500)
            entry.grid(row=i, column=1, sticky="ew", padx=5, pady=5)
            
            self.limit_entry_chars(entry, 30)
            self.prevent_newlines(entry)
            self.add_context_menu(entry)
            
            if field_name == "port":
                self.validate_port_wrapper(var, entry)
            
            setattr(self, f"{field_name}_var", var)
            setattr(self, f"{field_name}_entry", entry)
            
            if is_password:
                entry.configure(show="*")
                
                toggle_btn = ttk.Button(self.main_frame, text="Show", width=5,
                                      command=lambda e=entry: self.toggle_password_visibility(e))
                toggle_btn.grid(row=i, column=2, padx=5, pady=5)
                self.password_toggle_btn = toggle_btn
                
    def validate_port_wrapper(self, var, entry):
        def validate_port(value):
            if value == "":
                entry.configure(foreground='white')
                return True
                
            try:
                port = int(value)
                if 0 <= port <= 65535:
                    entry.configure(foreground='white')
                    return True
                else:
                    # entry.configure(foreground='red')
                    return False
            except ValueError:
                # entry.configure(foreground='red')
                return False

        def on_port_change(*args):
            current_value = var.get()
            if not validate_port(current_value):
                # entry.configure(foreground='red')
                pass
            else:
                entry.configure(foreground='white')

        vcmd = (self.main_frame.register(validate_port), '%P')
        entry.configure(validate='key', validatecommand=vcmd)
        
        var.trace_add('write', on_port_change)
    
    def toggle_password_visibility(self, entry):
        if entry.cget('show') == '*':
            entry.configure(show='')
            self.password_toggle_btn.configure(text='Hide')
        else:
            entry.configure(show='*')
            self.password_toggle_btn.configure(text='Show')
    
    def add_context_menu(self, entry):
        if not hasattr(self, 'context_menu'):
            self.context_menu = Menu(self.root, tearoff=0, bg='black', fg='white')
            self.context_menu.add_command(label="Copy", command=lambda: self.copy_text(entry))
            self.context_menu.add_command(label="Paste", command=lambda: self.paste_text(entry))
        
        def show_context_menu(event):
            self.context_menu.unpost()
            self.context_menu.entryconfig(0, command=lambda: self.copy_text(entry))
            self.context_menu.entryconfig(1, command=lambda: self.paste_text(entry))
            self.context_menu.post(event.x_root, event.y_root)
        
        def close_context_menu(event):
            self.context_menu.unpost()
        
        entry.bind('<Button-3>', show_context_menu)
        entry.bind('<Button-1>', close_context_menu)
        self.root.bind('<Button-1>', close_context_menu)
    
    def copy_text(self, entry):
        if entry.selection_present():
            selected_text = entry.selection_get()
            self.root.clipboard_clear()
            self.root.clipboard_append(selected_text)
    
    def paste_text(self, entry):
        try:
            text = self.root.clipboard_get()
            current_len = len(entry.get())
            if current_len + len(text) <= 30:
                entry.insert(tk.INSERT, text)
            else:
                remaining = 30 - current_len
                if remaining > 0:
                    entry.insert(tk.INSERT, text[:remaining])
        except:
            pass
    
    def limit_entry_chars(self, entry, max_chars):
        def limit_chars(*args):
            value = entry.get()
            if len(value) > max_chars:
                entry.delete(max_chars, tk.END)
        
        vcmd = (self.root.register(lambda P: len(P) <= max_chars), '%P')
        entry.configure(validate='key', validatecommand=vcmd)
    
    def prevent_newlines(self, entry):
        def check_input(event):
            if event.char == '\r' or event.char == '\n':
                return 'break'
        
        entry.bind('<Key>', check_input)
    
    def on_connect(self):
        connection_data = {
            'ip_address': self.ip_address_var.get(),
            'port': int(self.port_var.get()),
            'username': self.username_var.get(),
            'password': self.password_var.get()
        }
        
        self.lock_connect_button()
        self.save_config()
        
        self.callback(connection_data)
        
        return connection_data
    
    def lock_connect_button(self):
        self.connect_button.configure(state='disabled', text="Connecting...")
        
        self.ip_address_entry.configure(state='disabled')
        self.port_entry.configure(state='disabled')
        self.username_entry.configure(state='disabled')
        self.password_entry.configure(state='disabled')
        
        if hasattr(self, 'password_toggle_btn'):
            self.password_toggle_btn.configure(state='disabled')

    def unlock_connect_button(self):
        self.connect_button.configure(state='normal', text="Connect")
        
        self.ip_address_entry.configure(state='normal')
        self.port_entry.configure(state='normal')
        self.username_entry.configure(state='normal')
        self.password_entry.configure(state='normal')
        
        if hasattr(self, 'password_toggle_btn'):
            self.password_toggle_btn.configure(state='normal')
    
    def set_status_message(self, message, is_error=True):
        self.status_var.set(message)
        if is_error:
            self.status_label.configure(foreground="red")
            self.unlock_connect_button()
        else:
            self.status_label.configure(foreground="green")
        # self.unlock_connect_button()
    
    def close(self):
        self.root.after(0, self.root.destroy)
        self.kill = True
    
    def start(self):
        try:
            self.root.mainloop()
        except:
            pass
        if self.connection_status:
            return True
        return False
            
