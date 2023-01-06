from tkinter import (
    Tk, Menu, Frame, Label, Button, Scale, Toplevel,
    BOTH, Entry, DISABLED, END, HORIZONTAL, VERTICAL
)
from vlc import Instance
from yt_dlp import YoutubeDL
from random import shuffle, choice
from datetime import timedelta
from csv import writer, reader
from requests import get
from urllib.parse import quote_plus
from json import loads
MEDIA_QUALITIES = [
        'ultralow',
        'low',
        'medium',
        'high',
        '144p',
        '240p',
        '360p',
        '480p',
        '720p',
        '1080p',
        '1440p',
        '2160p'
    ]
PATH = 'MediaStreamerInventories.txt'


class Music_Interface:
    '''the music interface is the main class here. It creates a gui,
        puts in subclasses (the vlc player, the two Contractors,
        the time scale, volume scale, menu's etc.)
        Originally the functions for transferring data between the two
        so called contractors was to be a separate class, for the sake of
        clarity, but it became such a small class that I included in in the
        main interface.
    '''

    def __init__(self):
        self.win = Tk()
        self.win.geometry("500x150")
        self.win.protocol('WM_DELETE_WINDOW', self.quit)
        self.win.title("Multimedia Interface")
        self.menubar = Menu(self.win)
        self.win.config(menu=self.menubar)
        self.main_frame = Frame(self.win, width=320, height=600)
        self.main_frame.grid(row=1, column=1, padx=0, sticky='new')
        self.quasitor_frame = Frame(self.main_frame, width=150)
        self.quasitor_frame.grid(row=1, column=1, rowspan=3)
        self.quasitor_frame.bind(
            '<Button-1>', lambda event: self.quasitor_frame.focus_set())
        self.quasitor_frame.bind('<Left>', lambda event: self.skip(-10000))
        self.quasitor_frame.bind('<Right>', lambda event: self.skip(10000))
        self.quasitor = Quasitor(self.quasitor_frame)
        Button(
            self.quasitor_frame, text="OK",
            command=self.inject).pack(side='left')
        Button(
            self.quasitor_frame, text="+",
            command=self.add).pack(side='left')
        self.selector_frame = Frame(self.main_frame, width=150)
        self.selector_frame.grid(row=1, column=2, rowspan=3)
        self.item_label = Entry(self.selector_frame, state=DISABLED)
        self.item_label.pack(side='top', anchor="w")
        self.selector = Selector(self.menubar, self.selector_frame)
        Button(
            self.selector_frame, text="OK",
            command=self.preload).pack(side='left')
        self.vlc_instance = Instance('--no-xlib -q > /dev/null 2>&1')
        self.player = self.vlc_instance.media_player_new()
        self.prefered_quality = 3
        self.current_quality = 0
        self.item = {}
        self.item['duration'] = 0
        self.item['quality_levels'] = []
        self.time = 0
        self.description_frame = Frame(self.main_frame, width=320, height=100)
        self.description_frame.grid(
            row=5, column=1, padx=0, sticky='nesw',
            columnspan=3, rowspan=4)
        self.description_label = Entry(self.description_frame, state=DISABLED)
        self.description_label.pack(side='top', anchor="w", fill=BOTH)
        self.volume_scale = Scale(
            self.main_frame, from_=200, to=0, orient=VERTICAL,
            showvalue=0, command=self.change_volume)
        self.volume_scale.set(100)
        self.volume_scale.grid(
            row=1, column=3, padx=0,
            sticky='nsew', rowspan=4)
        self.time_frame = Frame(self.main_frame, width=320)
        self.time_frame.grid(
            row=4, column=1, padx=0,
            sticky='new', columnspan=2)
        self.pause_button = Button(
            self.time_frame,
            text="▶", command=self.toggle_pause2)
        self.pause_button.pack(side='left')
        self.quasitor_frame.bind('<space>', self.toggle_pause2)
        self.selector_frame.bind('<space>', self.toggle_pause2)

        self.time_label = Label(
            self.time_frame, text="0:00:00 / 0:00:00")
        self.time_label.pack(side='left')
        self.timescale = Scale(
            self.time_frame, from_=0, to=1000,
            orient=HORIZONTAL, length=267,
            showvalue=0, command=self.timescale_move)
        self.timescale.pack(side='left')
        self.quality_menu = Menu(self.menubar, tearoff=0)
        self.current_quality_menu = Menu(self.menubar, tearoff=0)
        self.prefered_quality_menu = Menu(self.menubar, tearoff=0)
        self.prefered_quality_menu.add_command(
            label="best video format",
            command=(lambda: self.set_prefered_quality(11)))
        self.prefered_quality_menu.add_command(
            label="best audio format", command=(
                lambda: self.set_prefered_quality(3)))
        self.prefered_quality_menu.add_command(
            label="least audio format",
            command=(lambda: self.set_prefered_quality(0)))
        self.menubar.add_cascade(
            label="Quality", menu=self.quality_menu)
        self.quality_menu.add_cascade(
            label="Set prefered quality",
            menu=self.prefered_quality_menu)
        self.quality_menu.add_cascade(
            label="Set current item quality",
            menu=self.current_quality_menu)
        self.menubar.add_cascade(
            label="Playlists", menu=self.selector.inventory_menu)
        self.selector.inventory_menu.add_command(
            label="all results to playlist",
            command=self.extend)
        self.selector.inventory_list_menu.add_command(
            label="rename current playlist",
            command=self.rename)
        self.time_loop()
        self.win.mainloop()

    def extend(self):
        self.selector.extend(self.quasitor.inventory)

    def add(self):
        item = self.quasitor.get_item()
        if item:
            self.selector.add(item)
            self.quasitor.browse(1)

    def inject(self):
        if self.quasitor.get_length() > 0:
            self.load(self.selector.collect(self.quasitor.get_item()))
            self.quasitor.browse(1)

    def preload(self):
        if self.selector.index < self.selector.get_length():
            self.load(self.selector.collect())
            self.selector.browse(1)

    def timescale_move(self, timescale_var):
        if abs(int(timescale_var) - self.player.get_time()) > 4000:
            self.player.set_time(int(timescale_var))

    def skip(self, amount):
        time = self.player.get_time() + amount
        if time < 0:
            time = 0
        if time > self.item['duration']:
            time = self.item['duration']
        self.player.set_time(time)
        self.timescale.set(time)

    def toggle_pause2(self, event=None):
        pause = self.player.is_playing()
        if self.item['duration'] == 0:
            pause = 1
        self.player.set_pause(pause)
        self.pause_button.config(text=["||", "▶"][int(pause)])

    def change_volume(self, volume_var: int):
        self.player.audio_set_volume(int(volume_var))

    def rename(self):
        top = Toplevel(self.win)
        top.geometry("200x200")
        entry = Entry(top, width=25)
        entry.pack()
        entry.focus_set()
        Button(top, text="OK", command=(
            lambda: self.rename2(top, entry))).pack()
        Label(
            top, wraplength=200, width=200, height=100,
            text="enter new name; change will take in effect next " +
            "time you open the program").pack()

    def rename2(self, top, entry):
        var = entry.get()
        top.destroy()
        self.selector.rename(var)

    def select_stream_quality(self, index: int, absolute_index: int):
        ''' most of this code is for when the media quality
        is changed while playing. However, it is also used
        to load new media. The prefered quality is updated
        in case it changed, the current quality (index
        from stream url list of current song) is also
        updated, which is used when downloading the current
        song '''

        self.prefered_quality = absolute_index
        self.current_quality = index
        self.item['stream_url'] = self.item['stream_list'][index]
        time = self.player.get_time()
        media = self.vlc_instance.media_new(self.item['stream_url'])
        media.get_mrl()
        self.player.set_media(media)
        self.player.play()
        self.player.set_time(time)

    def set_menus(self):
        '''Here, the streams are evaluated to update all the
        menus so that it is possible to select highest video quality,
        highest audio quality, lowest audio quality or
        more exact choice of quality.'''
        index = -1
        for quality in self.item['quality_levels']:
            index += 1
            absolute_index = MEDIA_QUALITIES.index(quality)
            audio_or_video = ["audio only, ", "video, "][quality[0].isdigit()]
            quality_label = audio_or_video + quality
            if absolute_index <= self.prefered_quality:
                self.current_quality = index
            if quality[0].isalpha():
                self.prefered_quality_menu.entryconfigure(
                    1, command=(lambda index=index:
                                self.select_stream_quality(index, 3)))
            self.current_quality_menu.add_command(
                label=quality_label, command=(
                    lambda index=index, absolute_index=absolute_index:
                    self.select_stream_quality(
                        index, absolute_index)))
        self.prefered_quality_menu.entryconfigure(
            0, command=(lambda index=index: self.select_stream_quality(
                index, 11)))
        self.prefered_quality_menu.entryconfigure(
            2, command=(lambda: self.select_stream_quality(
                0, 0)))

    def delete_quality_menu(self, delete_list: list):
        '''deleting the specific qualities, to make new ones
        for the next song'''
        for quality in delete_list:
            if quality[0].isdigit():
                self.current_quality_menu.delete(f"video, {quality}")
            else:
                self.current_quality_menu.delete(f"audio only, {quality}")

    def load(self, item):
        self.player.set_time(0)
        self.player.set_pause(1)
        self.delete_quality_menu(self.item['quality_levels'])
        self.item = item
        self.set_menus()
        self.select_stream_quality(
            self.current_quality, self.prefered_quality)
        self.pause_button.config(text="||")
        self.timescale.config(to=self.item['duration'])
        self.timescale.set(0)
        self.win.title(self.item['title'])
        self.update_label(
            self.description_label, self.item['description'])
        self.update_label(
            self.item_label, self.item['title'])

    def update_label(self, label, content):
        label.config(state="normal")
        label.delete(0, END)
        label.insert(0, content)
        label.config(state="disable")

    def time_loop(self):
        if self.player.is_playing():
            self.time = self.player.get_time()
            time_info = str(timedelta(seconds=round(
                self.time / 1000))) + " / " + str(
                timedelta(seconds=round(
                    self.item['duration']/1000)))
            self.time_label.config(text=time_info)
            self.timescale.set(self.time)
        elif self.time > self.item['duration'] - 10000:
            item = self.selector.collect()
            if item:
                self.load(item)
                self.selector.browse(1)
        self.win.after(1000, self.time_loop)

    def set_prefered_quality(self, index: int):
        self.prefered_quality = index

    def quit(self):
        self.win.after(100, self.win.destroy)


class DataContractor:
    '''This is a macro-widget that serves to add information
    to given information of the user and display it. This class
    serves as superclass for subclasses with more specific
    functions to gather data.
    '''

    def place_widgets(self, widget_frame):
        self.label = Entry(widget_frame, state=DISABLED)
        self.label.pack(side='top')
        self.left = Button(widget_frame, text="←", command=(
                lambda: self.browse(-1))).pack(side='left')
        self.right = Button(widget_frame, text="→", command=(
                lambda: self.browse(1))).pack(side='left')

    def get_length(self) -> int:
        return (len(self.inventory))

    def get_title(self, index="") -> str:
        if index == "":
            index = self.index
        if index < self.get_length():
            return (self.inventory[self.index]['title'])
        else:
            return ("")

    def update_label(self):
        '''this is the way to update the text in
        disabled entries'''
        self.label.config(state="normal")
        self.label.delete(0, END)
        self.label.insert(0, self.get_title())
        self.label.config(state="disable")

    def browse(self, direction: int):
        self.frame.focus_set()
        if self.inventory:
            self.index += direction
            if self.index < 0 or self.index > self.get_length()-self.inundant:
                '#the inundant option is there to make the'
                '#playlist end on an "empty square" at the end'
                '#of the last song.'
                self.index -= direction
        self.update_label()

    def get_item(self) -> int:
        if self.index < self.get_length():
            return (self.inventory[self.index])

    def add(self, item: dict):
        self.inventory.append(item)
        self.update_label()

    def remove_item(self):
        if self.inventory:
            del self.inventory[self.index]
            self.browse(-1)

    def set(self, inventory, unit=""):
        self.index = 0
        self.inventory = inventory
        self.update_label()
        self.playlist = unit

    def extend(self, inventory: list):
        self.inventory.extend(inventory)
        self.update_label()


class Quasitor(DataContractor):
    '''this class receives search queries, and collects youtube URL and Title,
    and displays it
    '''

    def __init__(self, frame):
        self.inventory = []
        self.index = 0
        self.inundant = 1
        self.shuffle = 1
        self.frame = frame
        self.collector = YoutubeSearch()
        self.search_box = Entry(frame)
        self.search_box.pack(side='top')
        self.search_box.bind('<Return>', self.collect)
        self.search_box.focus_set()
        self.place_widgets(frame)

    def collect(self, event):
        self.frame.focus_set()
        self.set(self.collector.search(self.search_box.get(), self.shuffle))


class Selector(DataContractor):
    '''The selector is to select from the search results the desired one.
    Relevant data is taken from Youtube, such as the stream urls.
    '''

    def __init__(self, menu_location, frame):
        self.frame = frame
        self.playlist = ""
        self.inventory = []
        self.index = 0
        self.inundant = 0
        self.shuffle = False
        self.collector = YoutubeCollector()
        self.place_widgets(frame)
        Button(frame, text="X", command=self.remove_item).pack(side='left')
        Button(frame, text="↓", command=self.download).pack(side='left')
        self.inventory_menu = Menu(menu_location, tearoff=0)
        self.inventory_list_menu = Menu(menu_location, tearoff=0)
        self.inventory_menu.add_command(
            label="turn on shuffle",
            command=self.toggle_shuffle)
        self.inventory_menu.add_command(
            label="clear playlist",
            command=self.clear)
        self.inventory_menu.add_command(
            label="save playlist",
            command=self.inventory_export)
        self.inventory_menu.add_cascade(
            label="Playlists", menu=self.inventory_list_menu)
        self.filehandler = FileHandler()
        listlist = self.filehandler.inventory_import()
        for index in range(0, 100, 2):
            try:
                self.inventory_list_menu.add_command(
                    label=listlist[index], command=(
                        lambda inventory_import=listlist[index+1],
                        playlist=listlist[index]: self.set(
                            inventory_import, playlist)))
            except IndexError:
                break
        self.inventory_list_menu.add_command(
            label="remove current playlist", command=self.remove_playlist)

    def remove_playlist(self):
        self.filehandler.delete_row(self.playlist)
        self.inventory_list_menu.delete(self.playlist)
        self.playlist = ""

    def rename(self, var):
        self.filehandler.rename(self.playlist, var)

    def toggle_shuffle(self):
        self.shuffle = not self.shuffle
        on_or_off = ["on", "off"][int(self.shuffle)]
        self.inventory_menu.entryconfigure(
            0, label=f"turn {on_or_off} shuffle")

    def collect(self, item=False) -> dict:
        if not item:
            if self.shuffle == 1 and self.get_length() > 1:
                item = choice(self.inventory)
            else:
                item = self.get_item()
        if item:
            return (self.collector.collect(item))

    def inventory_export(self):
        if self.get_length() > 1:
            self.filehandler.inventory_export(
                self.get_title(0), self.inventory)
            self.inventory_list_menu.add_command(
                label=self.get_title(0), command=(
                    lambda inventory=self.inventory:
                    self.set(inventory)))

    def clear(self):
        self.inventory.clear()
        self.update_label()

    def download(self):
        self.collector.download()


class YoutubeCollector:
    '''This is a collector that gets from youtube the stream urls, titles
    and such. Also the option to download a song.
    '''

    def __init__(self):
        self.url = ""
        self.title = ""
        self.format_ids = ""

    def collect(self, item: dict) -> dict:
        ydl_opts = {"quiet": True}
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(item['url'], download=False)
            item['duration'] = 1000 * info['duration']
            item['description'] = "".join([
                s for s in info['description'].strip().splitlines(True)
                if s.strip()])
            item['quality_levels'] = []
            item['stream_list'] = []
            item['format_ids'] = []
            item['absolute_indices'] = []
            for format in info['formats']:
                media_format = format['format']
                media_format_short = media_format[
                    media_format.find("(")+1:media_format.find(")")]
                if ("storyboard" in media_format
                        or "dash" in media_format
                        or item['quality_levels'].count(
                            media_format_short) > 0):
                    continue
                if (int(format['format_id']) < 133
                        or "audio" in media_format):
                    '#the above criteria select only stream urls'
                    '#with audio or media and audio'
                    item['stream_list'].append(format['url'])
                    item['quality_levels'].append(media_format_short)
                    item['format_ids'].append(format['format_id'])
                    item['absolute_indices'].append(
                        MEDIA_QUALITIES.index(media_format_short))
        self.format_ids = item['format_ids']
        self.url = item['url']
        self.title = item['title']
        return (item)

    def download(self, quality=0):
        if self.url:
            ydl_opts = {
                'format_id': self.format_ids[quality],
                'outtmpl': self.title + '.%(ext)s',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3'}]}
            with YoutubeDL(ydl_opts) as ydl:
                ydl.extract_info(self.url, download=True)


class YoutubeSearch:
    '''Taken from YoutubeSearch library, and simplified.
    Fetches urls and titles for youtube items.'''

    def __init__(self):
        self.YOUTUBE_BASE_URL = 'https://www.youtube.com'

    def search(self, search_terms: str, random: int) -> dict:
        encoded_search = quote_plus(search_terms)
        url = f"https://www.youtube.com/results?search_query={encoded_search}"
        response = get(url).text
        while "ytInitialData" not in response:
            response = get(url).text
        results = self.parse_html(response)
        if random == 1:
            shuffle(results)
        return results

    def parse_html(self, response) -> dict:
        results = []
        start = response.index("ytInitialData") + 16
        end = response.index("};", start) + 1
        json_str = response[start:end]
        data = loads(
            json_str)["contents"]
        data = data["twoColumnSearchResultsRenderer"]["primaryContents"]
        for contents in data["sectionListRenderer"]["contents"]:
            for video in contents["itemSectionRenderer"]["contents"]:
                res = {}
                if "videoRenderer" in video.keys():
                    video_data = video.get("videoRenderer", {})
                    res["title"] = video_data.get(
                        "title", {}).get("runs", [[{}]])[0].get(
                        "text", None)
                    res["url"] = self.YOUTUBE_BASE_URL + video_data.get(
                        "navigationEndpoint", {}).get(
                        "commandMetadata", {}).get(
                        "webCommandMetadata", {}).get("url", None)
                    results.append(res)
            if results:
                return results
        return results


class FileHandler:
    '''This is for writing and reading the csv file with the playlists in it.
    '''
    def inventory_import(self) -> list:
        listlist = []
        try:
            with open(PATH, "r") as inventory_file:
                '#function to get the playlists from text file'
                csv_reader = reader(inventory_file,  delimiter=',')
                for inventory in csv_reader:
                    inventory_import = []
                    for url_title in range(1, 100, 2):
                        try:
                            item = {}
                            item['url'] = inventory[url_title]
                            item['title'] = inventory[url_title+1]
                            inventory_import.append(item)
                        except IndexError:
                            listlist.append(inventory[0])
                            listlist.append(inventory_import)
                            break
        except FileNotFoundError:
            with open('MediaStreamerInventories.txt', "w") as inventory_file:
                pass
        return (listlist)

    def inventory_export(self, name, inventory):
        '''saving the current playlist to txt file'''
        inventory_export = [name]
        for item in inventory:
            inventory_export.extend([item['url'], item['title']])
        with open(
                PATH, 'a',
                encoding='utf-8') as inventory_file:
            write = writer(inventory_file)
            write.writerow(inventory_export)

    def delete_row(self, playlist):
        newfile = list()
        with open(
                    PATH, 'r',
                    encoding='utf-8') as inventory_file:
            csv_reader = reader(inventory_file,  delimiter=',')
            for row in csv_reader:
                if row[0] != playlist:
                    newfile.append(row)
        with open(
                    PATH, 'w',
                    encoding='utf-8') as inventory_file:
            write = writer(inventory_file)
            write.writerows(newfile)

    def rename(self, playlist, var):
        newfile = list()
        with open(
                    PATH, 'r',
                    encoding='utf-8') as inventory_file:
            csv_reader = reader(inventory_file,  delimiter=',')
            for row in csv_reader:
                if row[0] != playlist:
                    newfile.append(row)
                else:
                    temprow = [var]
                    for index in range(1, len(row)-2):
                        temprow.append(row[index])
                    newfile.append(temprow)
        with open(
                    PATH, 'w',
                    encoding='utf-8') as inventory_file:
            write = writer(inventory_file)
            write.writerows(newfile)


def main():
    Music_Interface()


if __name__ == '__main__':
    main()
