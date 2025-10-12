import tkinter as tk
import frontend_config as config

def set_background_image(app):
    """Sets the background image on the main canvas."""
    app.canvas.create_image(0, 0, anchor="nw", image=app.bg_img)

def create_header(app, show_nav=True):
    """Creates the top header with logo, navigation, and status icons."""
    nav_y_center, line_y, side_padding = 50, 70, 40
    app.canvas.create_image(side_padding, line_y / 1.2, anchor="w", image=app.logo_img, tags="logo")
    
    current_x = app.width - side_padding

    # Info icon
    info_tag = "info_icon"
    info_img_id = app.canvas.create_image(current_x - 11, nav_y_center, image=app.info_img, tags=info_tag)
    app.canvas.tag_bind(info_tag, "<Button-1>", app.show_about_screen)
    app.canvas.tag_bind(info_tag, "<Enter>", lambda e: app.canvas.config(cursor="hand2"))
    app.canvas.tag_bind(info_tag, "<Leave>", lambda e: app.canvas.config(cursor=""))
    bbox_info = app.canvas.bbox(info_img_id)

    # Help icon
    current_x -= 32 
    help_tag = "help_icon"
    help_img_id = app.canvas.create_image(current_x - 11, nav_y_center, image=app.help_img, tags=help_tag)
    app.canvas.tag_bind(help_tag, "<Button-1>", app.show_help_screen)
    app.canvas.tag_bind(help_tag, "<Enter>", lambda e: app.canvas.config(cursor="hand2"))
    app.canvas.tag_bind(help_tag, "<Leave>", lambda e: app.canvas.config(cursor=""))

    # Dynamic Navigation Tabs
    if show_nav:
        start_x = 180
        is_enrolled = getattr(app, "user_data", {}).get("enrolled", False)

    nav_map = {
        "home": app.show_home_screen,
        "applications": app.show_applications_screen,
        "enrollment": app.navigate_to_enrollment,
    }

    #if is_enrolled:
    #    nav_map["profile"] = app.show_profile_screen
    #else:
    #    nav_map["enrollment"] = app.navigate_to_enrollment

    app.nav_widgets = {}
    first_tab_bbox = None
    for key, command in nav_map.items():
        text, tag = key.capitalize(), f"nav_{key}"

        text_id = app.canvas.create_text(
            start_x, nav_y_center,
            text=text,
            font=app.font_nav,
            fill=config.TEXT_COLOR,
            anchor="w",
            tags=tag
        )
        bbox = app.canvas.bbox(text_id)

        pad_x, pad_y = 14, 10
        rect_id = app.canvas.create_round_rectangle(
            bbox[0] - pad_x, bbox[1] - pad_y,
            bbox[2] + pad_x, bbox[3] + pad_y,
            radius=20,
            fill="white",
            outline="",
            state="hidden"
        )
        app.canvas.tag_lower(rect_id, text_id)

        app.canvas.tag_bind(tag, "<Button-1>", lambda e, cmd=command: cmd())
        app.canvas.tag_bind(tag, "<Enter>", lambda e: app.canvas.config(cursor="hand2"))
        app.canvas.tag_bind(tag, "<Leave>", lambda e: app.canvas.config(cursor=""))

        app.nav_widgets[key] = {"text_id": text_id, "rect_id": rect_id}

        if first_tab_bbox is None:
            first_tab_bbox = bbox
        start_x = bbox[2] + 70

    if first_tab_bbox and bbox_info:
        line_x0 = first_tab_bbox[0]
        line_x1 = bbox_info[2]
        app.canvas.create_line(line_x0, line_y, line_x1, line_y, fill=config.TEXT_COLOR, width=1)

def update_nav_selection(app, key):
    """Updates the visual selection indicator for the navigation tabs."""
    if not key:
        return
    key = key.lower()

    for k, w in app.nav_widgets.items():
        app.canvas.itemconfig(w["text_id"], font=app.font_nav, fill=config.TEXT_COLOR)
        app.canvas.itemconfig(w["rect_id"], state="hidden")

    if key in app.nav_widgets:
        w = app.nav_widgets[key]
        app.canvas.itemconfig(w["text_id"], font=app.font_nav_active, fill="#7C2E50")
        app.canvas.itemconfig(w["rect_id"], state="normal")

def clear_content_frame(app):
    """Destroys all widgets in the main content frame."""
    for w in app.content_frame.winfo_children():
        w.destroy()
    app.content_frame.config(bg="#AD567C", bd=0)

def create_main_card(app, width=600, height=400):
    """Clears the content frame and creates a new main card to hold content."""
    clear_content_frame(app)
    card = tk.Frame(
        app.content_frame,
        bg=config.CARD_BG_COLOR,
        relief="solid",
        bd=1,
        width=width,
        height=height
    )
    card.pack(pady=0)
    card.pack_propagate(False)
    return card

def create_rounded_button(parent, text, command, app=None, bg="#F5F5F5", fg="#000000"):
    """Reusable rounded-style button."""
    import tkinter.font as tkFont
    font_button = tkFont.Font(family="Poppins", size=10)

    btn = tk.Button(
        parent,
        text=text,
        font=font_button,
        bg=bg,
        fg=fg,
        relief="flat",
        padx=16,
        pady=6,
        command=command
    )
    btn.config(bd=0, highlightthickness=0)
    btn.pack(pady=5)
    return btn

def _create_round_rectangle(self, x1, y1, x2, y2, radius=25, **kwargs):
    points = [
        x1 + radius, y1,
        x2 - radius, y1,
        x2, y1,
        x2, y1 + radius,
        x2, y2 - radius,
        x2, y2,
        x2 - radius, y2,
        x1 + radius, y2,
        x1, y2,
        x1, y2 - radius,
        x1, y1 + radius,
        x1, y1
    ]
    return self.create_polygon(points, smooth=True, **kwargs)

tk.Canvas.create_round_rectangle = _create_round_rectangle
