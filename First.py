
"""
Smart Panel UI (Tkinter) - 3 Pages: Camera, Alarm, Video
--------------------------------------------------------
- Top area shows webcam feed (with graceful fallback to a static placeholder)
- Bottom bar contains 3 large buttons: Camera, Alarm, Video
- Bottom-right shows Date + Time and a simulated temperature
- Each page draws its own overlay to resemble the provided mockups
  (REC dot, Video playback HUD, Alarm            # Border for visual effect
            self.overlay_canvas.create_rectangle(
                x1-2, y1-2, 
                x2+2, y2+2, 
                fill="#808080", outline="", width=0
            )l panel        thumb_pos = scroll_top + int((scroll_height - thumb_height) * (1 - self.volume_value/100))
        self.overlay_canvas.create_rectangle(right_x-6, thumb_pos, right_x+6, thumb_pos+thumb_height, 
                                            fill=COLORS["scrollbar_thumb"], outline="", width=0)
        # Volume icon - draw muted speaker icon like reference
        icon_y = scroll_top-20
        # Draw speaker box (small rectangle on left)
        self.overlay_canvas.create_rectangle(right_x-8, icon_y-3, right_x-5, icon_y+3, 
                                            fill="#FFFFFF", outline="")
        # Draw speaker cone (trapezoid)
        self.overlay_canvas.create_polygon([
            right_x-5, icon_y-3,
            right_x-5, icon_y+3,
            right_x-1, icon_y+5,
            right_x-1, icon_y-5,
        ], fill="#FFFFFF", outline="")
        # Draw X (mute symbol)
        self.overlay_canvas.create_line(right_x+1, icon_y-4, right_x+5, icon_y+4, 
                                       fill="#FFFFFF", width=2)
        self.overlay_canvas.create_line(right_x+1, icon_y+4, right_x+5, icon_y-4, 
                                       fill="#FFFFFF", width=2) & feel).
- Colors approximated to match the reference images.

Run:
    python smart_panel_ui.py

Dependencies:
    pip install opencv-python pillow
"""

import sys
import time
import datetime as dt
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw, ImageFont

# Try importing cv2; if not available, fall back to placeholder image
try:
    import cv2
except Exception:
    cv2 = None

# -----------------------------
# Color Palette (matching reference image)
# -----------------------------
COLORS = {
    "bg": "#424242",
    "panel_bg": "#424242",
    "video_bg": "#424242",
    "overlay": "#424242",
    "overlay_light": "#FFFFFF",
    "button": "#F5F5F5",
    "button_bg": "#F5F5F5",
    "button_hover": "#E0E0E0",
    "text": "#FFFFFF",
    "text_dark": "#2C2C2C",
    "scrollbar_track": "#5A5A5A",
    "scrollbar_thumb": "#9A9A9A",
    "accent": "#FF3B30",
    "accent_blue": "#007AFF",
}

FONT_CACHE = {}

def get_font(size: int, bold=False):
    """Return a cached Tk font-like PIL font (for overlay drawings)."""
    key = (size, bold)
    if key in FONT_CACHE:
        return FONT_CACHE[key]
    # Try to load a common sans font; otherwise use default PIL font
    try:
        # DejaVuSans is bundled with many Python installs
        path = "/usr/share/fonts/truetype/dejavu/DejaVuSans{}.ttf".format("-Bold" if bold else "")
        font = ImageFont.truetype(path, size)
    except Exception:
        # Default bitmap font fallback
        font = ImageFont.load_default()
    FONT_CACHE[key] = font
    return font

class SmartPanelApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Smart Panel UI")
        self.configure(bg=COLORS["bg"])
        self.geometry("1024x600")
        self.minsize(900, 520)

        # State
        self.current_page = "camera"
        self.temp_c = 20.0
        
        # Alarm page spinbox values - initialize with current time
        now = dt.datetime.now()
        self.alarm_left_value = now.hour  # Hours (0-23)
        self.alarm_right_value = now.minute  # Minutes (0-59)
        self.alarm_set_time = None  # Store the confirmed alarm time (None = not set yet)
        
        # Scrollbar values (0-100)
        self.brightness_value = 50
        self.volume_value = 50
        
        # Camera recording state
        self.is_recording = False

        # Video capture (graceful fallback if unavailable)
        self.cap = None
        self.camera_available = False
        self.placeholder_img = self._make_placeholder()
        if cv2 is not None:
            # Try different camera indices and backends
            # For Mac: try AVFoundation backend first, index 0 is usually built-in, 1 is external
            camera_configs = [
                (0, cv2.CAP_AVFOUNDATION),  # Built-in camera with AVFoundation
                (1, cv2.CAP_AVFOUNDATION),  # External/Continuity camera with AVFoundation
                (0, cv2.CAP_ANY),           # Built-in camera with default backend
                (1, cv2.CAP_ANY),           # External camera with default backend
                (2, cv2.CAP_ANY),           # Third camera option
            ]
            
            for cam_index, backend in camera_configs:
                try:
                    print(f"Trying to open camera {cam_index} with backend {backend}...")
                    self.cap = cv2.VideoCapture(cam_index, backend)
                    # Set a reasonable resolution (if supported)
                    if self.cap is not None and self.cap.isOpened():
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                        
                        # Warm up the camera by discarding first few frames
                        print(f"Warming up camera {cam_index}...")
                        for i in range(10):
                            ret, test_frame = self.cap.read()
                            time.sleep(0.1)
                        
                        # Test if we can actually read a valid frame
                        ret, test_frame = self.cap.read()
                        if ret and test_frame is not None and test_frame.size > 0:
                            # Check if frame has actual data (not all black)
                            mean_value = test_frame.mean()
                            self.camera_available = True
                            print(f"✓ Camera {cam_index} opened successfully!")
                            print(f"  Resolution: {test_frame.shape[1]}x{test_frame.shape[0]}")
                            print(f"  Frame mean value: {mean_value:.2f} (checking for actual image data)")
                            if mean_value < 1.0:
                                print(f"  ⚠ Warning: Camera might be showing black screen (very low brightness)")
                            break
                        else:
                            print(f"✗ Camera {cam_index} opened but no valid frames")
                            self.cap.release()
                            self.cap = None
                    else:
                        self.cap = None
                except Exception as e:
                    print(f"✗ Camera {cam_index} failed: {e}")
                    if self.cap is not None:
                        try:
                            self.cap.release()
                        except:
                            pass
                    self.cap = None
            
            if not self.camera_available:
                print("⚠ No camera available. Using placeholder image.")

        # Layout frames
        self._build_layout()

        # Start loops
        self._update_time()
        self._update_video()

        # Exit handling
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------------- Layout ----------------
    def _build_layout(self):
        # Main container - full screen, no padding
        self.main = tk.Frame(self, bg=COLORS["panel_bg"], bd=0, highlightthickness=0)
        self.main.pack(fill="both", expand=True, padx=0, pady=0)

        # Video / content area (top) - remove padding
        self.video_frame = tk.Frame(self.main, bg=COLORS["video_bg"], height=420)
        self.video_frame.pack(side="top", fill="both", expand=True, padx=0, pady=0)

        # Use a stacked layout: base label for video, canvas for overlays
        self.video_label = tk.Label(self.video_frame, bg=COLORS["video_bg"])
        self.video_label.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.overlay_canvas = tk.Canvas(self.video_frame, bg=COLORS["video_bg"], highlightthickness=0, bd=0)
        self.overlay_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        # Bind mouse events for interactive controls
        self.overlay_canvas.bind("<Button-1>", self._on_canvas_click)
        self.overlay_canvas.bind("<B1-Motion>", self._on_canvas_drag)

        # Bottom bar - remove padding
        self.bottom_bar = tk.Frame(self.main, bg=COLORS["panel_bg"])
        self.bottom_bar.pack(side="bottom", fill="x", padx=20, pady=(0, 12))

        # Left: Three buttons with border style
        self.btn_container = tk.Frame(self.bottom_bar, bg=COLORS["panel_bg"])
        self.btn_container.pack(side="left")

        # Create buttons with individual borders
        btn_style = {
            "font": ("Arial", 20, "bold"),
            "fg": COLORS["text"],
            "bg": COLORS["button_bg"],
            "activebackground": COLORS["button_hover"],
            "bd": 0,
            "relief": "flat",
            "cursor": "hand2",
            "width": 8,
            "height": 3,
            "highlightthickness": 2,
            "highlightbackground": COLORS["panel_bg"],
            "highlightcolor": COLORS["panel_bg"]
        }

        self.btn_camera = tk.Button(
            self.btn_container, text="Camera", 
            command=lambda: self.show_page("camera"),
            **btn_style
        )
        self.btn_alarm = tk.Button(
            self.btn_container, text="Alarm",
            command=lambda: self.show_page("alarm"),
            **btn_style
        )
        self.btn_video = tk.Button(
            self.btn_container, text="Video",
            command=lambda: self.show_page("video"),
            **btn_style
        )
        
        # Pack buttons horizontally with spacing
        self.btn_camera.pack(side="left", padx=(0, 4))
        self.btn_alarm.pack(side="left", padx=4)
        self.btn_video.pack(side="left", padx=(4, 0))

        # Right: time + temp without border (no background)
        self.info_card = tk.Frame(self.bottom_bar, bg=COLORS["panel_bg"], relief="flat", bd=0)
        self.info_card.pack(side="right")
        
        self.info_inner = tk.Frame(self.info_card, bg=COLORS["panel_bg"])
        self.info_inner.pack(padx=24, pady=12)

        self.date_label = tk.Label(self.info_inner, text="--/--/----", font=("Arial", 20, "bold"),
                                   fg=COLORS["text_dark"], bg=COLORS["panel_bg"])
        
        # Time and temp on same line
        self.time_temp_frame = tk.Frame(self.info_inner, bg=COLORS["panel_bg"])
        self.time_label = tk.Label(self.time_temp_frame, text="--:--", font=("Arial", 20, "bold"),
                                   fg=COLORS["text_dark"], bg=COLORS["panel_bg"])
        self.temp_label = tk.Label(self.time_temp_frame, text="--.-°C", font=("Arial", 20, "bold"),
                                   fg=COLORS["text_dark"], bg=COLORS["panel_bg"])

        self.date_label.pack(anchor="center", pady=(0, 2))
        self.time_temp_frame.pack(anchor="center", pady=2)
        self.time_label.pack(side="left", padx=(0, 10))
        self.temp_label.pack(side="left")

        # Initial page highlight
        self._style_active_button()

    # ---------------- Overlays ----------------
    def _draw_overlay(self, img_w, img_h):
        """Draw page-specific overlay on the transparent canvas."""
        self.overlay_canvas.delete("all")
        
        # Store canvas dimensions for click detection
        self.canvas_w = img_w
        self.canvas_h = img_h

        if self.current_page == "camera":
            self._draw_camera_overlay(img_w, img_h)
        elif self.current_page == "video":
            self._draw_video_overlay(img_w, img_h)
        elif self.current_page == "alarm":
            self._draw_alarm_overlay(img_w, img_h)

    def _draw_camera_overlay(self, w, h):
        # Show set time at top right if alarm is set
        if self.alarm_set_time is not None:
            self.overlay_canvas.create_text(w-30, 30, text=f"Alarm: {self.alarm_set_time}", 
                                          fill=COLORS["text"], font=("Arial", 20, "bold"), anchor="e")
        
        # Draw scrollbars - use consistent positioning
        scroll_top = int(h*0.25)
        scroll_bottom = int(h*0.90)
        self._draw_scrollbars(w, h, scroll_top, scroll_bottom)

        # REC indicator - only show when recording
        if self.is_recording:
            self.overlay_canvas.create_text(130, 80, text="REC", fill=COLORS["text"], font=("Arial", 28, "bold"), anchor="w")
            self.overlay_canvas.create_oval(80, 60, 110, 90, fill=COLORS["accent"], width=0)
        
        # Camera/Record button in the center bottom
        btn_w = 140
        btn_h = 50
        btn_x = w // 2 - btn_w // 2
        btn_y = int(h * 0.88)
        
        # Store button bounds for click detection
        self.camera_button_bounds = (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h)
        
        # Button appearance based on recording state
        if self.is_recording:
            btn_color = COLORS["accent"]
            btn_text = "⏹ Stop"
        else:
            btn_color = "#34C759"
            btn_text = "⏺ Record"
        
        # Button background
        self.overlay_canvas.create_rectangle(btn_x, btn_y, btn_x + btn_w, btn_y + btn_h,
                                            fill=btn_color, outline="", width=0, tags="camera_button")
        # Button text
        self.overlay_canvas.create_text(btn_x + btn_w // 2, btn_y + btn_h // 2, text=btn_text,
                                       fill="#FFFFFF", font=("Arial", 20, "bold"), tags="camera_button")

    def _draw_video_overlay(self, w, h):
        # Show set time at top right if alarm is set
        if self.alarm_set_time is not None:
            self.overlay_canvas.create_text(w-30, 30, text=f"Alarm: {self.alarm_set_time}", 
                                          fill=COLORS["text"], font=("Arial", 20, "bold"), anchor="e")
        
        # Title (top-left)
        now = dt.datetime.now()
        date_str = now.strftime("%d/%m/%Y")
        self.overlay_canvas.create_text(30, 30, text=f"VIDEO : {date_str}", fill=COLORS["text"],
                                        font=("Arial", 28, "bold"), anchor="w")
        
        # Draw scrollbars - same as camera page
        scroll_top = int(h*0.25)
        scroll_bottom = int(h*0.90)
        self._draw_scrollbars(w, h, scroll_top, scroll_bottom)

        # Playback controls & scrub bar
        bar_y = int(h*0.88)
        margin = 150
        self.overlay_canvas.create_line(margin, bar_y, w - margin, bar_y, fill="#FFFFFF", width=4)
        # current time and total time
        self.overlay_canvas.create_text(margin-35, bar_y, text="6:15", fill="#FFFFFF", font=("Arial", 16), anchor="e")
        self.overlay_canvas.create_text(w - margin + 35, bar_y, text="8:34", fill="#FFFFFF", font=("Arial", 16), anchor="w")

        # scrubber circle (somewhere ~70%)
        scrub_x = margin + 0.7*(w - 2*margin)
        self.overlay_canvas.create_oval(scrub_x-10, bar_y-10, scrub_x+10, bar_y+10, fill="#FFFFFF", width=0)

        # playback icons (<<  ►  ||)
        icons_y = bar_y - 50
        icons_x = [margin, margin+60, margin+120]
        icons = ["\u23EA", "\u25B6", "\u23F8"]
        for i, x in enumerate(icons_x):
            self.overlay_canvas.create_text(x, icons_y, text=icons[i], fill="#FFFFFF", font=("Arial", 32))

    def _draw_alarm_overlay(self, w, h):
        # Show set time at top right if alarm is set
        if self.alarm_set_time is not None:
            self.overlay_canvas.create_text(w-30, 30, text=f"Alarm: {self.alarm_set_time}", 
                                          fill=COLORS["text"], font=("Arial", 20, "bold"), anchor="e")
        
        # Title (top-left)
        self.overlay_canvas.create_text(30, 30, text="ALARM", fill=COLORS["text"], font=("Arial", 28, "bold"), anchor="w")
        
        # Panel dimensions (no dark background rectangle)
        pad = 80
        panel_h = int(h*0.55)
        panel_top = int(h*0.25)
        panel_bottom = panel_top + panel_h

        # Draw scrollbars - same as camera page
        scroll_top = int(h*0.25)
        scroll_bottom = int(h*0.90)
        self._draw_scrollbars(w, h, scroll_top, scroll_bottom)

        # Two spinbox control pads (left/right) - more centered
        spinbox_w = 320
        spinbox_h = 180
        
        # Calculate center positions
        center_x = w // 2
        spacing = 100  # Space between spinboxes
        
        left_x1 = center_x - spinbox_w - spacing // 2
        left_y1 = panel_top + 90
        left_x2 = left_x1 + spinbox_w
        left_y2 = left_y1 + spinbox_h
        
        right_x1 = center_x + spacing // 2
        right_y1 = left_y1
        right_x2 = right_x1 + spinbox_w
        right_y2 = left_y2
        
        # Store spinbox positions
        self.spinbox_left = (left_x1, left_y1, left_x2, left_y2)
        self.spinbox_right = (right_x1, right_y1, right_x2, right_y2)

        for idx, (x1, y1, x2, y2) in enumerate([(left_x1, left_y1, left_x2, left_y2), (right_x1, right_y1, right_x2, right_y2)]):
            # Main spinbox background
            self.overlay_canvas.create_rectangle(x1, y1, x2, y2, fill=COLORS["overlay_light"], outline="", width=0)
            # Outer border
            self.overlay_canvas.create_rectangle(x1, y1, x2, y2, outline="#D0D0D0", width=2)
            
            # Display area (larger central area)
            display_x2 = x2 - 60
            self.overlay_canvas.create_rectangle(x1+2, y1+2, display_x2-2, y2-2, fill="#FFFFFF", outline="", width=0)
            
            # Center display value with better styling
            center_x = (x1 + display_x2) // 2
            center_y = (y1 + y2) // 2
            value = self.alarm_left_value if idx == 0 else self.alarm_right_value
            # Format as 2-digit time
            display_text = f"{value:02d}"
            # Main text
            self.overlay_canvas.create_text(center_x, center_y, text=display_text, 
                                          fill=COLORS["text_dark"], font=("Arial", 60, "bold"))
            
            # Button area on the right with gradient
            btn_x1 = display_x2
            btn_width = 60
            btn_height = (y2 - y1) // 2
            
            # Up button - with hover effect color
            up_btn_y2 = y1 + btn_height
            tag = f"spinbox_{idx}_up"
            self.overlay_canvas.create_rectangle(btn_x1, y1+2, x2-2, up_btn_y2-1, 
                                                fill="#F0F0F0", outline="", width=0, tags=tag)
            tri_cx = btn_x1 + btn_width // 2
            tri_cy = y1 + btn_height // 2
            self._draw_triangle(tri_cx, tri_cy, 15, direction="up", fill=COLORS["text_dark"])
            
            # Separator line
            self.overlay_canvas.create_line(btn_x1, up_btn_y2, x2, up_btn_y2, fill="#D0D0D0", width=2)
            
            # Down button - with hover effect color
            tag = f"spinbox_{idx}_down"
            self.overlay_canvas.create_rectangle(btn_x1, up_btn_y2+1, x2-2, y2-2, 
                                                fill="#F0F0F0", outline="", width=0, tags=tag)
            tri_cy = up_btn_y2 + btn_height // 2
            self._draw_triangle(tri_cx, tri_cy, 15, direction="down", fill=COLORS["text_dark"])

        # Labels under spinboxes
        left_center_x = (left_x1 + left_x2) // 2
        right_center_x = (right_x1 + right_x2) // 2
        label_y = left_y2 + 30
        self.overlay_canvas.create_text(left_center_x, label_y, text="HOUR", fill="#A0A0A0", font=("Arial", 16, "bold"))
        self.overlay_canvas.create_text(right_center_x, label_y, text="MINUTE", fill="#A0A0A0", font=("Arial", 16, "bold"))
        
        # Two circular indicators in the middle (colon separator) - white circles
        mid_x = w // 2
        cy = (left_y1 + left_y2) // 2
        dot_spacing = 15
        for cy_offset in [-dot_spacing, dot_spacing]:
            self.overlay_canvas.create_oval(mid_x-8, cy+cy_offset-8, mid_x+8, cy+cy_offset+8, 
                                          outline=COLORS["text"], fill=COLORS["text"], width=0)
        
        # Done button at the bottom right of the panel
        btn_w = 140
        btn_h = 50
        btn_x = w - pad - btn_w + 20
        btn_y = panel_bottom + 80
        
        # Store button bounds for click detection
        self.alarm_done_button = (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h)
        
        # Button shadow
        shadow_offset = 4
        self.overlay_canvas.create_rectangle(
            btn_x + shadow_offset, btn_y + shadow_offset, 
            btn_x + btn_w + shadow_offset, btn_y + btn_h + shadow_offset,
            fill="#00000030", outline="", width=0
        )
        
        # Button background - iOS style blue
        self.overlay_canvas.create_rectangle(btn_x, btn_y, btn_x + btn_w, btn_y + btn_h,
                                            fill=COLORS["accent_blue"], outline="", width=0, tags="done_button")
        # Inner highlight for depth
        self.overlay_canvas.create_rectangle(btn_x+2, btn_y+2, btn_x + btn_w-2, btn_y + btn_h-2,
                                            outline="#CCCCCC", width=1, tags="done_button")
        # Button text
        self.overlay_canvas.create_text(btn_x + btn_w // 2, btn_y + btn_h // 2, text="✓ Done",
                                       fill="#FFFFFF", font=("Arial", 22, "bold"), tags="done_button")

    def _draw_triangle(self, cx, cy, size, direction="up", fill="#FFFFFF"):
        if direction == "up":
            points = [cx, cy - size, cx - size*0.8, cy + size*0.8, cx + size*0.8, cy + size*0.8]
        else:
            points = [cx, cy + size, cx - size*0.8, cy - size*0.8, cx + size*0.8, cy - size*0.8]
        self.overlay_canvas.create_polygon(points, fill=fill, width=0)
    
    def _draw_scrollbars(self, w, h, scroll_top, scroll_bottom):
        """Draw consistent scrollbars on both sides of the screen."""
        scroll_height = scroll_bottom - scroll_top
        thumb_height = 50
        
        # Left brightness scrollbar
        left_x = 40
        self.left_scroll_x = left_x
        self.left_scroll_top = scroll_top
        self.left_scroll_bottom = scroll_bottom
        self.left_scroll_height = scroll_height
        
        # Track
        self.overlay_canvas.create_rectangle(left_x-4, scroll_top, left_x+4, scroll_bottom, 
                                            fill=COLORS["scrollbar_track"], outline="", width=0)
        # Thumb
        thumb_pos = scroll_top + int((scroll_height - thumb_height) * (1 - self.brightness_value/100))
        self.overlay_canvas.create_rectangle(left_x-6, thumb_pos, left_x+6, thumb_pos+thumb_height, 
                                            fill=COLORS["scrollbar_thumb"], outline="", width=0)
        # Icon
        self.overlay_canvas.create_text(left_x, scroll_top-20, text="☼", fill="#FFFFFF", font=("Arial", 18))
        
        # Right volume scrollbar
        right_x = w - 40
        self.right_scroll_x = right_x
        self.right_scroll_top = scroll_top
        self.right_scroll_bottom = scroll_bottom
        self.right_scroll_height = scroll_height
        
        # Track
        self.overlay_canvas.create_rectangle(right_x-4, scroll_top, right_x+4, scroll_bottom, 
                                            fill=COLORS["scrollbar_track"], outline="", width=0)
        # Thumb
        thumb_pos = scroll_top + int((scroll_height - thumb_height) * (1 - self.volume_value/100))
        self.overlay_canvas.create_rectangle(right_x-6, thumb_pos, right_x+6, thumb_pos+thumb_height, 
                                            fill=COLORS["scrollbar_thumb"], outline="", width=0)
        # Volume icon - use muted speaker symbol
        self.overlay_canvas.create_text(right_x, scroll_top-20, text="�", fill="#FFFFFF", font=("Arial", 18))

    # ---------------- Video update ----------------
    def _update_video(self):
        frame = None
        # Only read from camera if recording is active
        if self.is_recording and self.camera_available and self.cap is not None and self.cap.isOpened():
            try:
                ok, frame = self.cap.read()
                if not ok or frame is None or frame.size == 0:
                    frame = None
                    # Camera disconnected, mark as unavailable
                    if self.camera_available:
                        self.camera_available = False
                        print("⚠ Camera feed lost - switching to placeholder")
            except Exception as e:
                print(f"Error reading camera frame: {e}")
                frame = None
                self.camera_available = False
        
        if frame is None or not self.is_recording:
            # Fallback image
            img = self.placeholder_img.copy()
        else:
            # Verify frame has data
            if frame.size == 0 or frame.shape[0] == 0 or frame.shape[1] == 0:
                print("⚠ Received empty frame from camera")
                img = self.placeholder_img.copy()
            else:
                # Convert BGR -> RGB
                try:
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(frame_rgb)
                except Exception as e:
                    print(f"Error converting frame: {e}")
                    img = self.placeholder_img.copy()

        # Fit to widget size while preserving aspect
        w = max(self.video_frame.winfo_width(), 100)
        h = max(self.video_frame.winfo_height(), 100)
        
        try:
            img = self._letterbox(img, (w, h), COLORS["video_bg"])
            
            # Update Tk image
            self.tk_img = ImageTk.PhotoImage(img)
            self.video_label.configure(image=self.tk_img)
            
            # Draw overlays after updating the video
            self._draw_overlay(w, h)
        except Exception as e:
            print(f"Error updating video display: {e}")

        # Schedule next frame
        self.after(33, self._update_video)

    def _letterbox(self, img: Image.Image, target_size, bg_color):
        """Resize with aspect ratio preserved, pad with bg_color."""
        target_w, target_h = target_size
        img_w, img_h = img.size
        scale = min(target_w / img_w, target_h / img_h)
        new_w = max(1, int(img_w * scale))
        new_h = max(1, int(img_h * scale))
        img_resized = img.resize((new_w, new_h), Image.LANCZOS)

        canvas = Image.new("RGB", (target_w, target_h), bg_color)
        offset = ((target_w - new_w) // 2, (target_h - new_h) // 2)
        canvas.paste(img_resized, offset)
        return canvas

    def _make_placeholder(self):
        """Generate a neutral placeholder image that simulates a defocused camera."""
        w, h = 960, 540
        img = Image.new("RGB", (w, h), COLORS["video_bg"])
        draw = ImageDraw.Draw(img)
        # Add a soft gradient / vignette
        for i in range(16):
            alpha = int(180 * (i/15))
            draw.rectangle([i*5, i*5, w - i*5, h - i*5], outline=(23, 23, 23))
        # Text
        txt = "Webcam Unavailable\n(Showing placeholder)"
        font = get_font(20, True)
        bbox = draw.multiline_textbbox((0, 0), txt, font=font, spacing=6)
        wtxt, htxt = bbox[2] - bbox[0], bbox[3] - bbox[1]
        draw.multiline_text(((w-wtxt)//2, (h-htxt)//2), txt, fill="#A0A0A0", font=font, align="center", spacing=6)
        return img

    # ---------------- Time/Temp update ----------------
    def _update_time(self):
        now = dt.datetime.now()
        self.date_label.configure(text=now.strftime("%m/%d/%Y"))
        self.time_label.configure(text=now.strftime("%H:%M"))
        # Simulate temp gently oscillating
        self.temp_c = 20.0 + 0.8 * (time.time() % 60) / 60.0
        self.temp_label.configure(text=f"{self.temp_c:0.1f}°C")
        self.after(1000, self._update_time)

    # ---------------- Page switching ----------------
    def show_page(self, page_name: str):
        self.current_page = page_name
        self._style_active_button()

    def _style_active_button(self):
        # Reset all buttons to default style with subtle shadow effect
        for b in (self.btn_camera, self.btn_alarm, self.btn_video):
            b.configure(
                bg=COLORS["button_bg"], 
                fg=COLORS["text_dark"], 
                bd=0, 
                relief="flat", 
                highlightthickness=2,
                highlightbackground=COLORS["panel_bg"]
            )
        # Highlight active button with darker background and subtle border
        active = {
            "camera": self.btn_camera,
            "alarm": self.btn_alarm,
            "video": self.btn_video
        }.get(self.current_page, self.btn_camera)
        active.configure(
            bg="#FFFFFF", 
            fg=COLORS["text_dark"], 
            bd=0, 
            relief="flat",
            highlightthickness=3,
            highlightbackground=COLORS["accent_blue"]
        )

    # ---------------- Event handlers ----------------
    def _on_canvas_click(self, event):
        """Handle mouse clicks on the canvas."""
        x, y = event.x, event.y
        
        # Check camera record button (on Camera page)
        if self.current_page == "camera" and hasattr(self, 'camera_button_bounds'):
            x1, y1, x2, y2 = self.camera_button_bounds
            if x1 <= x <= x2 and y1 <= y <= y2:
                self.is_recording = not self.is_recording
                if self.is_recording:
                    print("🔴 Recording started")
                else:
                    print("⏹ Recording stopped")
                return
        
        if self.current_page == "alarm":
            # Check Done button
            if hasattr(self, 'alarm_done_button'):
                x1, y1, x2, y2 = self.alarm_done_button
                if x1 <= x <= x2 and y1 <= y <= y2:
                    # Set the alarm time
                    self.alarm_set_time = f"{self.alarm_left_value:02d}:{self.alarm_right_value:02d}"
                    print(f"✓ Alarm set to {self.alarm_set_time}")
                    return
            
            # Check spinbox buttons
            if hasattr(self, 'spinbox_left'):
                x1, y1, x2, y2 = self.spinbox_left
                btn_x1 = x2 - 50
                btn_height = (y2 - y1) // 2
                
                # Left spinbox up button (Hours: 0-23)
                if btn_x1 <= x <= x2 and y1 <= y <= y1 + btn_height:
                    self.alarm_left_value = (self.alarm_left_value + 1) % 24
                    print(f"Hour: {self.alarm_left_value:02d}")
                    return
                # Left spinbox down button
                elif btn_x1 <= x <= x2 and y1 + btn_height <= y <= y2:
                    self.alarm_left_value = (self.alarm_left_value - 1) % 24
                    print(f"Hour: {self.alarm_left_value:02d}")
                    return
            
            if hasattr(self, 'spinbox_right'):
                x1, y1, x2, y2 = self.spinbox_right
                btn_x1 = x2 - 50
                btn_height = (y2 - y1) // 2
                
                # Right spinbox up button (Minutes: 0-59)
                if btn_x1 <= x <= x2 and y1 <= y <= y1 + btn_height:
                    self.alarm_right_value = (self.alarm_right_value + 1) % 60
                    print(f"Minute: {self.alarm_right_value:02d}")
                    return
                # Right spinbox down button
                elif btn_x1 <= x <= x2 and y1 + btn_height <= y <= y2:
                    self.alarm_right_value = (self.alarm_right_value - 1) % 60
                    print(f"Minute: {self.alarm_right_value:02d}")
                    return
    
    def _on_canvas_drag(self, event):
        """Handle mouse dragging on scrollbars."""
        x, y = event.x, event.y
        
        # Check if dragging on left scrollbar
        if hasattr(self, 'left_scroll_x') and hasattr(self, 'left_scroll_top'):
            if abs(x - self.left_scroll_x) < 20:
                if self.left_scroll_top <= y <= self.left_scroll_bottom:
                    # Update brightness based on y position (inverted - top = 100%, bottom = 0%)
                    progress = (y - self.left_scroll_top) / self.left_scroll_height
                    self.brightness_value = max(0, min(100, int((1 - progress) * 100)))
                    print(f"Brightness: {self.brightness_value}%")
                    return
        
        # Check if dragging on right scrollbar
        if hasattr(self, 'right_scroll_x') and hasattr(self, 'right_scroll_top'):
            if abs(x - self.right_scroll_x) < 20:
                if self.right_scroll_top <= y <= self.right_scroll_bottom:
                    # Update volume based on y position (inverted - top = 100%, bottom = 0%)
                    progress = (y - self.right_scroll_top) / self.right_scroll_height
                    self.volume_value = max(0, min(100, int((1 - progress) * 100)))
                    print(f"Volume: {self.volume_value}%")
                    return

    # ---------------- Cleanup ----------------
    def _on_close(self):
        try:
            if self.cap is not None:
                self.cap.release()
            if cv2 is not None:
                try:
                    cv2.destroyAllWindows()
                except Exception:
                    pass
        finally:
            self.destroy()


if __name__ == "__main__":
    app = SmartPanelApp()
    app.mainloop()

