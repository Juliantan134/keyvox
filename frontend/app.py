import tkinter as tk
from tkinter import font, messagebox
import os
import pyaudio
from PIL import Image, ImageTk

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
    def __init__(self, root):
        self.temp_new_email = None # JC Temporary email variable for OTP Change
        self.root = root
        self.api = APIClient()
        
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

        # --- Initialize PyAudio ---
        self.pyaudio_instance = pyaudio.PyAudio()

        self._initialize_fonts()
        
        # --- Build Core UI ---
        self.canvas = tk.Canvas(root, width=self.width, height=self.height, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        ui_helpers.set_background_image(self)
        ui_helpers.create_header(self)
        
        self.content_frame = tk.Canvas(self.canvas, highlightthickness=0, bg=self.canvas.cget('bg'))
        self.canvas.create_window(self.width / 2, self.height / 2 + 60, window=self.content_frame, anchor="center")
        
        self.check_server_and_start()
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)

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
        """Checks backend server status and starts the UI flow."""
        if not self.api.check_server_status():
            messagebox.showerror("Connection Error", "Could not connect to the backend server.\nPlease ensure the server is running.")
            self.root.destroy()
        else:
            print("✅ Backend server connected.")
            self.show_insert_key_screen()

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
    app = KeyVoxApp(root)
    root.mainloop()


