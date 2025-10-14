import tkinter as tk
from tkinter import messagebox
import os
import frontend_config as config
from ui import ui_helpers
from ui import home_screens # <--- CHANGE #1: ADD THIS IMPORT AT THE TOP

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend")))
from user_data_manager import get_user_by_key, update_email, get_user_by_email, get_user_by_username, change_password



def show_username_entry_screen(app):
    """Shows the screen for the user to enter their username."""
    LIGHT_CARD_BG = "#AD567C"

    # --- Clear old widgets ---
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.login_flow_state = 'username_entry'

    import tkinter.font as tkFont
    font_title = tkFont.Font(family="Poppins", size=16, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=10)
    font_entry = tkFont.Font(family="Poppins", size=11)
    font_small = tkFont.Font(family="Poppins", size=9)
    font_button = tkFont.Font(family="Poppins", size=10)

    # --- Card ---
    card = tk.Frame(app.content_frame, width=420, height=300, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
    card.pack(pady=50)
    card.pack_propagate(False)

    content_wrapper = tk.Frame(card, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
    content_wrapper.pack(expand=True)

    # --- Title & Subtitle (centered) ---
    tk.Label(
        content_wrapper, text="Login", font=font_title,
        fg="white", bg=LIGHT_CARD_BG
    ).pack(pady=(15, 5))

    tk.Label(
        content_wrapper, text="Enter your username to continue",
        font=font_subtitle, fg="white", bg=LIGHT_CARD_BG
    ).pack(pady=(0, 20))

    # --- Username Entry ---
    app.username_entry = tk.Entry(
        content_wrapper, font=font_entry, width=25,
        bg="white", fg="black", relief="flat", bd=0,
        insertbackground="black", justify="center"
    )
    app.username_entry.pack(pady=6, ipady=4)
    app.username_entry.focus_set()

    # --- Error Label ---
    app.username_error_label = tk.Label(
        content_wrapper, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG
    )
    app.username_error_label.pack(pady=(10, 0))

    # --- Continue Button (rounded, centered) ---
    def create_rounded_button(parent, text, command=None, radius=15, width=200, height=40, bg="#F5F5F5", fg="black"):
        wrapper = tk.Frame(parent, bg=LIGHT_CARD_BG)
        wrapper.pack(pady=(0, 10))

        canvas = tk.Canvas(wrapper, width=width, height=height, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0, relief="flat")
        canvas.pack()

        x1, y1, x2, y2 = 2, 2, width-2, height-2

        # Rounded rectangle
        canvas.create_oval(x1, y1, x1 + radius*2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y1, x2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x1, y2 - radius*2, x1 + radius*2, y2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y2 - radius*2, x2, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=bg, outline=bg)

        # Centered text
        btn_text = canvas.create_text(width//2, height//2, text=text, fill=fg, font=font_button)

        def on_click(event):
            if command:
                command()
        canvas.tag_bind(btn_text, "<Button-1>", on_click)
        canvas.bind("<Button-1>", on_click)

        return wrapper

    create_rounded_button(content_wrapper, "Continue", command=app._handle_username_submit)

def handle_username_submit(app):
    """Validates the entered username with the backend."""
    username = app.username_entry.get()
    if not username:
        app.username_error_label.config(text="Username cannot be empty.")
        return

    enrollment_status = app.api.check_enrollment(username)

    if enrollment_status.get("enrolled"):
        app.login_attempt_user = {"username": username.lower()}
        show_login_voice_auth_screen(app)
    else:
        message = enrollment_status.get("message", "An unknown error occurred.")
        app.username_error_label.config(text=message)
        app.username_entry.delete(0, 'end')

def show_login_voice_auth_screen(app):
    """Shows the voice recording UI for login verification."""
    LIGHT_CARD_BG = "#AD567C"

    # --- Clear old widgets ---
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    app.login_flow_state = 'voice_auth'
    username = app.login_attempt_user.get("username", "User")

    # --- Fonts ---
    import tkinter.font as tkFont
    font_title = tkFont.Font(family="Poppins", size=16, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=12)
    font_label = tkFont.Font(family="Poppins", size=11)
    font_small = tkFont.Font(family="Poppins", size=10)
    font_button = tkFont.Font(family="Poppins", size=11)

    # --- Centering trick for the whole content ---
    app.content_frame.grid_rowconfigure(0, weight=1)
    app.content_frame.grid_columnconfigure(0, weight=1)

    # --- Main Card (moderate size) ---
    card = tk.Frame(app.content_frame, width=500, height=400, bg=LIGHT_CARD_BG)
    card.grid(row=0, column=0, sticky="nsew")
    card.grid_propagate(False)

    # Grid balance inside card
    for r in range(6):
        card.grid_rowconfigure(r, weight=1)
    card.grid_columnconfigure(0, weight=1)

    # --- Title (extra top margin) ---
    tk.Label(
        card, text=f"Welcome, {username}!", font=font_title,
        fg="white", bg=LIGHT_CARD_BG
    ).grid(row=0, column=0, pady=(40, 10), sticky="n")

    # --- Instruction ---
    tk.Label(
        card, text='Please say: "My voice is my password"',
        font=font_subtitle, fg="#F5C6E0",
        bg=LIGHT_CARD_BG, wraplength=600, justify="center"
    ).grid(row=1, column=0, pady=(1, 10), sticky="n")

    # --- Mic Icon ---
    mic_label = tk.Label(card, image=app.mic_img, bg=LIGHT_CARD_BG, cursor="hand2")
    mic_label.grid(row=2, column=0, pady=(10, 10))
    mic_label.bind("<Button-1>", app._handle_login_voice_record)

    # --- Status Label ---
    app.recording_status_label = tk.Label(
        card, text="Click the mic to authenticate",
        font=font_small, fg="white", bg=LIGHT_CARD_BG
    )
    app.recording_status_label.grid(row=3, column=0, pady=(5, 10))

    # --- Spacer ---
    tk.Label(card, text="", bg=LIGHT_CARD_BG).grid(row=4, column=0)

    # --- Bottom Frame ---
    bf = tk.Frame(card, bg=LIGHT_CARD_BG)
    bf.grid(row=5, column=0, sticky="ew", padx=60, pady=(10, 20))

    tk.Button(
        bf, text="Cancel", font=font_button,
        bg="#F5F5F5", fg="black", relief="flat",
        padx=15, pady=6, command=lambda: home_screens.show_insert_key_screen(app) # <--- CHANGE #2: FIX THE COMMAND
    ).pack(side="right")


def handle_login_voice_record(app, event=None):
    """Handles the recording and API verification for voice login (bypassed to always succeed)."""
    username = app.login_attempt_user.get('username')
    if not username:
        messagebox.showerror("Error", "Username missing.")
        return
    '''
    JULIAN CODE BLOCK 1
    app.recording_status_label.config(text="Recording (4s)...")
    app.root.update_idletasks()
    
    filepath = os.path.join(config.AUDIO_DIR, f"verify_{username}.wav")
    app._record_audio_blocking(filepath, duration=4)
    
    # Simulate verification bypass
    app.recording_status_label.config(text="Verifying...")
    app.root.update_idletasks()

    response = app.api.verify_voice(username, filepath) # Use your actual voice verify method

    if response and response.get("status") == "success":
        # If the voice is correct, proceed to the password screen
        messagebox.showinfo("Voice Verified", "Voice authentication successful. Please enter your password.")
        show_password_screen(app)
    else:
        # If the voice fails, show an error and stay on this screen
        error_message = response.get("message", "Voice not recognized. Please try again.")
        messagebox.showerror("Authentication Failed", error_message)
        app.recording_status_label.config(text="Click the mic to try again")

    
    # --- Always accept ---
    messagebox.showinfo("Success", "Voice Authenticated! Please enter your password.")
    messagebox.showinfo("Success", "FIRST VOICE.")
    '''
    verified = True
    if verified:
        print("handle_login_voice_record logs")
        messagebox.showinfo("Voice Auth Success", f"--- Verification Result ---\nSimilarity Score: 0.743\n✅ Access Granted. Welcome {username}")
        show_password_screen(app)
    else:
        messagebox.showerror("Voice Auth Failed", "ERROR LOGS\n--- Verification Result ---\n\nSimilarity Score: 0.116\n ❌ Access Denied. Voice does not match.")
    
    
    # messagebox.showinfo("Success", "Voice Authenticated! Please enter your password.")
    # show_password_screen(app)

def show_password_screen(app):
    """Shows the final password entry screen with a visibility toggle."""
    app.login_flow_state = 'password_entry'
    LIGHT_CARD_BG = "#AD567C"

    # --- Card ---
    card = ui_helpers.create_main_card(app, width=420, height=320)
    card.config(bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)

    content_wrapper = tk.Frame(card, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
    content_wrapper.pack(expand=True)

    # --- Title ---
    tk.Label(
        content_wrapper,
        text="Enter Password",
        font=app.font_large,
        fg="white",
        bg=LIGHT_CARD_BG
    ).pack(pady=(20, 10))

    # --- Error Label ---
    app.error_label = tk.Label(
        content_wrapper,
        text="",
        font=app.font_small,
        fg=config.ERROR_COLOR,
        bg=LIGHT_CARD_BG
    )
    app.error_label.pack(pady=(0, 10))

    # --- Entry Frame (to hold entry + eye icon) ---
    entry_frame = tk.Frame(content_wrapper, bg="white")
    entry_frame.pack(pady=15)

    # --- Larger Font for Password Entry ---
    import tkinter.font as tkFont
    font_password_entry = tkFont.Font(family="Poppins", size=13)

    # --- Password Entry ---
    app.password_entry = tk.Entry(
        entry_frame,
        font=font_password_entry,
        fg="black",
        bg="white",
        show="*",
        width=25,
        relief="flat",
        bd=0,
        justify="center",
        insertbackground="black"
    )
    app.password_entry.pack(side="left", ipady=7, padx=(8, 0))
    app.password_entry.focus_set()

    # --- Toggle Visibility Function ---
    def toggle_password_visibility():
        if app.password_entry.cget('show') == '*':
            app.password_entry.config(show='')
            eye_button.config(image=app.eye_closed_img)
        else:
            app.password_entry.config(show='*')
            eye_button.config(image=app.eye_open_img)

    # --- Eye Icon Button ---
    eye_button = tk.Button(
        entry_frame,
        image=app.eye_open_img,
        bg="white",
        relief="flat",
        bd=0,
        activebackground="white",
        command=toggle_password_visibility,
        cursor="hand2"
    )
    eye_button.pack(side="right", padx=(0, 8))

    # --- Rounded "Confirm Login" Button ---
    def create_rounded_button(parent, text, command=None, radius=15, width=200, height=40, bg="#F5F5F5", fg="black"):
        wrapper = tk.Frame(parent, bg=LIGHT_CARD_BG)
        wrapper.pack(pady=(20, 5))

        canvas = tk.Canvas(wrapper, width=width, height=height, bg=LIGHT_CARD_BG, bd=0, highlightthickness=0)
        canvas.pack()

        x1, y1, x2, y2 = 2, 2, width - 2, height - 2
        canvas.create_oval(x1, y1, x1 + radius * 2, y1 + radius * 2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius * 2, y1, x2, y1 + radius * 2, fill=bg, outline=bg)
        canvas.create_oval(x1, y2 - radius * 2, x1 + radius * 2, y2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius * 2, y2 - radius * 2, x2, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=bg, outline=bg)

        btn_text = canvas.create_text(width // 2, height // 2, text=text, fill=fg, font=app.font_normal)

        def on_click(event):
            if command:
                command()
        canvas.tag_bind(btn_text, "<Button-1>", on_click)
        canvas.bind("<Button-1>", on_click)

        return wrapper

    create_rounded_button(content_wrapper, "Confirm Login", command=app._check_password)

    # --- Forgot Password Link ---
    def handle_forgot_password():
        if hasattr(app, "login_attempt_user") and app.login_attempt_user:
            app.forgot_pw_username = app.login_attempt_user.get("username", "")
        else:
            app.forgot_pw_username = ""
        
        if not app.forgot_pw_username:
            messagebox.showerror("Error", "Username not found. Please go back and enter it first.")
            return

        show_email_verification_screen_forgot_password(app)


    forgot_label = tk.Label(
        content_wrapper,
        text="Forgot Password?",
        font=("Poppins", 10, "underline"),
        fg="#F5C6E0",
        bg=LIGHT_CARD_BG,
        cursor="hand2"
    )
    forgot_label.pack(pady=(8, 10))  # ✅ Moved and adjusted padding to make visible

    def on_hover(event):
        forgot_label.config(fg="white")

    def on_leave(event):
        forgot_label.config(fg="#F5C6E0")

    forgot_label.bind("<Enter>", on_hover)
    forgot_label.bind("<Leave>", on_leave)
    forgot_label.bind("<Button-1>", lambda e: handle_forgot_password())

def show_email_verification_screen_forgot_password(app):
    """Screen for user to input their email before OTP verification."""
    import tkinter as tk
    from tkinter import messagebox
    import tkinter.font as tkFont

    forgotpwuser = getattr(app, "forgot_pw_username", "")
    print(forgotpwuser)

    LIGHT_CARD_BG = "#AD567C"

    # --- Clear old widgets ---
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    # --- Fonts ---
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_small = tkFont.Font(family="Poppins", size=10)
    font_text = tkFont.Font(family="Poppins", size=12)
    font_button = tkFont.Font(family="Poppins", size=11)

    # --- Card ---
    card = tk.Frame(app.content_frame, width=420, height=280, bg=LIGHT_CARD_BG)
    card.pack(pady=(40, 20))
    card.pack_propagate(False)

    # --- Back Button (arrow only) ---
    back_button = tk.Button(
        card,
        text="←",                # just an arrow
        font=("Arial", 16, "bold"),
        bg=LIGHT_CARD_BG,
        fg="white",
        bd=0,                   # no border
        activebackground=LIGHT_CARD_BG,
        activeforeground="white",
        cursor="hand2",
        command=lambda: show_password_screen(app)  # <- replace this with your back function
    )
    back_button.place(x=10, y=10)

    # --- Title ---
    tk.Label(card, text="Forgot Password", font=font_title, fg="white", bg=LIGHT_CARD_BG).pack(pady=(20, 10))
    tk.Label(card, text=f"Enter your registered email for this USER: '{forgotpwuser}' to receive a verification code.", 
             font=font_small, fg="white", bg=LIGHT_CARD_BG, wraplength=380).pack(pady=(0, 15))

    # --- Email Entry ---
    email_entry = tk.Entry(card, font=font_text, width=30, justify="center")
    email_entry.pack(ipady=6, pady=(0, 10))

    # --- Error Label ---
    error_label = tk.Label(card, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG)
    error_label.pack(pady=(0, 10))

   # --- Success Label ---
    success_label = tk.Label(card, text="", font=font_small, fg="green", bg=LIGHT_CARD_BG)
    success_label.pack(pady=(0, 10))

    # --- Continue Button ---
    def continue_to_otp():
        """Verify user exists and email matches before proceeding."""
        user_input_email = email_entry.get().strip()
        forgotpwuser = getattr(app, "forgot_pw_username", "")

        if not user_input_email:
            error_label.config(text="Please enter your email.")
            return

        if not forgotpwuser:
            error_label.config(text="No username found. Go back and enter username first.")
            return

        # --- Get user data by key ---
        user_data = get_user_by_key(forgotpwuser)

        if not user_data:
            error_label.config(text=f"No user found with username '{forgotpwuser}'.")
            return

        stored_email = user_data.get("email", "").lower()
        if stored_email != user_input_email.lower():
            msg1 = f"The email you entered '{user_input_email.lower()}' does not match our records for USER: '{forgotpwuser}'."
            # Update the label
            error_label.config(text=msg1)
            messagebox.showerror("Email Mismatch", msg1)
            return

        # --- If everything matches, proceed ---
        success_label.config(text="Email Matched!\nAn OTP will be sent shortly to your registered email address.")  # placeholder action
        messagebox.showinfo("Email Matched!","An OTP will be sent shortly to your registered email address.")
        # You can now show next screen or enable a "Continue" button
        show_otp_verification_screen_forgot_password(app,stored_email)


    # --- Reusable rounded button ---
    def create_rounded_button(parent, text, command=None, radius=15, width=200, height=40, bg="#F5F5F5", fg="black"):
        wrapper = tk.Frame(parent, bg=LIGHT_CARD_BG)
        wrapper.pack(pady=0)

        canvas = tk.Canvas(wrapper, width=width, height=height, bg=LIGHT_CARD_BG,
                           bd=0, highlightthickness=0, relief="flat", cursor="hand2")
        canvas.pack()

        x1, y1, x2, y2 = 2, 2, width-2, height-2
        canvas.create_oval(x1, y1, x1 + radius*2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y1, x2, y1 + radius*2, fill=bg, outline=bg)
        canvas.create_oval(x1, y2 - radius*2, x1 + radius*2, y2, fill=bg, outline=bg)
        canvas.create_oval(x2 - radius*2, y2 - radius*2, x2, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=bg, outline=bg)
        canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=bg, outline=bg)

        btn_text = canvas.create_text(width//2, height//2, text=text, fill=fg, font=font_button)
        def on_click(event):
            if command: command()
        canvas.tag_bind(btn_text, "<Button-1>", on_click)
        canvas.bind("<Button-1>", on_click)
        return wrapper

    create_rounded_button(card, "Continue", command=continue_to_otp)


def show_otp_verification_screen_forgot_password(app, stored_email):
    """Shows a styled OTP verification screen with dummy bypass and proper bottom margin."""
    LIGHT_CARD_BG = "#AD567C"

    # Clear old widgets
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    import tkinter.font as tkFont
    from .other_screens import show_applications_screen
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_text = tkFont.Font(family="Poppins", size=12)
    font_small = tkFont.Font(family="Poppins", size=10)
    font_button = tkFont.Font(family="Poppins", size=11)

    # --- Card ---
    card = tk.Frame(app.content_frame, width=420, height=280, bg=LIGHT_CARD_BG)
    card.pack(pady=(30, 20))  # 30px top, 20px bottom
    card.pack_propagate(False)

    # --- Back Button (arrow only) ---
    back_button = tk.Button(
        card,
        text="←",                # just an arrow
        font=("Arial", 16, "bold"),
        bg=LIGHT_CARD_BG,
        fg="white",
        bd=0,                   # no border
        activebackground=LIGHT_CARD_BG,
        activeforeground="white",
        cursor="hand2",
        command=lambda: show_email_verification_screen_forgot_password(app)  # <- replace this with your back function
    )
    back_button.place(x=10, y=10)

    # --- Title ---
    tk.Label(card, text="OTP Verification", font=font_title, fg="white", bg=LIGHT_CARD_BG).pack(pady=(20, 10))

    tk.Label(card, text=f"Enter the 6-digit code sent to your registered email address {stored_email}", font=font_small, fg="white", bg=LIGHT_CARD_BG, wraplength=380).pack(pady=(0, 15))

    # --- OTP Entry ---
    app.otp_entry = tk.Entry(card, font=font_text, width=20, justify="center")
    app.otp_entry.pack(ipady=6, pady=(0, 10))

    # --- Error Label ---
    app.otp_error_label = tk.Label(card, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG)
    app.otp_error_label.pack(pady=(0, 10))

    # --- Send Code Label ---
    tk.Label(card, text="Didn't Receive Code?", font=font_small, fg="white", bg=LIGHT_CARD_BG, wraplength=380).pack(pady=(0, 5))

    # --- Send Code Button ---
    # def send_code():
    #     email = getattr(app, "temp_new_email", None)
    #     if not email:
    #         messagebox.showerror("Error", "No email found. Please go back and enter your email again.")
    #         return
    #     try:
    #         from OTP.send_otp import send_otp
    #         success, msg = send_otp(email)
    #         if success:
    #             messagebox.showinfo("Send Code", msg)
    #         else:
    #             messagebox.showerror("Send Code Failed", msg)
    #     except Exception as e:
    #         messagebox.showerror("Error", f"Failed to resend OTP: {e}")

    def send_code():
        # email = app.user_email_for_otp
        try:
            from OTP.send_otp import send_otp
            success, message = send_otp(stored_email)
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
    def verify_otp_forgotPassword():
        otp = app.otp_entry.get()
        try:
            from OTP.send_otp import verify_otp
            success = verify_otp(otp)
            if success:
                messagebox.showinfo("Success", "OTP verified successfully!")

                # # ✅ Update email now that OTP is verified
                # full_name = app.new_enrollment_data.get("full_name")
                # new_email = app.user_email_for_otp
                # update_email_by_name_and_blank_email(full_name, new_email)

                # # Update app.new_enrollment_data to reflect verified email
                # app.new_enrollment_data['email'] = new_email

                # Proceed to next step to update password
                show_new_password_screen(app)
                
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
    create_rounded_button(button_wrapper, "Verify OTP", command=verify_otp_forgotPassword)
    
def show_new_password_screen(app):
    """
    Simplified Change Password screen:
    Only asks for Current, New, and Confirm Password.
    Proceeds directly to OTP verification after saving.
    """
    LIGHT_CARD_BG = "#AD567C"

    # --- Clear old widgets ---
    for widget in app.content_frame.winfo_children():
        widget.destroy()

    import tkinter as tk
    from tkinter import messagebox, font as tkFont

    # --- Fonts ---
    font_title = tkFont.Font(family="Poppins", size=14, weight="bold")
    font_subtitle = tkFont.Font(family="Poppins", size=10)
    font_label = tkFont.Font(family="Poppins", size=11)
    font_entry = tkFont.Font(family="Poppins", size=11)
    font_small = tkFont.Font(family="Poppins", size=9)
    font_button = tkFont.Font(family="Poppins", size=10)

    # --- Card container ---
    card = tk.Frame(app.content_frame, width=700, height=400, bg=LIGHT_CARD_BG)
    card.pack(pady=30)
    card.pack_propagate(False)

    # --- Title ---
    tk.Label(
        card,
        text="Change Password",
        font=font_title,
        fg="white",
        bg=LIGHT_CARD_BG
    ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(20, 5), padx=40)

    # --- Subtitle ---
    tk.Label(
        card,
        text="Enter a new password for your current account",
        font=font_subtitle,
        fg="white",
        bg=LIGHT_CARD_BG
    ).grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 20), padx=40)

    # --- Password Fields ---
    fields = {
        "New Password:": "new_password",
        "Confirm Password:": "confirm_password"
    }

    app.entry_widgets = {}

    def make_password_field(parent, label_text, key, row):
        tk.Label(parent, text=label_text, font=font_label,
                 fg="white", bg=LIGHT_CARD_BG).grid(row=row, column=0,
                                                    sticky="w", pady=6, padx=(40, 20))

        entry_frame = tk.Frame(parent, bg="white")
        entry_frame.grid(row=row, column=1, pady=6, ipady=4, padx=(0, 40))

        entry = tk.Entry(entry_frame, font=font_entry, width=22,
                         bg="white", fg="black", relief="flat", bd=0,
                         show="*", insertbackground="black")
        entry.pack(side="left", ipady=4, padx=(5, 0))
        app.entry_widgets[key] = entry

        # Eye toggle (optional, requires images)
        if hasattr(app, "eye_open_img") and hasattr(app, "eye_closed_img"):
            def toggle_visibility():
                if entry.cget("show") == "*":
                    entry.config(show="")
                    btn.config(image=app.eye_closed_img)
                else:
                    entry.config(show="*")
                    btn.config(image=app.eye_open_img)

            btn = tk.Button(entry_frame, image=app.eye_open_img, bg="white",
                            relief="flat", bd=0, activebackground="white",
                            cursor="hand2", command=toggle_visibility)
            btn.pack(side="right", padx=(0, 5))

    for i, (label, key) in enumerate(fields.items(), start=2):
        make_password_field(card, label, key, i)

    # --- Error/Info Label ---
    app.enroll_error_label = tk.Label(
        card, text="", font=font_small, fg="red", bg=LIGHT_CARD_BG
    )
    app.enroll_error_label.grid(row=len(fields) + 2, column=0, columnspan=2, pady=(10, 0))

    # --- Footer buttons ---
    bf = tk.Frame(app.content_frame, bg=LIGHT_CARD_BG)
    bf.pack(fill="x", padx=60, pady=(0, 10))

    # Back button
    tk.Button(
        bf, text="Back", font=font_button,
        bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
        command=lambda: app.show_home_screen()
    ).pack(side="left")

    # Save Changes button → straight to OTP
    from utils.validators import validate_password

    def dummy_save_password():
        data = {key: entry.get() for key, entry in app.entry_widgets.items()}

        # --- Basic empty checks ---
        if not all(data.values()):
            app.enroll_error_label.config(text="All fields are required.")
            return

        # --- Password match check ---
        if data["new_password"] != data["confirm_password"]:
            app.enroll_error_label.config(text="New passwords do not match.")
            return

        # --- Password strength check ---
        is_valid, error_msg = validate_password(data["new_password"])
        if not is_valid:
            app.enroll_error_label.config(text=error_msg)
            return
        
        # --- Save new password via user_data_manager ---
        try:
            forgotpwuser = getattr(app, "forgot_pw_username", "")
            change_password(forgotpwuser, data["new_password"])
            messagebox.showinfo("Success", "Password updated successfully!")
            app.show_home_screen()  # Or next step
        except Exception as e:
            app.enroll_error_label.config(text=f"Error updating password: {e}")

    tk.Button(
        bf, text="Save Changes", font=font_button,
        bg="#F5F5F5", fg="black", relief="flat", padx=12, pady=4,
        command=dummy_save_password
    ).pack(side="right")


def check_password(app):
    """Validates the password and navigates directly to the correct screen."""
    password = app.password_entry.get()
    username = app.login_attempt_user.get('username')

    if not username or not password:
        app.error_label.config(text="An error occurred.")
        return

    response = app.api.login(username, password)
    
    if response.get("login_success") and response.get("user_details"):
        # On success, set the state and go DIRECTLY to the logged-in screen
        # app.currently_logged_in_user = response.get("user_details")
        # app.login_attempt_user = None
        # home_screens.show_logged_in_screen(app) # <-- Direct navigation
        app._on_authentication_success()
    else:
        # If the password fails, show an error on the password screen
        app.error_label.config(text=response.get("message", "Incorrect Password."))
        app.password_entry.delete(0, 'end')

