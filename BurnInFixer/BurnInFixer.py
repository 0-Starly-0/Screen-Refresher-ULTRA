import easykinter as ek
import time, screen_brightness_control as sbc, sys, os
from typing import Literal as lit

import tkinter as tk
from tkinter import ttk

if getattr(sys, 'frozen', False):
    os.add_dll_directory(sys._MEIPASS)

# Setting Global Variables
root = ek.CreateRoot(HideWindow=True)

# Screen Dimensions
ScreenX = root.winfo_screenwidth()
ScreenY = root.winfo_screenheight()

# Icon Images
FixerIcon = ek.BetterPhotoImage("FixerIcon.png")
MainIcon = ek.BetterPhotoImage("MainIcon.png")


# Making the Customized ScrollBar
class ScrollableFrame(ttk.Frame):
    _active_frame = None
    _bound_roots = set()

    def __init__(self, container, orient="vertical", *args, **kwargs):
        super().__init__(container, *args, **kwargs)
        self.orient = orient.lower()
        
        if self.orient not in ("vertical", "horizontal"):
            raise ValueError("orient must be 'vertical' or 'horizontal'")

        toplevel = self.winfo_toplevel()
        if toplevel not in ScrollableFrame._bound_roots:
            toplevel.bind_all("<MouseWheel>", ScrollableFrame._global_mouse_wheel)
            toplevel.bind_all("<Button-4>", ScrollableFrame._global_mouse_wheel)
            toplevel.bind_all("<Button-5>", ScrollableFrame._global_mouse_wheel)
            ScrollableFrame._bound_roots.add(toplevel)

        self.canvas = tk.Canvas(self, borderwidth=0, highlightthickness=0)
        
        if self.orient == "vertical":
            self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.canvas.configure(yscrollcommand=self.scrollbar.set)
            self.scrollbar.pack(side="right", fill="y")
            self.canvas.pack(side="left", fill="both", expand=True)
        else:
            self.scrollbar = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
            self.canvas.configure(xscrollcommand=self.scrollbar.set)
            self.scrollbar.pack(side="bottom", fill="x")
            self.canvas.pack(side="top", fill="both", expand=True)

        self.scrollable_inner_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_inner_frame, anchor="nw")

        self.scrollable_inner_frame.bind("<Configure>", self._on_frame_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        for widget in (self.canvas, self.scrollable_inner_frame):
            widget.bind("<Enter>", lambda e, f=self: f._set_active())
            widget.bind("<Leave>", lambda e, f=self: f._clear_active())

    def _set_active(self):
        ScrollableFrame._active_frame = self

    def _clear_active(self):
        if ScrollableFrame._active_frame == self:
            ScrollableFrame._active_frame = None

    @classmethod
    def _global_mouse_wheel(cls, event):
        if cls._active_frame and hasattr(cls._active_frame, '_handle_scroll'):
            cls._active_frame._handle_scroll(event)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        if self.orient == "vertical":
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        else:
            self.canvas.itemconfig(self.canvas_window, height=event.height)

    def _handle_scroll(self, event):
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            if not event.delta:
                return
            delta = int(-1 * (event.delta / 120))

        if self.orient == "vertical":
            self.canvas.yview_scroll(delta, "units")
        else:
            self.canvas.xview_scroll(delta, "units")


# Making self.Main Script
class ScreenRefresher:
    def __init__(self):

        # Initializing self.Main variables
        self.Time = 0
        self.DefaultBrightness = sbc.get_brightness()
        self.FixBrightness = 100
        self.ColorDelay = 0
        self.Colors = []
        self.CurrentColor = 0
        self.FixID = None

        # Main Window
        self.Main = ek.CreateToplevel("Screen Refresher ULTRA", root, None, 500, 500)
        self.Main.iconphoto(False, MainIcon)
        ek.BetterConfigure(self.Main, None, False, False, False, lambda:root.destroy(), None, False, True)
        self.Main.bind("<Button-1>", lambda event: event.widget.focus_set())
        ek.CenterWindow(self.Main)

        # Window Contents
        self.TitleLabel = ek.CreateLabel(self.Main, "Screen Refresher - ULTRA\nWhen Fullscreen, click anywhere to stop.\nWhen Windowed, close the window to stop.", "Monaco", 15, "Italic", PackType="Place", RelX=0.5, RelY=0.08)
        self.DiagLabel = ek.CreateLabel(self.Main, "Diagnostic - Find dead pixels:", "Arial", 14, "Bold", PackType="Place", RelX=0.5, RelY=0.18)
        self.SettingsLabel = ek.CreateLabel(self.Main, "Settings - Configure for both diagnostic and fix:", "Arial", 14, "Bold", PackType="Place", RelX=0.5, RelY=0.35)
        self.RunLabel = ek.CreateLabel(self.Main, "Fixer Tool - Click to toggle colors that will appear:", "Arial", 14, "Bold", PackType="Place", RelX=0.5, RelY=0.725)

        self.WindowModeLabel = ek.CreateLabel(self.Main, "Window mode:", "Arial", 13, PackType="Place", RelX=0.385, RelY=0.42)
        self.TimerLabel = ek.CreateLabel(self.Main, "Run for (Timer):", "Arial", 13, PackType="Place", RelX=0.135, RelY=0.48)
        self.HourLabel = ek.CreateLabel(self.Main, "Hours", "Arial", 13, PackType="Place", RelX=0.420, RelY=0.485)
        self.MinuteLabel = ek.CreateLabel(self.Main, "Minutes", "Arial", 13, PackType="Place", RelX=0.665, RelY=0.485)
        self.SecondLabel = ek.CreateLabel(self.Main, "Seconds", "Arial", 13, PackType="Place", RelX=0.895, RelY=0.485)
        self.BrightnessLabel = ek.CreateLabel(self.Main, "Brightness (When fixing):", "Arial", 13, PackType="Place", RelX=0.45, RelY=0.55)
        self.DelayLabel = ek.CreateLabel(self.Main, "Delay between colors (seconds):", "Arial", 13, PackType="Place", RelX=0.45, RelY=0.62)

        self.DiagBlack = ek.CreateButton(self.Main, "Black", None, "center", ButtonHeight=25, ButtonWidth=80, optionalCustomization="Bold", FgColor="black", CommandFunc=lambda:self.StartDiagnostic("black"), PackType="Place", RelX=0.1, RelY=0.25)
        self.DiagWhite = ek.CreateButton(self.Main, "White", None, "center", ButtonHeight=25, ButtonWidth=80, optionalCustomization="Bold", FgColor="gray", CommandFunc=lambda:self.StartDiagnostic("white"), PackType="Place", RelX=0.3, RelY=0.25)
        self.DiagRed = ek.CreateButton(self.Main, "Red", None, "center", ButtonHeight=25, ButtonWidth=80, optionalCustomization="Bold", FgColor="red", CommandFunc=lambda:self.StartDiagnostic("red"), PackType="Place", RelX=0.5, RelY=0.25)
        self.DiagBlue = ek.CreateButton(self.Main, "Green", None, "center", ButtonHeight=25, ButtonWidth=80, optionalCustomization="Bold", FgColor="green", CommandFunc=lambda:self.StartDiagnostic("green"), PackType="Place", RelX=0.7, RelY=0.25)
        self.DiagGreen = ek.CreateButton(self.Main, "Blue", None, "center", ButtonHeight=25, ButtonWidth=80, optionalCustomization="Bold", FgColor="blue", CommandFunc=lambda:self.StartDiagnostic("blue"), PackType="Place", RelX=0.9, RelY=0.25)

        self.SelecBlack = ek.CreateButton(self.Main, "Black", None, "center", ButtonHeight=25, ButtonWidth=80, optionalCustomization="Bold", FgColor="black", CommandFunc=lambda:self.ToggleColors("black"), PackType="Place", RelX=0.1, RelY=0.8)
        self.SelecWhite = ek.CreateButton(self.Main, "White", None, "center", ButtonHeight=25, ButtonWidth=80, optionalCustomization="Bold", FgColor="gray", CommandFunc=lambda:self.ToggleColors("white"), PackType="Place", RelX=0.3, RelY=0.8)
        self.SelecRed = ek.CreateButton(self.Main, "Red", None, "center", ButtonHeight=25, ButtonWidth=80, optionalCustomization="Bold", FgColor="red", CommandFunc=lambda:self.ToggleColors("red"), PackType="Place", RelX=0.5, RelY=0.8)
        self.SelecGreen = ek.CreateButton(self.Main, "Green", None, "center", ButtonHeight=25, ButtonWidth=80, optionalCustomization="Bold", FgColor="green", CommandFunc=lambda:self.ToggleColors("green"), PackType="Place", RelX=0.7, RelY=0.8)
        self.SelecBlue = ek.CreateButton(self.Main, "Blue", None, "center", ButtonHeight=25, ButtonWidth=80, optionalCustomization="Bold", FgColor="blue", CommandFunc=lambda:self.ToggleColors("blue"), PackType="Place", RelX=0.9, RelY=0.8)

        self.StartButton = ek.CreateButton(self.Main, "Start Fix", None, "center", ButtonHeight=45, ButtonWidth=150, FontSize=20, optionalCustomization="Bold", FgColor="black", CommandFunc=lambda:self.ManagerFunc(), PackType="Place", RelX=0.5, RelY=0.91)

        self.HourEntry = ek.CreateEntry(self.Main, None, None, True, "000", "Gray", 4, "Arial", 12, PackType="Place", RelX=0.325, RelY=0.485)
        self.MinuteEntry = ek.CreateEntry(self.Main, None, None, True, "000", "Gray", 4, "Arial", 12, PackType="Place", RelX=0.555, RelY=0.485)
        self.SecondEntry = ek.CreateEntry(self.Main, None, None, True, "000", "Gray", 4, "Arial", 12, PackType="Place", RelX=0.785, RelY=0.485)
        self.BrightnessEntry = ek.CreateEntry(self.Main, None, None, True, "100", "Gray", 3, "Arial", 12, PackType="Place", RelX=0.675, RelY=0.55)
        self.DelayEntry = ek.CreateEntry(self.Main, None, None, True, "1", "Gray", 3, "Arial", 12, PackType="Place", RelX=0.735, RelY=0.62)

        # I hate these mf's
        self.WindowStyle = tk.StringVar(self.Main)
        self.WindowStyle.set("Fullscreen")
        options = ["Fullscreen", "Windowed"]

        # Like seriously be normal for once
        self.Dropdown = tk.OptionMenu(self.Main, self.WindowStyle, *options)
        self.Dropdown.place(relx=0.63, rely=0.42, anchor="center")

        # Fixer Window
        self.Fixer = ek.CreateToplevel("Fixer/Diagnostic window", root, None, ScreenX, ScreenY)
        self.Fixer.iconphoto(False, FixerIcon)
        self.Fixer.config(cursor="none")
        self.Fixer.withdraw()
        ek.BetterConfigure(self.Fixer, None, True, False, False, lambda:None, 1, True, False)
        ek.BetterBind(self.Fixer, "Button-1", self.EndDiagnostic)

        # Vertical
        """
        vertical_frame = ScrollableFrame(self.Main, orient="vertical")
        vertical_frame.place(x=30, y=50, width=150, height=200)

        for i in range(20):
            ttk.Label(vertical_frame.scrollable_inner_frame, text=f"Item {i}").pack(anchor="w", padx=5, pady=2)
        """

        # Horizontal
        """
        horizontal_frame = ScrollableFrame(self.Main, orient="horizontal")
        horizontal_frame.place(x=220, y=50, width=220, height=150)

        for i in range(10):
            btn = ttk.Button(horizontal_frame.scrollable_inner_frame, text=f"Btn {i}", width=10)
            btn.pack(side="left", padx=5, pady=5)
        """

    def ToggleColors(self, WhichColor:lit["blue", "red", "green", "white", "black"]="white"):
        if WhichColor in self.Colors:
            match WhichColor:
                case "black":
                    self.SelecBlack.config(bg="#F0F0F0")
                case "white":
                    self.SelecWhite.config(bg="#F0F0F0")
                case "red":
                    self.SelecRed.config(bg="#F0F0F0")
                case "blue":
                    self.SelecBlue.config(bg="#F0F0F0")
                case "green":
                    self.SelecGreen.config(bg="#F0F0F0")
            self.Colors.remove(WhichColor)

        else:
            match WhichColor:
                case "black":
                    self.SelecBlack.config(bg="lightgreen")
                case "white":
                    self.SelecWhite.config(bg="lightgreen")
                case "red":
                    self.SelecRed.config(bg="lightgreen")
                case "blue":
                    self.SelecBlue.config(bg="lightgreen")
                case "green":
                    self.SelecGreen.config(bg="lightgreen")
            self.Colors.append(WhichColor)


    def TimerConfig(self):

        try:
            Seconds = int(self.SecondEntry.get())
            Minutes = int(self.MinuteEntry.get()) * 60
            Hours = int(self.HourEntry.get()) * 3600
        
        except Exception:
            Seconds = 0
            Minutes = 0
            Hours = 0

        self.Time = ( (Hours) + (Minutes) + (Seconds) )

        try:
            self.FixBrightness = int(self.BrightnessEntry.get())

        except Exception:
            self.FixBrightness = 100

        try:
            self.ColorDelay = int(self.DelayEntry.get()) * 1000
    
        except Exception:
            self.ColorDelay = 1000

        root.after( (self.Time * 1000), lambda:root.after_cancel(self.FixID) )
        root.after( (self.Time * 1000), self.EndDiagnostic )


    def ManagerFunc(self):
        if bool(self.Colors) == True:
        
            if self.WindowStyle.get() == "Windowed":
                self.Fixer.geometry("250x250")
                self.Fixer.overrideredirect(False)
                ek.BetterConfigure(self.Fixer, ResizableHeight=True, ResizableWidth=True)
                self.Fixer.protocol("WM_DELETE_WINDOW", self.EndDiagnostic)
                self.Fixer.unbind("<Button-1>")
            else:
                self.Fixer.overrideredirect(True)
                self.Fixer.geometry(f"{ScreenX}x{ScreenY}")
                ek.BetterConfigure(self.Fixer, ResizableHeight=False, ResizableWidth=False)
                ek.BetterBind(self.Fixer, "Button-1", self.EndDiagnostic)

            self.Fixer.deiconify()
            ek.CenterWindow(self.Fixer)

            sbc.set_brightness(self.FixBrightness)

            if self.FixID is not None:
                root.after_cancel(self.FixID)

            self.TimerConfig()
            self.StartFix()


    def StartFix(self):
        self.CurrentColor += 1
        if self.CurrentColor >= len(self.Colors):
            self.CurrentColor = 0

        self.Fixer.configure(bg=self.Colors[self.CurrentColor])
        self.FixID = root.after(self.ColorDelay, self.StartFix)

    def StartDiagnostic(self, WhichColor:lit["blue", "red", "green", "white", "black"]="white"):
        if self.WindowStyle.get() == "Windowed":
            self.Fixer.geometry("250x250")
            self.Fixer.overrideredirect(False)
            ek.BetterConfigure(self.Fixer, ResizableHeight=True, ResizableWidth=True)
            self.Fixer.protocol("WM_DELETE_WINDOW", self.EndDiagnostic)
            self.Fixer.unbind("<Button-1>")
        else:
            self.Fixer.overrideredirect(True)
            self.Fixer.geometry(f"{ScreenX}x{ScreenY}")
            ek.BetterConfigure(self.Fixer, ResizableHeight=False, ResizableWidth=False)
            ek.BetterBind(self.Fixer, "Button-1", self.EndDiagnostic)

        self.Fixer.deiconify()
        ek.CenterWindow(self.Fixer)
        sbc.set_brightness(self.FixBrightness)

        self.Fixer.config(bg=WhichColor)
        self.Fixer.geometry("+0+0")
        self.Fixer.lift()

    def EndDiagnostic(self):
        if self.FixID is not None:
            root.after_cancel(self.FixID)

        sbc.set_brightness(self.DefaultBrightness)
        self.Fixer.withdraw()
        


ScreenRefresher()
