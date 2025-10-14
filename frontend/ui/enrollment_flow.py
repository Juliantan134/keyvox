import tkinter as tk
from tkinter import messagebox, font as tkFont # Added font import for consistency
import os
import frontend_config as config
from ui import ui_helpers
from utils.validators import validate_email, validate_password
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))
from OTP.send_otp import send_otp, verify_otp

from user_data_manager import get_user_by_username, update_email, update_email_by_name_and_blank_email

def navigate_to_enrollment(app, event=None):
    """Entry point for the enrollment flow."""
    ui_helpers.update_nav_selection(app, "enrollment")
    show_enrollment_step1(app)
    
def show_enrollment_step1(app):
    """Shows the account setup form (name, username, password)."""
    LIGHT_CARD_BG = "#AD567C"

    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.enrollment_state = 'step1_account_setup'
    app.new_enrollment_data = {}

    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=10)
    font_label = tkFont.Font(family="Poppins", size=11)
    font_entry = tkFont.Font(family="Poppins", size=11)
    font_small = tkFont.Font(family="Poppins", size=9)
    font_button = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=700, height=400, bg=LIGHT_CARD_BG)
    card.pack(pady=30)
    card.pack_propagate(False)
    card.grid_columnconfigure(1, weight=1)

    tk.Label(card, text="STEP 1: Account Setup", font=font_title,
             fg="white", bg=LIGHT_CARD_BG).grid(row=0, column=0, columnspan=2,
                                               sticky="w", pady=(20, 5), padx=40)
    tk.Label(card, text="Enter your basic account information",
             font=font_subtitle, fg="white", bg=LIGHT_CARD_BG).grid(row=1, column=0,
                                                                   columnspan=2,
                                                                   sticky="w",
                                                                   pady=(0, 20),
                                                                   padx=40)

    fields = {
        "Full Name:": "full_name",
        "Username:": "username",
        "Email Address:": "email",
        "Password:": "password",
        "Confirm Password:": "confirm_password"
    }
    app.entry_widgets = {}

    def make_password_field(parent, key):
        entry_frame = tk.Frame(parent, bg="white")
        entry = tk.Entry(entry_frame, font=font_entry, width=22,
                         bg="white", fg="black", relief="flat", bd=0,
                         show="*", insertbackground="black")
        entry.pack(side="left", ipady=4, padx=(5, 0))
        app.entry_widgets[key] = entry
        def toggle_visibility():
            if entry.cget("show") == "*": entry.config(show=""); btn.config(image=app.eye_closed_img)
            else: entry.config(show="*"); btn.config(image=app.eye_open_img)
        btn = tk.Button(entry_frame, image=app.eye_open_img, bg="white", relief="flat", bd=0,
                        activebackground="white", cursor="hand2", command=toggle_visibility)
        btn.pack(side="right", padx=(0, 5))
        return entry_frame

    for i, (label, key) in enumerate(fields.items()):
        tk.Label(card, text=label, font=font_label,
                 fg="white", bg=LIGHT_CARD_BG).grid(row=i + 2, column=0,
                                                    sticky="w", pady=6, padx=(40, 20))
        if "Password" in label:
            frame = make_password_field(card, key)
            frame.grid(row=i + 2, column=1, pady=6, padx=(0, 40), sticky="ew")
        else:
            entry = tk.Entry(card, font=font_entry, width=25,
                             bg="white", fg="black", relief="flat", bd=0,
                             insertbackground="black")
            entry.grid(row=i + 2, column=1, pady=6, ipady=4, padx=(0, 40), sticky="ew")
            app.entry_widgets[key] = entry

    app.enroll_error_label = tk.Label(card, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG)
    app.enroll_error_label.grid(row=len(fields) + 2, column=0, columnspan=2, pady=(10, 0))

    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 10))

    dots_frame = tk.Frame(bf, bg=bf.cget('bg'))
    dots_frame.pack(side="left")
    tk.Label(dots_frame, image=app.dot_filled_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)

    tk.Button(bf, text="Next Step →", font=font_button,
              bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
              command=lambda: validate_step1(app)).pack(side="right")

def validate_step1(app):
    data = {key: entry.get() for key, entry in app.entry_widgets.items()}

    # Email and password validation...
    email_valid, email_err = validate_email(data.get("email", ""))
    if not email_valid:
        app.enroll_error_label.config(text=email_err)
        return

    password_valid, password_err = validate_password(data.get("password", ""))
    if not password_valid:
        app.enroll_error_label.config(text=password_err)
        return

    if data["password"] != data["confirm_password"]:
        app.enroll_error_label.config(text="Passwords do not match.")
        return

    # Save data **in memory only**
    app.new_enrollment_data = {k: v for k, v in data.items() if k != "confirm_password"}
    
    # Proceed to next step without saving to JSON yet
    app.enroll_error_label.config(text="")
    show_enrollment_step2(app)
 
def show_enrollment_step2(app):
    LIGHT_CARD_BG = "#AD567C"
    for widget in app.content_frame.winfo_children(): widget.destroy()
    app.enrollment_state = 'step2_voice_intro'
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=10)
    font_button = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=500, height=300, bg=LIGHT_CARD_BG)
    card.pack(pady=30); card.pack_propagate(False)
    tk.Label(card, text="STEP 2: Voice Authentication", font=font_title, fg="white", bg=LIGHT_CARD_BG).pack(anchor="w", pady=(20, 5), padx=40)
    tk.Label(card, text="Record your voice for added security.\nYou will record 5 phrases to create your voiceprint.", font=font_subtitle, fg="white", bg=LIGHT_CARD_BG, justify="left", wraplength=600).pack(anchor="w", pady=(0, 25), padx=40)

    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG); bf.pack(fill="x", padx=60, pady=(0, 10))
    tk.Button(bf, text="< Back", font=font_button, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=12, pady=4, command=lambda: show_enrollment_step1(app)).pack(side="left")
    
    dots_frame = tk.Frame(bf, bg=bf.cget('bg')); dots_frame.pack(side="left", padx=20)
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_filled_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    tk.Label(dots_frame, image=app.dot_empty_img, bg=bf.cget('bg')).pack(side="left", padx=2)
    
    tk.Button(bf, text="Start →", font=font_button, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=12, pady=4, command=lambda: show_enrollment_voice_record(app)).pack(side="right")

def show_enrollment_voice_record(app):
    print("show_enrollment_voice_record")
    LIGHT_CARD_BG = "#AD567C"
    for widget in app.content_frame.winfo_children(): widget.destroy()
    app.enrollment_state = 'step3_voice_record'
    font_title = tkFont.Font(family="Poppins", size=12, weight="bold")
    font_text = tkFont.Font(family="Poppins", size=10)
    font_button = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=500, height=300, bg=LIGHT_CARD_BG); card.pack(pady=30); card.pack_propagate(False)
    tk.Label(card, text=f"{app.current_phrase_index + 1} of {len(app.enrollment_phrases)}", font=font_text, fg="white", bg=LIGHT_CARD_BG).pack(pady=(20, 0))
    tk.Label(card, text=f'"{app.enrollment_phrases[app.current_phrase_index]}"', font=font_title, fg="white", bg=LIGHT_CARD_BG, wraplength=600).pack(expand=True)
    mic_label = tk.Label(card, image=app.mic_img, bg=LIGHT_CARD_BG, highlightthickness=0, cursor="hand2"); mic_label.pack(pady=10); mic_label.bind("<Button-1>", app.toggle_recording)
    app.recording_status_label = tk.Label(card, text="Click the mic to record", font=font_text, fg="white", bg=LIGHT_CARD_BG); app.recording_status_label.pack(pady=(0, 20))
    
    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG); bf.pack(fill="x", padx=60, pady=(0, 10))
    # Corrected command with lambda
    tk.Button(bf, text="< Back", font=font_button, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=12, pady=4, command=lambda: go_back_phrase(app)).pack(side="left")
    
    # app.next_btn = tk.Button(bf, text="Next →", font=font_button, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=12, pady=4, command=lambda: go_next_phrase(app), state="disabled"); app.next_btn.pack(side="right")
    app.next_btn = tk.Button(bf, text="Next →", font=font_button, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=12, pady=4, command=lambda: handle_final_enrollment_upload(app, next_step="otp"), state="disabled"); app.next_btn.pack(side="right")



def go_back_phrase(app):
    if app.current_phrase_index > 0:
        app.current_phrase_index -= 1
        show_enrollment_voice_record(app)
    else:
        show_enrollment_step2(app)

def go_next_phrase(app):
    if app.current_phrase_index < len(app.enrollment_phrases) - 1:
        app.current_phrase_index += 1
        show_enrollment_voice_record(app)
    else:
        handle_final_enrollment_upload(app, next_step="otp")

def show_enrollment_step3_otp(app):
    """Shows a styled OTP verification screen with dummy bypass and proper bottom margin."""
    LIGHT_CARD_BG = "#AD567C"

    # SAVE THE STEP 1 EMAIL AND SAVE THE PENGUINS FOR OTP SENDING TOO
    app.user_email_for_otp = app.new_enrollment_data.get('email', 'your_email@example.com')
    email_from_step1 = app.user_email_for_otp

    # Clear old widgets
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    import tkinter.font as tkFont
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_text = tkFont.Font(family="Poppins", size=12)
    font_small = tkFont.Font(family="Poppins", size=10)
    font_button = tkFont.Font(family="Poppins", size=11)

    # --- Card ---
    card = tk.Frame(app.content_frame, width=420, height=280, bg=LIGHT_CARD_BG)
    card.pack(pady=(30, 20))  # 30px top, 20px bottom
    card.pack_propagate(False)

    # --- Title ---
    tk.Label(card, text="OTP Verification", font=font_title, fg="white", bg=LIGHT_CARD_BG).pack(pady=(20, 10))

    # --- Info Text ---
    # email = app.currently_logged_in_user.get('email', 'your_email@example.com') if app.currently_logged_in_user else 'your_email@example.com'
    # email = getattr(app, "user_email_for_otp", "your_email@example.com")
    tk.Label(card, text=f"Enter the 6-digit code sent to {email_from_step1}", font=font_small, fg="white", bg=LIGHT_CARD_BG, wraplength=380).pack(pady=(0, 15))

    # --- OTP Entry ---
    app.otp_entry = tk.Entry(card, font=font_text, width=20, justify="center")
    app.otp_entry.pack(ipady=6, pady=(0, 10))

    # --- Error Label ---
    app.otp_error_label = tk.Label(card, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG)
    app.otp_error_label.pack(pady=(0, 10))

    # --- Send Code Label ---
    tk.Label(card, text="Didn't Receive Code?", font=font_small, fg="white", bg=LIGHT_CARD_BG, wraplength=380).pack(pady=(0, 5))

    # --- Send Code Button ---
    def send_code():
        email = app.user_email_for_otp
        try:
            from OTP.send_otp import send_otp
            success, message = send_otp(email)
            if success:
                messagebox.showinfo("OTP Sent", message)
            else:
                app.otp_error_label.config(text=message)
        except Exception as e:
            err_msg = f"❌ Error sending OTP: {e}"
            app.otp_error_label.config(text=err_msg)
            messagebox.showerror("Error", err_msg)

    tk.Button(card, text="Send Code", font=font_small, command=send_code, bg="#F5F5F5").pack(pady=(0, 10))

    # --- Verify Function (bypasses OTP for testing) ---
    def verify_otp_ui():
        otp = app.otp_entry.get()
        try:
            from OTP.send_otp import verify_otp
            success = verify_otp(otp)
            if success:
                messagebox.showinfo("Success", "OTP verified successfully!")

                # ✅ Update email now that OTP is verified
                full_name = app.new_enrollment_data.get("full_name")
                new_email = app.user_email_for_otp
                update_email_by_name_and_blank_email(full_name, new_email)

                # Update app.new_enrollment_data to reflect verified email
                app.new_enrollment_data['email'] = new_email

                # Proceed to next step
                show_enrollment_summary(app)
            else:
                app.otp_error_label.config(text="Invalid or expired OTP. Please try again.")
        except Exception as e:
            err_msg = f"❌ Error verifying OTP: {e}"
            app.otp_error_label.config(text=err_msg)
            messagebox.showerror("Error", err_msg)

    # --- Rounded Verify Button ---
    def create_rounded_button(parent, text, command=None, radius=15, width=200, height=40, bg="#F5F5F5", fg="black"):
        wrapper = tk.Frame(parent, bg=LIGHT_CARD_BG)
        wrapper.pack(pady=0)  # spacing handled by wrapper frame below

        canvas = tk.Canvas(wrapper, width=width, height=height, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0, relief="flat", cursor="hand2")
        canvas.pack()

        x1, y1, x2, y2 = 2, 2, width-2, height-2
        canvas.create_oval(x1, y1, x1 + radius*2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y1, x2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x1, y2 - radius*2, x1 + radius*2, y2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y2 - radius*2, x2, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=bg, outline=bg)

        btn_text = canvas.create_text(width//2, height//2, text=text, fill=fg, font=app.font_normal)

        def on_click(event):
            if command:
                command()
        canvas.tag_bind(btn_text, "<Button-1>", on_click)
        canvas.bind("<Button-1>", on_click)

        return wrapper

    # --- Place the button below the card with proper bottom margin ---
    button_wrapper = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    button_wrapper.pack(pady=(0, 30))  # 30px bottom margin
    create_rounded_button(button_wrapper, "Verify OTP", command=verify_otp_ui)

def handle_final_enrollment_upload(app, next_step="otp"):
    username = app.new_enrollment_data.get("username")
    filepath = os.path.join(config.AUDIO_DIR, f"{username}_phrase_1.wav")

    if not os.path.exists(filepath):
        messagebox.showerror("Error", "Primary enrollment audio not found. Please record phrase 1 again.")
        return

    # 1️⃣ Register user first
    # Change the email in app.new_enrollment_data
    data_copy = app.new_enrollment_data.copy()
    data_copy['email'] = ''  # Only blank email in the copy
    save_response = app.api.register_user(data_copy)
    print(app.new_enrollment_data)
    print(data_copy)
    if save_response.get("status") != "success":
        messagebox.showerror("Enrollment Failed", save_response.get("message", "Could not save user data."))
        return
    # 2️⃣ Then enroll voice
    response = app.api.enroll_voice(username, filepath)
    if response.get("status") == "success":
        if next_step == "otp":
            show_enrollment_step3_otp(app)
        else:
            show_enrollment_summary(app)
    else:
        messagebox.showerror("Enrollment Failed", response.get("message", "Final enrollment failed."))

def show_enrollment_summary(app):
    LIGHT_CARD_BG = "#AD567C"
    for widget in app.content_frame.winfo_children(): widget.destroy()
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_text = tkFont.Font(family="Poppins", size=11)
    font_button = tkFont.Font(family="Poppins", size=10)

    card = tk.Frame(app.content_frame, width=500, height=300, bg=LIGHT_CARD_BG); card.pack(pady=30); card.pack_propagate(False)
    tk.Label(card, text="Enrollment Process Complete", font=font_title, fg="white", bg=LIGHT_CARD_BG).grid(row=0, column=0, columnspan=2, sticky="w", pady=(20, 5), padx=40)
    tk.Label(card, text="You've successfully enrolled. Your credentials are now securely registered.", font=font_text, fg="white", bg=LIGHT_CARD_BG, justify="left", wraplength=600).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 25), padx=40)
    
    summary_data = {
        "Full Name:": app.new_enrollment_data.get('full_name'), "Username:": app.new_enrollment_data.get('username'),
        "Password:": '******', "Email:": app.new_enrollment_data.get('email'),
        "Voice Pattern:": "Saved"
    }
    for i, (label, value) in enumerate(summary_data.items()):
        tk.Label(card, text=label, font=font_text, fg="white", bg=LIGHT_CARD_BG).grid(row=i + 2, column=0, sticky="w", pady=5, padx=40)
        tk.Label(card, text=value, font=font_text, fg="white", bg=LIGHT_CARD_BG).grid(row=i + 2, column=1, sticky="w", pady=5, padx=20)
    
    tk.Button(card, text="Finish", font=font_button, bg=config.BUTTON_LIGHT_COLOR, fg=config.BUTTON_LIGHT_TEXT_COLOR, relief="flat", padx=30, pady=5, command=app._finish_enrollment).grid(row=len(summary_data) + 2, column=0, columnspan=2, pady=30)

def finish_enrollment(app):
    messagebox.showinfo("Success", "New user enrollment complete! Please log in.")
    app.just_enrolled_username = app.new_enrollment_data.get("username")
    app.just_enrolled = True
    app.enrollment_state = 'not_started'
    app.show_home_screen()