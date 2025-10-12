import tkinter as tk
from tkinter import font, messagebox
import os
import pyaudio
from PIL import Image, ImageTk
import sys
from file_protector import decrypt_and_open_file
import serial.tools.list_ports # <-- Add or verify this import


# Local module imports
from api_client import APIClient
import frontend_config as config  
from ui import ui_helpers, home_screens, login_flow, enrollment_flow, other_screens
from utils import audio_handler, helpers
from ui import application_settings
from ui.login_flow import show_new_password_screen
from ui.application_settings import show_change_otp_settings_screen
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))
from user_profile import load_session, save_session, clear_session

class KeyVoxApp:
    def __init__(self, root, args):
        self.temp_new_email = None # JC Temporary email variable for OTP Change
        self.root = root
        self.api = APIClient()
        
        self.PICO_HWID = 'VID:PID=2E8A:0005' # The ID for a running Pico serial port
        self.authenticated_pico_port = None # To store the COM port after login

                 # State for file unlocking
        self.unlock_mode = False
        self.target_file_to_unlock = None
        self.temp_file_path = None # To track the decrypted file

        # Check if a file path was passed as a command-line argument
        if len(args) > 1: 
            file_path = args[1]
            if os.path.exists(file_path) and file_path.endswith(".locked"):
                self.unlock_mode = True
                self.target_file_to_unlock = file_path
                print(f"✅ Unlock mode activated for: {self.target_file_to_unlock}")
        # ----------------------------

        # --- Window and App Configuration ---
        self.width, self.height = 900, 600
        self.root.title("Key Vox")
        self.root.geometry(f"{self.width}x{self.height}")
        self.root.resizable(False, False)
        if not os.path.exists(config.AUDIO_DIR):
            os.makedirs(config.AUDIO_DIR)

        self._load_images()
            
        # --- State Management ---
        self.currently_logged_in_user = None
        self.login_attempt_user = None
        self.new_enrollment_data = {}
        self.is_recording = False
        self.recording_thread = None
        self.current_phrase_index = 0
        self.enrollment_phrases = [
            "My password is my voice", 
            "Authenticate me through speech", 
            "Nine five two seven echo zebra tree", 
            "Today I confirm my identity using my voice", 
            "Unlocking access with my voice"
        ]
        self.token_id = "f3d4-9a7b-23ce-8e6f"
        self.just_enrolled = False
        self.login_flow_state = 'not_started'
        self.enrollment_state = 'not_started'
        self.nav_widgets = {}

        self.authenticated_pico_port = None # To store the COM port of the logged-in Pico
        
        # --- Initialize PyAudio ---
        self.pyaudio_instance = pyaudio.PyAudio()

        self._initialize_fonts()
        
        # --- Build Core UI ---
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
      #  ui_helpers.set_background_image(self)
       # ui_helpers.create_header(self)
        self.content_frame = tk.Canvas(self.canvas, highlightthickness=0)
        # self.content_frame = tk.Canvas(self.canvas, highlightthickness=0, bg=self.canvas.cget('bg'))
        # self.canvas.create_window(self.width / 2, self.height / 2 + 60, window=self.content_frame, anchor="center")
        
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.check_server_and_start()

    # =========================================================
    # IMAGE LOADING
    # =========================================================
    def _load_images(self):
        """Loads all necessary images for the application."""
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))

            # Paths
            img_dir = os.path.join(script_dir, "assets", "images")
            icon_dir = os.path.join(script_dir, "assets", "icons")

            # Main images
            self.logo_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "logo.png")).resize((110, 110)))
            self.key_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "key.png")).resize((60, 60)))
            self.mic_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "mic.png")).resize((60, 60)))
            self.otp_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "otp_settings.png")).resize((60, 60)))
            self.usb_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "usb.png")).resize((230, 230)))
            self.bg_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "bg.png")).resize((self.width, self.height)))
            self.eye_open_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "eyes_closed.png")).resize((20, 20)))
            self.eye_closed_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "eyes_open.png")).resize((20, 20)))
            self.dot_filled_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "dot_filled.png")).resize((12, 12)))
            self.dot_empty_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "dot_empty.png")).resize((12, 12)))
            self.profile_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "profile.png")).resize((100, 100)))
            self.card_bg_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "card_background.png")))
            self.lock_img = ImageTk.PhotoImage(Image.open(os.path.join(img_dir, "lock.png")).resize((90, 90)))

            # Optional icons (info/help)
            try:
                self.help_img = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "help.png")).resize((22, 22)))
                self.info_img = ImageTk.PhotoImage(Image.open(os.path.join(icon_dir, "info.png")).resize((22, 22)))
            except Exception:
                # Fallbacks if icons are missing
                self.help_img = None
                self.info_img = None
                print("⚠️ Info/help icons not found, skipping.")

        except FileNotFoundError as e:
            messagebox.showerror(
                "Asset Error",
                f"Image not found: {e.filename}\nPlease ensure 'frontend/assets/images' exists and contains all required images."
            )
            self.root.destroy()
            exit()

    # =========================================================
    # FONT INITIALIZATION
    # =========================================================
    def _initialize_fonts(self):
        """Initializes all font styles used in the application."""
        self.font_nav = font.Font(family=config.FONT_FAMILY, size=12)
        self.font_nav_active = font.Font(family=config.FONT_FAMILY, size=12, weight="bold")
        self.font_large_bold = font.Font(family=config.FONT_FAMILY, size=20, weight="bold")
        self.font_large = font.Font(family=config.FONT_FAMILY, size=16)
        self.font_medium_bold = font.Font(family=config.FONT_FAMILY, size=14, weight="bold")
        self.font_normal = font.Font(family=config.FONT_FAMILY, size=10)
        self.font_small = font.Font(family=config.FONT_FAMILY, size=9)

    # =========================================================
    # SERVER CHECK AND STARTUP FLOW
    # =========================================================
    def check_server_and_start(self):
        """Checks backend server status and decides which UI flow to start."""
        if not self.api.check_server_status():
            messagebox.showerror("Connection Error", "Could not connect to the backend server.\nPlease ensure the server is running.")
            self.root.destroy()
            return  # This 'return' is now correctly inside the 'if' block.

        print("✅ Backend server connected.")

        # --- This routing logic is now correctly inside the function ---
        if self.unlock_mode:
            # --- UNLOCK FILE FLOW ---
            ui_helpers.set_background_image(self)
            ui_helpers.create_header(self, show_nav=True)

            self.content_frame.config(bg=self.canvas.cget('bg'))
            self.canvas.create_window(self.width / 2, self.height / 2 + 60, window=self.content_frame, anchor="center")

            self.login_attempt_user = {"username": "secure_file_access"}

            print("➡️ Unlock mode: Proceeding to voice authentication.")
            self.show_login_voice_auth_screen()
        else:
            # --- NORMAL APP STARTUP FLOW ---
            ui_helpers.set_background_image(self)
            ui_helpers.create_header(self, show_nav=True)

            self.content_frame.config(bg=self.canvas.cget('bg'))
            self.canvas.create_window(self.width / 2, self.height / 2 + 60, window=self.content_frame, anchor="center")
            
            print("➡️ Normal mode: Showing welcome screen.")
            self.show_welcome_screen()
        
    def _on_authentication_success(self):
        """
        This is the central handler for what to do after all authentication passes.
        It checks if we are in 'unlock_mode' and acts accordingly.
        """
        print("❤️ Starting Pico heartbeat check...")
        self.root.after(2000, self._check_pico_heartbeat)

        if self.unlock_mode:
            # --- FILE UNLOCK PATH ---
            print(f"🔓 Authentication successful! Decrypting and opening {self.target_file_to_unlock}")
            messagebox.showinfo("Access Granted", "Authentication successful. Opening secure file.")
            
            # Decrypt, open, and store the temp file path for later cleanup
            self.temp_file_path = decrypt_and_open_file(self.target_file_to_unlock)
            
            if self.temp_file_path is None:
                messagebox.showerror("Error", "Failed to decrypt or open the file. The key might be incorrect or the file corrupted.")
            
            # Gracefully shut down the authenticator app
            self.root.after(500, self._on_closing)
        else:
            # --- ORIGINAL SECURE FOLDER PATH ---
            print(f"🔓 Access Granted! Opening secure folder: {self.TARGET_PATH}")
            messagebox.showinfo("Access Granted", "Authentication successful. Opening secure folder.")
            try:
                os.startfile(self.TARGET_PATH)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open the target folder: {e}")
            self.root.after(500, self._shutdown)

    def _check_pico_heartbeat(self):
        """
        Periodically checks if the authenticated Pico is still connected.
        If the Pico is removed, this function closes the application.
        """
        # 1. Do nothing if no Pico was ever authenticated.
        if not self.authenticated_pico_port:
            return

        # 2. Get a list of all currently connected serial port devices.
        ports = serial.tools.list_ports.comports()
        current_devices = [p.device for p in ports]

        # 3. Check if our authenticated port is still in the list of connected devices.
        if self.authenticated_pico_port not in current_devices:
            # If it's MISSING, the Pico was unplugged!
            print("🔴 Pico disconnected! Closing application for security.")
            messagebox.showwarning("Security Alert", "Hardware token was removed. The application will now close.")
            self._on_closing() # Use your existing closing function to ensure cleanup
        else:
            # If it's STILL CONNECTED, schedule this check to run again in 2 seconds.
            self.root.after(2000, self._check_pico_heartbeat)


    # =========================================================
    # SCREEN NAVIGATION
    # =========================================================
    def show_home_screen(self, event=None): home_screens.show_home_screen(self)
    def show_applications_screen(self): other_screens.show_applications_screen(self)
    def show_about_screen(self, event=None): other_screens.show_about_screen(self)
    def show_help_screen(self, event=None): other_screens.show_help_screen(self)

    def show_insert_key_screen(self): home_screens.show_insert_key_screen(self)
    def show_username_entry_screen(self): login_flow.show_username_entry_screen(self)
    def _handle_username_submit(self): login_flow.handle_username_submit(self)
    def show_login_voice_auth_screen(self): login_flow.show_login_voice_auth_screen(self)
    def _handle_login_voice_record(self, event=None): login_flow.handle_login_voice_record(self, event)
    def _check_password(self): login_flow.check_password(self)
    
    def navigate_to_enrollment(self, event=None): enrollment_flow.navigate_to_enrollment(self)
    def _validate_step1(self): enrollment_flow.validate_step1(self)
    def show_enrollment_voice_record(self): enrollment_flow.show_enrollment_voice_record(self)
    def _go_back_phrase(self): enrollment_flow.go_back_phrase(self)
    def _go_next_phrase(self): enrollment_flow.go_next_phrase(self)
    def _finish_enrollment(self): enrollment_flow.finish_enrollment(self)
    def show_change_password_screen(self): application_settings.show_change_password_screen(self)
    def show_password_screen_voice_entry1(self): application_settings.show_password_screen_voice_entry1(self)
    def show_otp_settings_screen(self): application_settings.show_otp_settings_screen(self)
    def show_change_OTP_step1_voice_auth_screen(self): application_settings.show_change_OTP_step1_voice_auth_screen(self)

    def show_new_password_screen(self): show_new_password_screen(self)
    def show_change_otp_settings_screen(self): show_change_otp_settings_screen(self)

    # =========================================================
    # UTILITIES
    # =========================================================
    def toggle_recording(self, event=None): audio_handler.toggle_recording(self, event)
    def _record_audio_blocking(self, filepath, duration=4): audio_handler.record_audio_blocking(self, filepath, duration)
    def _mask_email(self, email): return helpers.mask_email(email)

    def _on_closing(self):
        if self.temp_file_path and os.path.exists(self.temp_file_path):
            print(f"🧹 Cleaning up temporary file: {self.temp_file_path}")
            os.remove(self.temp_file_path)
            self.temp_file_path = None # Clear the path

        self.is_recording = False
        if self.recording_thread and self.recording_thread.is_alive():
            self.root.after(100, self._shutdown)
        else:
            self._shutdown()

    def _shutdown(self):
        self.pyaudio_instance.terminate()
        self.root.destroy()

    # =========================================================
    # LOGOUT
    # =========================================================
    def logout_user(self):
        """Logs the user out, clears all session state, and returns to the welcome screen."""
        confirm = messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?")
        if confirm:
            self.currently_logged_in_user = None
            self.login_attempt_user = None
            self.login_flow_state = 'not_started'
            # Always go to the initial welcome screen on logout
            self.show_insert_key_screen() 

    # =========================================================
    # WELCOME SCREEN
    # =========================================================
    def show_welcome_screen(self):
        """Landing page before login screen."""
        self.login_flow_state = 'not_started'
        self.currently_logged_in_user = None
        self.login_attempt_user = None

        LIGHT_CARD_BG = "#AD567C"
        card = ui_helpers.create_main_card(self, width=480, height=380)
        card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)

        wrapper = tk.Frame(card, bg=LIGHT_CARD_BG, bd=0)
        wrapper.pack(expand=True)

        tk.Label(wrapper, image=self.lock_img, bg=LIGHT_CARD_BG).pack(pady=(15, 10))
        tk.Label(wrapper, text="Insert Your Key", font=self.font_large, fg=config.TEXT_COLOR, bg=LIGHT_CARD_BG).pack(pady=(0, 8))
        tk.Label(wrapper,
                 font=self.font_normal, fg="#E8E8E8", bg=LIGHT_CARD_BG,
                 wraplength=350, justify="center").pack(pady=(0, 18))

        # Rounded button
        def create_rounded_button(parent, text, command=None, radius=15, width=200, height=40,
                                  bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR):
            wrap = tk.Frame(parent, bg=LIGHT_CARD_BG)
            wrap.pack(pady=(0, 18))
            canvas = tk.Canvas(wrap, width=width, height=height, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
            canvas.pack()
            x1, y1, x2, y2 = 2, 2, width-2, height-2
            canvas.create_oval(x1, y1, x1+radius*2, y1+radius*2, fill=bg, outline=bg)
            canvas.create_oval(x2-radius*2, y1, x2, y1+radius*2, fill=bg, outline=bg)
            canvas.create_oval(x1, y2-radius*2, x1+radius*2, y2, fill=bg, outline=bg)
            canvas.create_oval(x2-radius*2, y2-radius*2, x2, y2, fill=bg, outline=bg)
            canvas.create_rectangle(x1+radius, y1, x2-radius, y2, fill=bg, outline=bg)
            canvas.create_rectangle(x1, y1+radius, x2, y2-radius, fill=bg, outline=bg)
            text_obj = canvas.create_text(width//2, height//2, text=text, fill=fg, font=self.font_normal)
            canvas.tag_bind(text_obj, "<Button-1>", lambda e: command())
            return wrap

        create_rounded_button(wrapper, "Get Started", command=self.show_insert_key_screen)

        tk.Label(wrapper, text="© 2025 KeyVox Technologies",
                 font=self.font_small, fg="#D9D9D9", bg=LIGHT_CARD_BG).pack(pady=(10, 0))


if __name__ == "__main__":
    root = tk.Tk()
    app = KeyVoxApp(root, sys.argv)
    root.mainloop()


