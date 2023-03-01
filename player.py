#!/usr/bin/env python3
from tkinter import (
    Tk, Menu, Frame, Label, Button, Scale, font, simpledialog, Text, Scrollbar,
    BOTH, Entry, DISABLED, END, HORIZONTAL, VERTICAL, StringVar, X, filedialog, Toplevel
)
from tkinter.ttk import Combobox, Scrollbar
from vlc import Instance as vlc
from yt_dlp import YoutubeDL
from datetime import timedelta, datetime
from requests import get as request
from urllib.parse import quote_plus, unquote
import os, psutil
from bs4 import BeautifulSoup
from json import load, dump, loads
from requests_html import HTMLSession
from time import sleep
from random import randint


QUAL_LIST = ["least_audio",
            "best_audio",
            "144p",
            "240p",
            "360p",
            "480p",
            "720p",
            "1080p",
            "1440p",
            "2160p"]
if datetime.now().hour > 18: 
    day = f"{datetime.now().day:02d}" 
else:
    day = f"{(datetime.now()- timedelta(days=1)).day:02d}" 

month = f"{datetime.now().month:02d}"
year = str(datetime.now().year)[-2:]

print(day)

class Gui:

    def __init__(self, argument='--no-xlib -q > /dev/null 2>&1'):
        self.win = Tk()
        self.superframe = Frame(self.win, bg="black")
        self.superframe.pack(side="left", anchor="ne", fill="both", expand=True)
        self.model = Model(argument)
        self.win.protocol('WM_DELETE_WINDOW', self.quit)
        self.win.title("Multimedia Interface")
        self.defaultbg = self.win.cget('bg')
        self.win.config(bg="black")
        self.fullscreen = 0
        self.default_font = font.nametofont("TkDefaultFont")
        self.light_yellow = "#ffff80"
        self.pastel_blue = "#AEC6CF"
        self.dark_pastel_blue = "#88AED0"
        self.very_light_blue = "#D5FFFF"
        self.toolframe = Frame(self.superframe, bg=self.very_light_blue)
        self.toolframe.pack(side="top", fill=X, expand=True, anchor="n")
        self.toolframe.bind('<space>', self.toggle_pause)
        self.toolframe.grid_columnconfigure(0, weight=1)
        self.toolframe.grid_columnconfigure(1, weight=0)
        self.toolframe.grid_rowconfigure(0, weight=1)
        self.toolframe.grid_rowconfigure(1, weight=1)
        self.toolframe.grid_rowconfigure(2, weight=1)
        self.toolframe.grid_rowconfigure(3, weight=1)
        self.toolframe.grid_rowconfigure(4, weight=1)
        searchframe = Frame(self.toolframe)
        searchframe.grid(row=0, column=0, sticky="ew", padx=5, pady=1)
        self.playerlist = Combobox(searchframe, state="readonly")
        self.playerlist['values'] = ["Youtube", "Vimeo", "Dailymotion", "Odysee", "Archive", "Google"]
        width = 0
        for item in self.playerlist['values']:
            if len(item) > width:
                width = len(item)
        self.playerlist.config(width=width)
        self.playerlist.set("Youtube")
        self.playerlist.bind(
            "<<ComboboxSelected>>", lambda e: self.model.set_player(
                self.playerlist.get()))
        self.playerlist.pack(side="right")
        self.searchentry = Entry(searchframe)
        self.searchentry.pack(
            side="left", fill="both", expand=True, anchor="e")
        self.searchentry.focus_set()
        self.searchentry.bind('<Return>', self.collect)
        self.searchentry.bind(
            '<Control-a>', lambda x: self.searchentry.selection_range(
                0, 'end') or "break")
        self.playframe = Frame(self.toolframe, bg=self.very_light_blue)
        self.playframe.grid(row=1, column=0, sticky="ew", padx=5)
        self.playlistframe = Frame(self.toolframe, bg=self.very_light_blue)
        self.playlistframe.grid(row=2, column=0, sticky="ew", padx=5)
        self.volumeframe = Frame(self.toolframe, bg="yellow")
        self.volumeframe.grid(row=0, column=1, rowspan=4, sticky="sne")
        self.videoframe = Frame(self.superframe, bg="black")
        self.videoframe.pack(side="top", fill="both", anchor="n")
        self.videoframe.pack_propagate(0)
        self.videodisplay = Frame(self.videoframe, bg="black")

        self.text_widget_frame = Frame(self.videoframe)
        self.text_tool_frame = Frame(self.text_widget_frame, bg="green")
        self.text_tool_frame.pack(side="top", fill="x")
        self.close_label = Label(self.text_tool_frame, text="hide")
        self.close_label.bind("<Button-1>",self.hide_text_widtget)
        self.close_label.pack(side="left", anchor="n")
        self.render_label = Label(self.text_tool_frame, text="try rendering javascript")
        self.render_label.bind("<Button-1>",self.render_js)
        self.render_label.pack(side="left", anchor="n")
        self.h_box = Combobox(self.text_tool_frame, state="readonly")
        self.h_box.set("Headers")
        self.h_box.pack(side="left", anchor="n")
        self.h_box.bind(
            "<<ComboboxSelected>>", self.jump)
        self.text_widget = Text(self.text_widget_frame, wrap="word", fg="black", bg="white")
        self.text_scrollbar = Scrollbar(self.text_widget_frame, orient = 'vertical', command=self.text_widget.yview)
        self.text_widget['yscrollcommand'] = self.text_scrollbar.set
        self.text_scrollbar.pack(side="right", fill="y")
        self.text_widget.pack(side="top", fill="both", expand=True)
        
        self.timeframe = Frame(self.videoframe, bg=self.light_yellow)
        self.videodisplay.place(relwidth=1, relheight=1)
        self.videodisplay.bind('<Motion>', self.show)
        self.videodisplay.bind('<Escape>', self.toggle_FullScreen)
        self.videodisplay.bind('<Double-Button-1>', self.toggle_FullScreen)
        self.videodisplay.bind('<Button-1>', self.prepause1)
        self.videodisplay.bind('<Left>', lambda event: self.skip(-10000))
        self.videodisplay.bind('<Right>', lambda event: self.skip(10000))
        self.videodisplay.bind('<Up>', lambda event: self.change_volume(5))
        self.videodisplay.bind('<Down>', lambda event: self.change_volume(-5))
        self.videodisplay.bind('<minus>', lambda event: self.set_speed(-10))
        self.videodisplay.bind('<plus>', lambda event: self.set_speed(+10))
        self.videodisplay.bind('r', lambda event: self.preload2(-1))
        self.videodisplay.bind('1', lambda event: self.preload2(-2))
        self.videodisplay.bind('2', lambda event: self.preload2(0))
        self.videodisplay.bind('<space>', self.toggle_pause)
        
        self.removebutton = Button(
            self.playlistframe,
            text="Remove", command=self.remove).pack(side='right')
        Button(
            self.playlistframe,
            text="OK", command=self.preload2).pack(side='right')
        self.playlist = Combobox(self.playlistframe, state="readonly")
        self.playlist.set("Playlist Is Empty")
        self.playlist.bind(
            "<<ComboboxSelected>>", lambda e: self.videodisplay.focus())
        self.playlist.pack(fill='both', expand=True, pady=1)

        self.playingentry = Entry(
            self.toolframe, disabledbackground=self.dark_pastel_blue, disabledforeground="black", font=f"{self.default_font} 14")
        self.playingentry.grid(row=3,column=0, columnspan=1,sticky="ew")
        self.playingentry.config(state=DISABLED)
        self.pausebutton = Button(
            self.timeframe,
            text="▶", command=self.toggle_pause)
        self.pausebutton.pack(side='left')

        self.timescale = Scale(
            self.timeframe, from_=0, to=1000,
            orient=HORIZONTAL, length=267,
            showvalue=0, command=self.timescale_move)
        self.timescale.pack(fill=X)
        self.timelabel = Label(
            self.timeframe, text="0:00:00 / 0:00:00", bg=self.light_yellow, font=f"{self.default_font} 6", pady=0)
        self.timelabel.pack(side='top')
        self.volumescale = Scale(
            self.volumeframe, from_=200, to=0, orient=VERTICAL,
            showvalue=0, command=self.model.change_volume)
        self.volumescale.set(100)
        self.volumescale.pack(side='left', fill=BOTH)
        self.menubar = Menu(self.win)
        self.quality_menu = Menu(self.menubar, tearoff=0)
        self.inventory_menu = Menu(self.menubar, tearoff=0)
        self.option_menu = Menu(self.menubar, tearoff=0)
        self.pref_quality_menu = Menu(self.quality_menu, tearoff=0)
        self.cur_quality_menu = Menu(self.quality_menu, tearoff=0)
        self.speed_menu = Menu(self.option_menu, tearoff=0)
        self.inventory_menu.add_command(
                    label="All Results To Playlist",
                    command=self.all_results_to_playlist)
        self.ext_playlist_menu = Menu(self.inventory_menu, tearoff=0)
        self.inventory_menu.add_command(
                    label="Clear Playlist",
                    command=self.clear_playlist)
        self.menubar.add_cascade(
            label="Playlists", menu=self.inventory_menu)
        ext_playlists = self.model.read_dict()
        self.inventory_menu.add_command(
            label="Save Playlist", command=self.save_playlist)
        self.inventory_menu.add_command(
            label="Change Playlist Name", command=self.change_title)
        self.inventory_menu.add_command(
            label="Update Playlist", command=self.update_playlist)
        self.inventory_menu.add_command(
            label="Delete Playlist", command=self.delete_playlist)
        for item in ext_playlists:
            self.ext_playlist_menu.add_command(
                    label=item, command=(
                        lambda item=item: self.choose_playlist(item)))
        self.inventory_menu.add_cascade(
            label="Saved Playlists", menu=self.ext_playlist_menu)
        self.menubar.add_cascade(
            label="Quality", menu=self.quality_menu)
        self.menubar.add_cascade(
            label="Options", menu=self.option_menu)
        for speed in range(-20, 30, 10):
            if speed > 0:
                self.speed_menu.add_command(
                    label=f"+{speed}%",
                    command=(lambda speed=speed: self.set_speed(speed)))
            elif speed < 0:
                self.speed_menu.add_command(
                    label=f"{speed}%",
                    command=(lambda speed=speed: self.set_speed(speed)))
        for quality in QUAL_LIST:
            self.quality_menu.add_command(
                label=quality, command=(
                    lambda quality=quality: self.set_prefered_quality(quality)))
        self.quality_menu.entryconfig(self.model.pref_qual, foreground='grey')
        self.option_menu.add_cascade(
            label="Playback Speed", menu=self.speed_menu)
        self.subs = Menu(self.option_menu, tearoff=0)
        self.option_menu.add_cascade(
            label="Subtitles", menu=self.subs)
        self.subs.add_command(
                label="Add Subtitles", command=self.addsubs)
        self.subs.add_command(
                label="Remove Subtitles", command=self.removesubs)
        self.instances = Menu(self.option_menu, tearoff=0)
        self.playlist_items = list()
        self.option_menu.add_cascade(
            label="New Window", menu=self.instances)
        self.instances.add_command(
                label="Extra Window (Flipped)", command=(lambda:self.make_gui(
                    '--no-xlib --quiet --video-filter=transform --transform-type=hflip')))
        self.instances.add_command(
                label="Extra Window (Normal)", command=(lambda:self.make_gui(
                    '--no-xlib -q > /dev/null 2>&1')))
        self.option_menu.add_command(
                label="Set Time", command=self.set_custom_time)
        self.option_menu.add_command(
                label="Download", command=self.download)
        self.option_menu.add_command(
                label="Toggle Autoplay", command=self.toggle_autoplay)
        self.option_menu.add_command(
                label="Filter Results", command=self.filter)
        self.option_menu.add_command(
                label="Open URL", command=self.url)
        self.option_menu.add_command(
                label="Set Track", command=self.set_audio_track)
        self.option_menu.add_command(
                label="Set Subtitles", command=self.set_sub_track)
        self.option_menu.add_command(
                label="Set Subtitles Delay", command=self.set_sub_delay)
        self.option_menu.add_command(
                label="Fullscreeen", command=(lambda: self.toggle_FullScreen("x")))
        self.option_menu.add_command(
                label="ZDF Heute", command=(lambda: self.play_by_url(f"https://nrodlzdf-a.akamaihd.net/none/zdf/{year}/{month}/{year}{month}{day}_1900_sendung_h19/1/{year}{month}{day}_1900_sendung_h19_2128k_p18v17.webm")))
        self.win.config(menu=self.menubar)
        self.sideframe = Frame(self.win, width=50,  bg="black" )
        self.sideframe.pack(side="right", anchor="n", fill="y")
        self.selected_song = False
        self.search_results = Text(self.sideframe, width=50, bg=self.light_yellow)
        self.play_results = Text(self.sideframe,width=50,  bg=self.light_yellow)
        self.search_scrollbar = Scrollbar(self.sideframe, orient = 'vertical', command=self.search_results.yview)
        self.play_results['yscrollcommand'] = self.search_scrollbar.set
        self.search_results['yscrollcommand'] = self.search_scrollbar.set
        self.expand = Label(self.sideframe, text="→ shrink", cursor="hand2", bg="black", fg="white", anchor="w", justify="left" )
        self.expand.bind('<Button-1>', self.shrink)
        self.playshow = Label(self.sideframe, text="show/hide playlist", cursor="hand2", bg="black", fg="white",  anchor="w", justify="left" )
        self.playshow.bind('<Button-1>', self.toggle_playlist)
        self.expand.grid(column=0, row=0, columnspan=2, sticky='ew')
        self.playshow.grid(column=0, row=1, columnspan=2, sticky='ew')
        
        for x in [self.search_results, self.play_results]:
            x.insert("end",'\n')
            x.insert("end",'\n')
            x.config(state="disable")
        self.search_results.grid(column=0, row=2, sticky='nsew')
        self.search_scrollbar.grid(column=1, row=2, sticky='ns')
        self.sideframe.grid_columnconfigure(0, weight=1)
        self.sideframe.grid_columnconfigure(1, weight=0)
        self.sideframe.grid_rowconfigure(0, weight=0)
        self.sideframe.grid_rowconfigure(1, weight=0)
        self.sideframe.grid_rowconfigure(2, weight=1)
        self.win.update_idletasks()
        height = 2 * self.win.winfo_height()
        self.win.minsize(0, self.win.winfo_height())
        self.winwidth = self.win.winfo_width()
        self.winwidth = 2 * self.winwidth
        self.win.geometry(f"{self.winwidth}x{height}")
        self.inventory = list()
        self.item = {}
        self.show_playframe = False
        self.templabel = Label(self.videoframe)
        self.hidden = 0
        self.func = []
        self.show()
        self.model.player.set_xwindow(self.videodisplay.winfo_id())
        self.win.update_idletasks()
        self.videoframe.config(height=self.superframe.winfo_height()-self.toolframe.winfo_height(), width=self.superframe.winfo_width())
        self.counter = 0

        self.model.player.audio_set_volume(100)
        self.preloadflag = 0
        self.autoplay = 1
        self.playlist_title = str()
        self.selected_widget = False
        self.speed = 100
        self.timeloop()
        self.win.mainloop()

    def set_sub_delay(self):
        amount = int(simpledialog.askstring("Input", "Subtitle Delay in Milliseconds"))
        self.model.player.video_set_spu_delay(amount)

    def set_sub_track(self):
        subtitle = self.model.player.video_get_spu_description()
        print(subtitle)
        track = self.model.player.video_get_spu()
        self.model.player.video_set_spu(int(track)+1)

    def set_audio_track(self):
        print(self.model.player.audio_get_track_description())
        print(self.item["best_audio"])

    def url(self):
        url = simpledialog.askstring("Input", "Url")
        self.play_by_url(url)
    
    def play_by_url(self, url):
        print(url)
        self.item = {"240p":url,
        "url": url
        }
        self.play()

    def shrink(self, event):
        if self.expand.cget("text") == "→ shrink":
            self.expand.config(text="← expand", width=10)
            self.search_results.config(width=10)
            self.play_results.config(width=10)
        else:
            self.expand.config(text="→ shrink", width=50)
            self.search_results.config(width=50)
            self.play_results.config(width=50)

    def toggle_playlist(self, event):
        self.show_playframe = not(self.show_playframe)
        if self.show_playframe:
            self.play_results.grid(column=0, row=2, sticky='nsew')
            self.update_playframe()
            self.search_scrollbar.config(command = self.play_results.yview)
        else:
            self.play_results.grid_forget()
            self.search_scrollbar.config(command = self.search_results.yview)


    def toggle_autoplay(self):
        self.autoplay = not self.autoplay


    def save_playlist(self):
        if len(self.model.playlist) > 0:
            title = simpledialog.askstring("Input", "Name For Playlist:")
            if len(title) > 0:
                self.playlist_title = title
                self.win.title(self.playlist_title)
                self.model.generate_dict(title, self.model.playlist)
                self.ext_playlist_menu.add_command(
                            label=title, command =(
                                lambda item=title: self.choose_playlist(item)))
    def filter(self):
        title = simpledialog.askstring("Input", "Only Show Results With:")
        self.query_results['values'] = []
        templist = []
        for item in list(self.inventory.keys()):
            if title in item:
                templist.append(item)
        self.query_results['values'] = templist
        self.query_results.current(0)


    def choose_playlist(self, playlist):
        self.playlist_title = playlist
        self.win.title(self.playlist_title)
        self.model.playlist = self.model.get_playlist(playlist)
        self.playlist['values'] = list(self.model.playlist.keys())
        self.playlist.current(0)
        self.update_playframe()

    def change_title(self):
        if self.playlist_title != "":
            new_title = simpledialog.askstring("Input", "New Name For Playlist:")
            if len(new_title) > 0:
                self.ext_playlist_menu.entryconfigure(self.playlist_title, label=new_title)
                self.model.change_title(self.playlist_title, new_title)

    def update_playlist(self):
        if self.playlist_title != "" and len(self.model.playlist) > 0:
            self.model.update_playlist(self.playlist_title, self.model.playlist)

    def delete_playlist(self):
        for x in range(0,10):
            print(self.model.media.get_meta(x))
        if self.playlist_title != "":
            self.model.delete_playlist(self.playlist_title)
            self.ext_playlist_menu.delete(self.playlist_title)
            self.playlist_title = ""

    def all_results_to_playlist(self):
        if len(self.inventory) > 0:
            self.model.playlist = self.inventory
            self.playlist['values'] = list(self.model.playlist.keys())
            self.playlist.current(0)
            self.update_playframe()

    def clear_playlist(self):
        self.model.playlist = {}
        self.playlist['values'] = []
        self.playlist.set('')
        self.update_playframe()

    def remove(self):
        if len(self.model.playlist) > 0:
            index = self.playlist.get()
            place = self.playlist.current()
            if place > -1:
                del self.model.playlist[index]
                self.playlist['values'] = list(self.model.playlist.keys())
            if place > 0:
                self.playlist.current(place-1)
            elif len(self.model.playlist) == 0:
                self.playlist.set('')
            else:
                self.playlist.current(0)
            self.update_playframe()


    def insert(self):
        pass

    def set_custom_time(self):
        answer = simpledialog.askstring("Input", "Time (Hours:Minutes:Seconds)")
        hours, minutes, seconds = answer.split(":")
        time = 1000*(3600*int(hours)+60*int(minutes) + int(seconds))
        self.model.player.set_time(time)

    def change_volume(self, amount):
        volume = self.model.player.audio_get_volume()+amount
        self.volumescale.set(volume)
        self.model.player.audio_set_volume(volume)
        self.tempshow(f"Set Volume: {volume}%")

    def addsubs(self):
        file_path = filedialog.askopenfilename()
        media = self.model.vlc.media_new(file_path).get_mrl()
        self.model.player.add_slave(0, media, True)

    def removesubs(self):
        self.model.player.video_set_spu(-1)

    def skip(self, amount):
        if "duration" in self.item:
            time = self.model.player.get_time() + amount
            if time < 0:
                time = 0
            if time > self.item.get('duration',10000000):
                time = self.item.get('duration',10000000)
            self.model.player.set_time(time)
            self.timescale.set(time)

    def temphide(self):
        self.templabel.pack_forget()

    def tempshow(self, textvariable: str, counter=3):
        self.counter = counter
        self.templabel.config(text=textvariable)
        self.templabel.pack(side="top", anchor="ne")
        if self.temphide not in self.func:
            self.func.append(self.temphide)

    def set_speed(self, factor: int):
        self.speed += factor
        self.tempshow(f"Set Speed: {self.speed}%")
        speed = self.speed/100
        self.model.player.set_rate(speed)

    def set_prefered_quality(self, quality: str):
        self.model.set_prefered_quality(quality, self.item)
        self.boldify()


    def boldify(self):
        for index in range(self.quality_menu.index('end')+1):
            label = self.quality_menu.entrycget(index, 'label')
            if label == self.model.pref_qual:
                self.quality_menu.entryconfig(
                    index, foreground='gray')
            else:
                self.quality_menu.entryconfig(
                    index, foreground='black')
            if label in self.item:
                self.quality_menu.entryconfig(
                    index, background=self.pastel_blue)
            else:
                self.quality_menu.entryconfig(
                    index, background=self.defaultbg)
        self.quality_menu.entryconfig(
            self.model.current_quality, background='light blue')

    def prepause1(self, event):
        self.counter = 2
        self.checkvar = self.fullscreen
        self.func.append(self.prepause2)

    def prepause2(self):
        if self.fullscreen == self.checkvar:
            self.toggle_pause()

    def toggle_pause(self, event=None):
        self.videodisplay.focus_set()
        state = self.model.player.get_state()
        if state == state.NothingSpecial:
            self.pausebutton.config(text="▶")
            return
        else:
            pause = self.model.player.is_playing()
            self.model.player.set_pause(pause)
            self.pausebutton.config(text=["||", "▶"][pause])
            self.tempshow(["Play", "Pause"][pause])

    def toggle_FullScreen(self, event):
        self.videodisplay.focus_set()

        if self.fullscreen == 0:
            self.sideframe.pack_forget()
            self.superframe.pack_forget()
            self.fullscreen = 1
            self.win.attributes("-fullscreen", True)
            self.win.config(menu="")
            self.videoframe.pack_forget()
            self.toolframe.pack_forget()
            self.superframe.place(relwidth=1,relheight=1)
            self.videoframe.place(relwidth=1, relheight=1)
            self.prevwidth = self.win.winfo_width()
            self.prevheight = self.win.winfo_height()
            self.videodisplay.focus_set()
            self.show()
        elif self.fullscreen == 1:
            self.fullscreen = 0
            self.superframe.place_forget()
            self.superframe.pack(side="left", anchor="ne", fill="both", expand=True)
            self.win.config(menu=self.menubar)
            self.videoframe.place_forget()
            self.toolframe.pack(side="top", fill=X, expand=True, anchor="n")
            self.videoframe.pack(side="bottom")
            self.sideframe.pack(side="right", anchor="n", fill="y")
            self.win.attributes("-fullscreen", False)
            self.win.geometry(f"{self.prevwidth}x{self.prevheight}")

    def update_label(self, label, content: str):
        label.config(state="normal")
        label.delete(0, END)
        label.insert(0, content)
        label.config(state="disable")

    def collect(self, event):
        self.selected_widget = False
        self.videodisplay.focus_set()
        self.inventory = self.model.youtube_search(self.searchentry.get())
        self.videodisplay.focus_set()
        self.update_sideframe()

    def add2(self, event):
        if self.selected_widget:
            item = self.inventory[self.selected_widget.cget("text").splitlines()[0]].copy()
            self.model.playlist[item["title"]] = item

    def update_sideframe(self, playlist=False):
        self.search_results.config(state="normal")
        self.search_results.delete("1.0", "end")
        self.search_results.insert("end",'\n')
        b = Label(self.search_results, text="Add To Playlist", bg=self.dark_pastel_blue, fg="white", cursor="hand2", width = 60, anchor="w", justify="left")
        b.bind('<Button-1>', self.add2)
        self.search_results.window_create("end", window=b)
        self.search_results.insert("end",'\n')
        self.search_results.window_create("end", window=b)
        self.search_results.insert("end",'\n')
        if playlist:
            b = Label(self.search_results, text="BACK TO ORIGINAL QUERY", bg=self.dark_pastel_blue, fg="white", cursor="hand2", width = 60, anchor="w", justify="left")
            b.bind('<Button-1>', self.redo)
            self.search_results.window_create("end", window=b)
            self.search_results.insert("end",'\n')
        for item in self.inventory:
            blurb = str(item+"\nPlay Time: "+ self.inventory[item].get("play_time","")+" Channel: "+ self.inventory[item].get("channel", "")  +"\n"+self.inventory[item].get("date","")+" "+self.inventory[item].get("description","")[:60]+"...")
        
            b = Label(self.search_results, text=blurb ,bg=self.pastel_blue, cursor="hand2", width = 60, height=3,borderwidth=2,highlightcolor="black",highlightbackground="black", relief="groove",justify="left", anchor="w")
            if "PLAYLIST" in item:
                b.config(bg=self.dark_pastel_blue)
            b.bind("<Button-4>", self.on_mousewheel)
            b.bind("<Button-5>", self.on_mousewheel)
            b.bind('<Button-1>', lambda event, item = item, b=b: self.showww(self.inventory[item].copy(), b))
            self.search_results.window_create("end", window=b)
            self.search_results.insert("end",'\n')
        self.search_results.config(state="disable")

    def update_playframe(self):
        if self.show_playframe == 1:
            self.play_results.config(state="normal")
            self.play_results.delete("1.0", "end")
            self.play_results.insert("end",'\n')
            for item in self.model.playlist:
                b = Label(self.play_results, text=item ,bg=self.pastel_blue, cursor="hand2", width = 60, height=3,borderwidth=2,highlightcolor="black",highlightbackground="black", relief="groove",justify="left", anchor="w")
                b.bind("<Button-4>", self.on_mousewheel)
                b.bind("<Button-5>", self.on_mousewheel)
                b.bind('<Button-1>', lambda event, item = item, b=b: self.showww(self.model.playlist[item].copy(),b))
                self.play_results.window_create("end", window=b)
                self.play_results.insert("end",'\n')
            self.play_results.config(state="disable")

    def redo(self, event):
        self.inventory = self.temp_inventory
        self.update_sideframe()

    def showww(self, item, widget):
        color = widget.cget("bg")
        if color == self.pastel_blue:
            widget.config(bg="red")
            if self.selected_widget:
                self.selected_widget.config(bg=self.pastel_blue)
            self.selected_widget = widget
        else:
            widget.config(bg=self.pastel_blue)
            if "PLAYLIST" not in item["title"]:
                self.item = item
                if "google" not in self.item:
                    self.item.update(self.model.collect(self.item["url"]))
                    self.play()
                else:
                    self.text_display(self.model.collect(self.item["url"]))
                    
                
            else:
                self.temp_inventory = self.inventory
                self.inventory = self.model.playlist_get(item["url"])
                self.update_sideframe(True)

    def render_js(self, event):
        self.text_display(self.model.collect_google(self.item["url"], 1))

    def text_display(self, text):
        self.update_label(self.playingentry, "Article: " + self.item.get('title',"no title"))
        self.text_widget_frame.place(relwidth=1,relheight=1)
        self.text_widget.config(state="normal", font=f"arial 12", fg="black", bg=self.pastel_blue)
        self.text_widget.delete("2.0", "end")
        self.positions = {}
        if "str" in str(type(text)):
            self.text_widget.insert("end",'\n'+text)
        else:
            for item in text:
                self.text_widget.insert("end",'\n'+str(item.text) + '\n' , str(item.name))
                if "h" in str(item.name):
                    self.positions[str(item.text)] = self.text_widget.index("end")
            self.h_box['values'] = list(self.positions.keys())
        self.h_box.set("")
        self.text_widget.tag_configure('h2', font=f"arial 14", relief='raised')
        self.text_widget.tag_configure('h1', font=f"arial 16", relief='raised')
        self.text_widget.config(state="disable")

    def jump(self, event):
        line = self.positions[self.h_box.get()]
        self.text_widget.see(line)

    def hide_text_widtget(self, event):
        self.text_widget_frame.place_forget()


    def preload2(self, amount=0):
        index = self.playlist.get()
        place = self.playlist.current()
        if place > -1:
            self.item = self.model.playlist[index].copy()
            self.item.update(self.model.collect(self.item["url"]))
            if self.item == "Error":
                return
            if place < len(self.model.playlist)-1:
                self.playlist.current(place+1)
            else:
                self.playlist.set("")
            if self.preloadflag == 0:
                self.play()

    def play(self):
        self.preloadflag = 0
        self.timelabel.config(text="0:00:00 / " + str(timedelta(milliseconds=self.item.get("duration",10000000))))
        self.timescale.set(0)
        if self.playlist_title != "":
            self.win.title(self.playlist_title)
        else:
            self.win.title(self.item.get('title',"no title"))
        self.pausebutton.config(text="||")
        playurl, audio = self.model.select_quality(self.item)
        self.model.play(playurl, audio)
        self.timescale.config(to=self.item.get('duration',10000000))
        self.boldify()
        self.tempshow(self.model.current_quality, 5)
        self.update_label(self.playingentry, "Playing: " + self.item.get('title',"no title"))

    def show(self, event=None):
        self.counter = 3
        if self.hide not in self.func:
            self.func.append(self.hide)
        if self.hidden == 1:
            self.videodisplay.config(cursor="arrow")
            self.timeframe.pack(side="bottom", fill="both")
            self.hidden = 0

    def hide(self):
        self.hidden = 1
        self.videodisplay.config(cursor="none")
        self.timeframe.pack_forget()

    def timerfunction(self):
        self.counter -= 1
        if self.counter == 1:
            for item in self.func:
                item()
            self.func = []

    def set_duration(self):
        duration = self.model.player.get_length()
        if duration != 0:
            self.item["duration"] = duration
            self.timescale.config(to=duration)
            time_info1 = str(timedelta(seconds=round(
            self.time / 1000)))
            time_info2 = str(timedelta(seconds=round(
            duration / 1000)))
            self.timelabel.config(text=time_info1 + " / " +  time_info2)

    def update_time(self):
        self.time = self.model.player.get_time()
        if not "duration" in self.item:
            self.set_duration()
        if (self.item.get("duration",10000000) - self.time) < 20000 and self.preloadflag == 0 and self.autoplay == 1:
            if self.playlist.get() != "" and self.playlist.get() != "Playlist Is Empty":
                self.preloadflag = 1
                self.preload2()
        label = self.timelabel.cget("text")
        time_info = str(timedelta(seconds=round(
            self.time / 1000)))
        self.timelabel.config(text=time_info + label[7:])
        self.timescale.set(self.time)   

    def timeloop(self):
        #print(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2)
        if self.counter > 0:

            self.timerfunction()
        state = self.model.player.get_state()
        if state == state.Playing:
            self.update_time()

        elif self.autoplay and state == state.NothingSpecial or state == state.Ended:
            if self.preloadflag == 1:
                self.play()
            else:
                if (self.playlist.get() != "" and self.playlist.get() != "Playlist Is Empty"):
                    self.preload2()
                else:
                    self.pausebutton.config(text="▶")
        self.win.after(1000, self.timeloop)

    def timescale_move(self, timescale_var: int):
        if abs(int(timescale_var) - self.model.player.get_time()) > 4000:
            self.model.player.set_time(int(timescale_var))

    def download(self):
        if "url" in self.item:
            answer = simpledialog.askstring("Input", "title")
            self.model.download(self.item['url'], answer)

    def on_mousewheel(self,event):
        scroller = [self.search_results, self.play_results][self.show_playframe]
        if event.num==4:
            scroller.yview("scroll",-1,"units")
        else:
            scroller.yview("scroll",1,"units")

    def make_gui(self, argument):
        Gui(argument)

    def quit(self):
        del self.model.player
        del self.model.vlc
        del self.model
        self.win.after(100, self.win.destroy)


class Model:

    def __init__(self, argument: str):
        self.vlc = vlc(argument)
        self.player = self.vlc.media_player_new()
        self.pref_qual = "1080p"
        self.current_quality = "1080p"
        self.playertype = "Youtube"
        self.playlist = {}

    def set_player(self, player):
        self.playertype = player

    def change_volume(self, volume_var: int):
        self.player.audio_set_volume(int(volume_var))

    def set_prefered_quality(self, quality: str, item: dict):
        self.pref_qual = quality
        self.quality_change(item)

    def quality_change(self, item: dict):
        url, audio = self.select_quality(item)
        place = self.player.get_time()
        self.play(url, audio)
        self.player.set_time(place)

    def youtube_search(self, term: str) -> dict:
        if self.playertype == "Youtube":
            return self.search(term)
        elif self.playertype == "Vimeo":
            return self.search_vimeo(term)
        elif self.playertype == "Dailymotion":
            return self.search_dailymotion(term)
        elif self.playertype == "Odysee":
            return self.search_odysee(term)
        elif self.playertype == "Archive":
            return self.search_archive(term)
        elif self.playertype == "Google":
            return self.search_google(term)
        elif self.playertype == "Tucker Carlson":
            return self.search_tc(term)


    def collect(self, url: str) -> dict:
        if "vimeo" in url or "youtube" in url or "dailymotion" in url:
            ydl_opts = {"quiet": True}
            try:
                with YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
            except:
                return "Error"
            if "vimeo" in url:
                return self.collect_vimeo(info)
            elif "youtube" in url:
                return self.collect_youtube(info)
            elif "dailymotion" in url:
                return self.collect_dailymotion(info)
        if "odysee" in url:
            return self.collect_odysee(url)
        elif "archive.org" in url:
            return self.collect_archive(url)
        elif "foxnews.com" in url:
            return self.collect_tc(url)
        else:
            return self.collect_google(url)


    def select_quality(self, item):
        index = QUAL_LIST.index(self.pref_qual)
        audio = ""
        for count in range(index, -1, -1):
            if QUAL_LIST[count] in item:
                current_quality = item[QUAL_LIST[count]]
                self.current_quality = QUAL_LIST[count]
                break
        if index > 1 and "youtube" in item["url"] or "vimeo" in item["url"]:
            audio = item["best_audio"]
        return current_quality, audio

    def play(self, url, audio):
        self.media = self.vlc.media_new(url)
        self.player.set_time(0)
        self.player.set_media(self.media)
        self.player.play()
        if audio != "" and "Dailymotion" not in url:
            self.player.add_slave(1, audio, True)

    def download(self, url, title):
        if "p" in self.current_quality:
            codec = "mp4"
        else:
            codec = "mp3"
        ydl_opts = {
            'outtmpl': title + '.%(ext)s',
            'postprocessors': [{
                'preferredcodec': codec}]}
        if codec == "mp3":
            ydl_opts["postprocessors"][0]['key']='FFmpegExtractAudio'
        with YoutubeDL(ydl_opts) as ydl:
            ydl.extract_info(url, download=True)

    def collect_youtube(self, info) -> dict:
        item = dict()
        item['duration'] = 1000 * info['duration']
        item['description'] = "".join([
            s for s in info['description'].strip().splitlines(True)
            if s.strip()])
        for format in info['formats']:
            video_ext = format['video_ext']
            audio_ext = format['audio_ext']
            media_format = format['format']
            media_format = media_format[
                media_format.find("(")+1:media_format.find(")")]
            if audio_ext == "none" and video_ext != "mp4":
                continue
            if "least_audio" not in item:
                item['least_audio'] = format['url']
            if audio_ext != "none":
                item['best_audio'] = format['url']
            if video_ext == "mp4":
                item[media_format] = format['url']
                if "relation" not in item:
                    x, y = format['resolution'].split("x")
                    item["relation"] = int(y)/int(x)
        return (item)

    def collect_google(self, url, js=0):
        if js == 1:
            session = HTMLSession()
            headers = {
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
            cookies = {'CONSENT': 'YES+cb.20210328-17-p0.en-GB+FX+{}'.format(randint(100, 999))}
            try:
                resp = session.get(url, timeout=10, headers=headers, cookies=cookies)
            except:
                return "connection error"
            resp.html.render(reload=False)
            session.close()
            line = resp.html.html
        else:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
            
            line = request(url, timeout=10, headers=headers,cookies={'CONSENT': 'YES+cb.20210328-17-p0.en-GB+FX+{}'.format(randint(100, 999))}).text
        if "azlyrics" in url:
            x = self.collect_azlyrics(line)
        else:
            soup = BeautifulSoup(line, "html.parser")
            body = soup.find("body")
            x = body.find_all(["p", "h1","h2","pre"])
        return x

    def collect_azlyrics(self, resp):
        index1 = resp.index('<h2>')
        index2 = resp.index("</div>", index1)
        index2 = resp.index("</div>", index2 + 10)
        index2 = resp.index("</div>", index2 + 10)
        soup = BeautifulSoup(resp[index1:index2], "html.parser")
        return soup.text

    def search_google(self, search_terms):
        encoded_search = quote_plus(search_terms)
        url = f"https://www.google.nl/search?q={encoded_search}&start=0&num=30"
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
        try:        
            line = request(url, timeout=10, headers=headers,cookies={'CONSENT': 'YES+cb.20210328-17-p0.en-GB+FX+{}'.format(randint(100, 999))}).text
        except:
            return
        soup = BeautifulSoup(line, "html.parser")
        output = {}
        for result in soup.find_all('a',href = True): 
            x = result.text
            
            if " › " in x and not "youtube" in x:
                try:
                    title = result.find("h3").text
                    description = x[len(title):]
                    url=unquote(result["href"].split("url=")[1].split("&ved=")[0])
                    output[title]={"title": title,"description":description,"url": url, "google":"1"}
                except:
                    pass

        return output


    def search_tc(self, search_terms):
        elements = [
            "imageUrl", "title", "description", "url", "publicationDate", "lastPublishedDate",
            "category", "name", "isBreaking", "isLive", "duration", "authors"
            ]
        elements2 = ["a", "b", "c", "d", "e", "f", "h","i","j","k","l","m","n","A", "B", "C", "D", "E", "F","G",
        "H", "I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X"]
        url = "https://www.foxnews.com/person/c/tucker-carlson"
        try:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
            resp = request(url, timeout=10, headers=headers).text
        except:
            print("exc")
        index1 = resp.index("items:[") + 6
        index2 = resp.index("]}]") + 3
        resp = resp[index1:index2]
        for item in elements:
            resp = resp.replace(f"{item}:", f'"{item}":')
        for item in elements2:
            resp = resp.replace(f":{item}", f':""')
        x = loads(resp)
        result = {}
        for item in x:
            if "www.foxnews.com" not in item["url"]:
                url =  "http://www.foxnews.com" + item["url"]
            else:
                url = item["url"]
            result[item["title"]] = {
            "title": item["title"],
            "url": unquote(url),
            "description": item["description"],
            "play_time": item["duration"]
            }
        return result

    def collect_tc(self, url):

        try:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
            resp = request(url, timeout=10, headers=headers).text
        except:
            print("exc")
        index1 = resp.index('"contentUrl": ')
        index2 = resp.index('duration', index1)
        index2 = resp.index(',', index2)
        x = loads("{"+resp[index1:index2] + "}")

        thing = {"144p": x["contentUrl"],
            "description": x["description"],
            "title": x["name"]}
        return thing


    def search(self, search_terms: str) -> list:
        encoded_search = quote_plus(search_terms)
        url = f"https://www.youtube.com/results?search_query={encoded_search}"
        try:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
            line = request(url, timeout=10, headers=headers).text
        except:
            return
        index1 = line.index("videoRenderer")-5
        line = line[index1:]
        resultlist=dict()
        index2 = 0
        while True:
            try:
                index1 = line.index("videoRenderer", index2)-2
            except:
                break
            try:
                line[index2:index1].index("playlistRenderer")
            except:
                pass
            else:
                index3 = line.index("playlistRenderer", index2)-2
                index4 = line.index("}]}}}]}}", index2)+8
                x = loads(line[index3:index4])
                title = "PLAYLIST: " + x["playlistRenderer"]["title"]["simpleText"]
                resultlist[title] = {"url": "https://www.youtube.com/playlist?list=" + x["playlistRenderer"]["playlistId"],
                    "info": "",
                    "channel": "",
                    "date": "",
                    "play_time": "",
                    "description": "",
                    "title": title}
            index2 = line.index("searchVideoResultEntityKey", index1)-2
            result = line[index1:index2]+"}}"
            x = loads(result)
            x = x["videoRenderer"]

            try:
                suffix = x["detailedMetadataSnippets"][0]["snippetText"]["runs"][0]["text"]
            except:
                suffix = " "
            title =  x["title"]["runs"][0]["text"]
            resultlist[title] = {
                    "url": 'https://www.youtube.com/watch?v=' + x["videoId"],
                    "info": x["title"]["accessibility"]["accessibilityData"]["label"],
                    "channel": x["longBylineText"]["runs"][0]["text"],
                    "date": x.get("publishedTimeText",{}).get("simpleText"," "),
                    "play_time": x.get("lengthText",{}).get("simpleText"," "),
                    "description": suffix,
                    "title": title
                    }
        return resultlist

    def search_vimeo(self, search_terms):
        encoded_search = quote_plus(search_terms)
        url = f"https://vimeo.com/search?q={encoded_search}"
        try:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
            response = request(url, timeout=10, headers=headers).text
        except:
            return
        index1 = response.index("vimeo.config = ")
        index1 = response.index("[", index1)
        index2 = response.index("}}}]", index1) + 4
        text = response[index1:index2]
        dicti = loads(text)
        results = dict()
        for song in dicti:
            title = song["clip"]["name"] + " "
            while title in results:
                title += "I"
            results[title] = {
                "url": song["clip"]["link"],
                "play_time": str(song["clip"]["duration"]),
                "date": song["clip"]["created_time"][:7],
                "channel": song["clip"]["user"]["name"],
                "title": title
            }
        return results

    def search_odysee(self, search_terms):
        url = f"https://lighthouse.lbry.com/search?s={search_terms}&include=channel,title,description,duration,release_time&mediaType=video&size=50&from=0&nsfw=false"
        try:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
            response = request(url, timeout=10, headers=headers).text
        except:
            return
        results = dict()
        for item in loads(response):
            try:
                results[item["title"]] = {
                "title": item["title"],
                "date": item["release_time"][:9],
                "duration": int(item.get("duration",0)) * 1000,
                "play_time": str(timedelta(seconds=round(
                int(item["duration"])))),
                "description": item["description"],
                "channel": item["channel"],
                "url": "http://www.odysee.com/" + item["name"] + "/" + item["claimId"]
                }
            except:
                pass
        return results

    def search_archive(self, search_terms):
        encoded_search = quote_plus(search_terms)
        url = f"https://archive.org/services/search/beta/page_production/?service_backend=metadata&user_query={encoded_search}&hits_per_page=20&page=1&filter_map=%7B%22mediatype%22%3A%7B%22movies%22%3A%22inc%22%7D%7D&aggregations=false&uid=johnny+cash+AND+%28mediatype%3A%28%22movies%22%29%29-0-none-none&client_url=https%3A%2F%2Farchive.org%2Fsearch%3Fquery%3Djohnny%2Bcash%26and%5B%5D%3Dmediatype%253A%2522movies%2522"
        try:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
            resp = request(url, timeout=10, headers=headers)
        except:
            print("exc")
        results = {}
        response = loads(resp.text)["response"]["body"]["hits"]["hits"]
        for result in response:
            x = result["fields"]
            results[x["title"]] = {
            "title": x["title"],
            "url": "https://archive.org/download/" + x.get("identifier") + "/",
            "description": x.get("description"),
            "date": x.get("addeddate")
            }
        return results


    def search_dailymotion(self, search_terms):
        session = HTMLSession()
        url = f"https://www.dailymotion.com/search/{search_terms}/videos"
        headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
        try:
            resp = session.get(url, timeout=10, headers=headers)
        except:
            return "connection error"
        resp.html.render()
        temp = list()
        index2 = 0
        string = resp.html.html
        while True:
            try:
                index1 = string.index('<a href="/video/', index2)+9
            except ValueError:
                break
            index2 = string.index('>', index1)-1
            substring = string[index1:index2]
            if substring not in temp:
                temp.append(substring)
        index1 = resp.html.text.index("Filters") + 8
        index2 = resp.html.text.index("Filters", index1)-1
        x = 0
        y = 0
        result = {}
        item = {}
        for line in resp.html.text[index1:index2].splitlines():
            if x == 0:
                item["play_time"] = line
            elif x == 1:
                line += " "
                if line in result:
                    line += "I"
                item["title"] = line
            elif x == 2:
                item["channel"] = line
            elif x == 3:
                item["date"] = line
            x += 1
            if x == 4:
                result[item["title"]] = {
                    "url": "https://www.dailymotion.com" + temp[y],
                    "play_time": item["play_time"],
                    "title": item["title"],
                    "channel": item["channel"],
                    "date": item["date"]}
                x = 0
                y += 1
        return result

    def collect_vimeo(self, info: str) -> dict:
        tempitem = {}
        item = dict()
        item["duration"] = 1000 * info["duration"]
        item["play_time"] = info["duration_string"]
        item["description"] = info["description"]
        for format in info["formats"]:
            if "least_audio" not in item and "url" in format and format[
            "ext"] == "mp4":
                item["least_audio"] = format["url"]
            if "best_audio" not in item:
                if "format_id" in format and "high-audio" in format["format_id"]:
                    item["best_audio"] = format["url"]
                elif "format_id" in format and "medium-audio" in format["format_id"]:
                    item["best_audio"] = format["url"]
            if "video_ext" in format and "url" in format and format[
            "video_ext"] != "none" and "filesize_approx" in format:
                if "resolution" in format and "relation" not in item:
                    if "relation" not in item:
                        x, y = format['resolution'].split("x")
                        item["relation"] = int(y)/int(x)
                size = format["filesize_approx"]
                size = size / 8000
                size = "{:02d}".format(round(size/(item['duration'])))
                size = f"{size} kb/s"
                tempitem[size] = format["url"]
        holderlist = []
        for key in tempitem:
            holderlist.append(key)
        holderlist.sort()
        length = len(holderlist) - 1
        item[QUAL_LIST[2]] = tempitem[holderlist[0]]
        item[QUAL_LIST[3]] = tempitem[holderlist[round(length/4)]]
        item[QUAL_LIST[4]] = tempitem[holderlist[round(length/2)]]
        item[QUAL_LIST[5]] = tempitem[holderlist[round(length-(length/4))]]
        item[QUAL_LIST[6]] = tempitem[holderlist[(length)]]
        return item

    def collect_odysee(self, url):
        try:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
            resp = request(url, timeout=10, headers=headers)
        except:
            print("exc")
        index1 = resp.text.index('">\n{') + 3
        index2 = resp.text.index("}\n<", index1) + 1
        string = loads(resp.text[index1:index2])
        result = {
            "240p": string["contentUrl"],
            "relation": string["width"] / string["height"],
            }
        return result

    def collect_archive(self,url):
        try:
            headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
            x = request(url, timeout=10, headers=headers).text
        except:
            print("exc")
        index1 = x.index("<tbody>")
        index2 = x.index("</tbody>") + 5
        x = x[index1:index2]
        results = []
        results2 = []
        while True:
            try:
                index1 = x.index("a href") + 8
            except:
                break
            index2 = x.index('"', index1)
            index3 = x.index("<td>", index2)+4
            index3 = x.index("<td>", index3) + 4
            index4 = x.index("</td>", index3)
            if "M" in x[index3:index4]:
                results.append(url + x[index1:index2])
                results2.append(round(float(x[index3:index4].replace(",","")[:-1])))
            elif "G" in x[index3:index4]:
                results.append(url + x[index1:index2])
                results2.append(round(1000*float(x[index3:index4].replace(",","")[:-1])))
            x = x[index2:]
        result = [x for _,x in sorted(zip(results2,results))]
        res={}
        for x in range(0,len(result)):
            res[QUAL_LIST[x+2]] = result[x]

        return res


    def collect_dailymotion(self, info: str) -> dict:
        result = {}
        result["description"] = info["description"]
        result["duration"] = info["duration"]*1000
        for format in info["formats"]:
            if "380" in format["format_id"]:
                result["least_audio"] = format["url"]
                if "relation" not in result:
                    x, y = format['resolution'].split("x")
                    result["relation"] = int(y)/int(x)
            if "480" in format["format_id"]:
                result["480p"] = format["url"]
            if "720" in format["format_id"]:
                result["720p"] = format["url"]
            if "1080" in format["format_id"]:
                result["1080p"] = format["url"]
        return result

    def playlist_get(self,url):
        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'}
        try:
            line = request(url, timeout=10, headers=headers,cookies={'CONSENT': 'YES+cb.20210328-17-p0.en-GB+FX+{}'.format(randint(100, 999))}).text
        except:
            pass
        index1 = line.index("playlistVideoRenderer")-5
        index2 = line.index(',"header":')
        line = line[index1:index2]
        resultlist=[]
        index2 = 2
        resultlist = {}
        while True:
            try:
                index1 = line.index("playlistVideoRenderer", index2)-2
                index2 = line.index("}]}}},", index1)+5
            except:
                break
            x = loads(line[index1:index2])
            x = x["playlistVideoRenderer"]
            title = x["title"]["runs"][0]["text"]
            resultlist[title] = {
                "url":"https://www.youtube.com/watch?v=" + x["videoId"],
                "title":title,
                "description": "''",
                "date":x["videoInfo"]["runs"][2]["text"],
                "channel": x["shortBylineText"]["runs"][0]["text"],
                "play_time": x["lengthText"]["simpleText"],
                "duration": x["lengthSeconds"]
                }
        return resultlist



    def read(self):
        with open("/home/balthazar/list.json", "r") as fp:
            return load(fp)

    def write(self, obj):
        with open("/home/balthazar/list.json", "w+") as fp:
            dump(obj, fp, indent=4, separators=(',', ': '))

    def generate_dict(self, title, playlist):
        item = {"title": title,
                "playlist": playlist}
        try:  
            listObj = self.read()
            listObj.append(item)

        except:  
            listObj = [item]
        self.write(listObj)

    def read_dict(self):
        try:
            x = self.read()
            ext_playlists = list()
            for item in x:
                ext_playlists.append(item["title"])
            return ext_playlists
        except:
            self.write([])
            return([])

    def get_playlist(self, title):
        x = self.read()
        for item in x:
            if item["title"] == title:
                return item["playlist"]

    def change_title(self, title, new_title):
        x = self.read()
        a = 0
        for item in x:
            if item["title"] == title:
                x[a]["title"] = new_title
                self.write(x)
                break
            a += 1

    def update_playlist(self, title, playlist):
        x = self.read()
        a = 0
        for item in x:
            if item["title"] == title:
                x[a]["playlist"] = playlist
                self.write(x)
                break
            a += 1

    def delete_playlist(self, title):
        x = self.read()
        a = 0
        for item in x:
            if item["title"] == title:
                del x[a] 
                self.write(x)
                break
            a += 1


def main():
    Gui()


if __name__ == '__main__':
    main()
