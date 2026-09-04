import random
import tkinter as tk
import ctypes
from pathlib import Path

from PIL import Image, ImageOps, ImageTk

PET_SIZE = 120
MOVE_SPEED = 2
MOVE_DELAY = 20
FRAME_DELAY = 100
BOTTOM_MARGIN = 0
TRANSPARENT_COLOR = "#211e21"
ground_y = 0

app = tk.Tk()
app.overrideredirect(True)
app.attributes("-topmost", True)
app.configure(bg=TRANSPARENT_COLOR)
app.attributes("-transparentcolor", TRANSPARENT_COLOR)

image_dir = Path(__file__).parent / "images"



def load_pair(filename, original_faces_left=True):
    image = Image.open(image_dir / filename).convert("RGBA")

    # Every pose receives exactly the same canvas size.
    image = image.resize(
        (PET_SIZE, PET_SIZE),
        Image.Resampling.LANCZOS,
    )

    mirrored = ImageOps.mirror(image)

    if original_faces_left:
        return {
            -1: ImageTk.PhotoImage(image),
            1: ImageTk.PhotoImage(mirrored),
        }

    return {
        -1: ImageTk.PhotoImage(mirrored),
        1: ImageTk.PhotoImage(image),
    }


walk_frames = [
    load_pair("walk-cycle-1.png"),
    load_pair("walk-cycle-2.png"),
    load_pair("walk-cycle-3.png"),
    load_pair("walk-cycle-4.png"),
]

happy_frames = load_pair(
    "happy.png",
    original_faces_left=False,
)

pet = tk.Label(
    app,
    bg=TRANSPARENT_COLOR,
    borderwidth=0,
    highlightthickness=0,
    padx=0,
    pady=0,
)
pet.pack()

class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


def get_work_area():
    rect = RECT()

    # SPI_GETWORKAREA returns the screen area above the taskbar.
    ctypes.windll.user32.SystemParametersInfoW(
        0x0030,
        0,
        ctypes.byref(rect),
        0,
    )

    return rect


work_area = get_work_area()

SCREEN_LEFT = work_area.left
SCREEN_RIGHT = work_area.right
TASKBAR_TOP = work_area.bottom

# In the original 300×300 sprites, the paws were aligned at y=255.
# Convert that baseline to the current PET_SIZE.
SPRITE_BASELINE = round(255 * PET_SIZE / 300)

x = SCREEN_LEFT + 20

# Place the paws directly on the taskbar's upper edge.
ground_y = TASKBAR_TOP - SPRITE_BASELINE


direction = 1
frame_index = 0
happy = False


def show_current_frame():
    if happy:
        pet.configure(image=happy_frames[direction])
    else:
        pet.configure(image=walk_frames[frame_index][direction])


def move_pet():
    global x, direction

    x += MOVE_SPEED * direction

    if x >= SCREEN_RIGHT - PET_SIZE:
        x = SCREEN_RIGHT - PET_SIZE
        direction = -1
        show_current_frame()

    elif x <= SCREEN_LEFT:
        x = SCREEN_LEFT
        direction = 1
        show_current_frame()

    app.geometry(f"{PET_SIZE}x{PET_SIZE}+{x}+{ground_y}")
    app.after(MOVE_DELAY, move_pet)


def animate_pet():
    global frame_index
    if not happy:
        frame_index = (frame_index + 1) % len(walk_frames)
        show_current_frame()
    app.after(FRAME_DELAY, animate_pet)


def pet_clicked(_event):
    global happy

    app.focus_force()

    happy = True
    show_current_frame()
    app.after(700, finish_reaction)


def finish_reaction():
    global happy
    happy = False
    show_current_frame()


def drag_pet(event):
    global x

    x = event.x_root - PET_SIZE // 2
    x = max(
        SCREEN_LEFT,
        min(x, SCREEN_RIGHT - PET_SIZE),
    )

    app.geometry(
        f"{PET_SIZE}x{PET_SIZE}+{x}+{ground_y}"
    )

def close_pet(_event=None):
    app.destroy()


pet.bind("<Button-1>", pet_clicked)
pet.bind("<B3-Motion>", drag_pet)
app.bind_all("<Escape>", close_pet)

# Give the borderless window keyboard focus after it appears.
app.after(200, lambda: (app.lift(), app.focus_force()))

# Reliable backup: double-right-click the kitty to close.
pet.bind("<Double-Button-3>", close_pet)

show_current_frame()
move_pet()
animate_pet()
app.mainloop()
