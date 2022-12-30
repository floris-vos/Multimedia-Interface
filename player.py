from tkinter import (
    Tk, Menu, Frame, Label, Button, Scale, BOTH, Entry, DISABLED, END,NORMAL,StringVar, HORIZONTAL, VERTICAL, Text
)
from youtube_search import YoutubeSearch
import re,random, vlc,datetime, time,yt_dlp, csv, os, sys, json
from csv import writer
win = Tk()
win.geometry("500x150")
def quit():
    win.after(500,win.destroy)
win.protocol('WM_DELETE_WINDOW', quit)
MAX_SONG_LENGTH = 300
YOUTUBE_BASE_URL = 'https://www.youtube.com'
NON_CHARS = r'[^a-zA-Z0-9 .,:;+-=!?/()öäßü]'

shuffle=0
prefered_quality=2

media_qualities = [
    'ultralow',
    'low',
    'medium',
    '144p',
    '240p',
    '360p',
    '480p',
    '720p',
    '1080p',
    '1440p',
    '2160p'
]

query_index = 0; timescale_var =0
play_index=-1
playlist_index = 0
volume_var= 100
query_list = []; playlist = []
win.title("Youtube Player")
instance = vlc.Instance('--no-xlib -q > /dev/null 2>&1')
player = instance.media_player_new() 

def query_songs(event):
    playlist_frame.focus_set()
    global query_index, query_list
    query_list = song_search(str(search_box.get()))
    query_index = 0
    update_query_title()

#making the search
def song_search(search_querie):
    results = YoutubeSearch(search_querie, max_results=40).to_dict()
    query_list=[]
    for result in results:    
        query_list.append({
                'url': ''.join([YOUTUBE_BASE_URL, result['url_suffix']]),
                'title': re.sub(NON_CHARS, '', result['title'])
            })
    return(query_list)

#moving through the songlist
def query_prev():
    if query_list:
        global query_index
        query_index-=1
        if query_index < 0:
            query_index =len(query_list) - 1
        update_query_title()

#moving through the songlist
def query_next():
    if query_list:
        global query_index
        query_index += 1
        if query_index == len(query_list):
            query_index = 0
        update_query_title()

def update_query_title():
    song_query.config(state="normal")
    song_query.delete(0, END)
    song_query.insert(0, query_list[query_index]['title'])
    song_query.config(state="disable")
    return

#moving through the songlist
def update_currently_playing(TITLE):
    currently_playing.config(state="normal")
    currently_playing.delete(0, END)
    currently_playing.insert(0, TITLE)
    currently_playing.config(state="disable")
    return

def update_playlist_title():
    playlist_item.config(state="normal")
    playlist_item.delete(0, END)
    try:
        playlist_item.insert(0, playlist[play_index+1]['title'])
    except: 
        playlist_item.insert(0, "")
    playlist_item.config(state="disable")
    return

#this function keeps track of time and moves the timescale
def update_time():
    length = timescale['to']
    place = player.get_time()
    if (length - place) < 10000 and player.is_playing() == 0:
        if shuffle == 1 and len(playlist) > 1:
            random()
            start_new_song(playlist[play_index]['url'])
        elif play_index < (len(playlist) -1): 
            playlist_go()
    elif player.is_playing() == 1:
        time_info =str(datetime.timedelta(seconds = round(place/1000))) + " / " + str(datetime.timedelta(seconds = round(length/1000)))
        time_label.config(text=time_info)
        timescale.set(place)
    win.after(1000,update_time)

def generate_stream_url(URL):
    for i in media_qualities:
        try:
            current_quality_menu.delete(i)
        except:
            continue
    audio = []
    ydl_opts = {"quiet":True }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(URL, download=False)
        formats = info['formats']
        songduration = 1000 * info['duration']
        songtitle = info['title']
        description = "".join([s for s in info['description'].strip().splitlines(True) if s.strip()])
        url_list = []
        counter = -1
        for format in info['formats']:
            video_format = format['format']
            video_format_short = video_format[video_format.find("(")+1:video_format.find(")")] 
            if (video_format[2]==" " or "audio only" in video_format) and not("DASH" in video_format) and not(counter > -1 and video_format_short == url_list[counter]['video_format']):
                url_list.append({
                        'stream_url':format['url'],
                        'video_format':video_format_short
                        })
                if "audio" in video_format:
                    quality_label = f"audio only ({video_format_short})"
                else:
                    quality_label = f"video ({video_format_short})"
                current_quality_menu.add_command(label=quality_label,command=(lambda url = format['url'], title=video_format_short:  set_player(url,title)))
                if counter>-1 and "audio" in video_format and not("audio" in url_list[counter]):
                    prefered_quality_menu.entryconfigure(1, command=(lambda url = format['url']:  set_player(url)))
    
                counter +=1
    
    prefered_quality_menu.entryconfigure(0, command=(lambda url = url_list[len(url_list)-1]['stream_url']:  set_player(url)))
    prefered_quality_menu.entryconfigure(2, command=(lambda url = url_list[0]['stream_url']:  set_player(url)))
    return(url_list, songduration, description, songtitle)

def select_stream(audio):
    break_out_flag = False
    for index in range(prefered_quality):
        if break_out_flag:
            break
        for item in audio:
            if item['video_format'] == media_qualities[prefered_quality-index]:
                url = item['stream_url']
                break_out_flag = True
                break
    return(url)

def set_player(playurl,quality_wish=""):
    global prefered_quality
    if quality_wish!="":
        prefered_quality= media_qualities.index(quality_wish)
    time = player.get_time()
    media=instance.media_new(playurl)
    media.get_mrl()
    player.set_media(media)
    player.play()
    player.set_time(time)
    
#starting the song
def start_new_song(URL):
    if query_list or playlist:
        audio, songduration, description, songtitle = generate_stream_url(URL)
        playurl = select_stream(audio)
        set_player(playurl) 
        description_label.config(state="normal")
        description_label.delete(0, END)
        description_label.insert(0, str(description))
        description_label.config(state="disable")
        pause_button.config(text="||")
        timescale.config(to = songduration)
        timescale.set(0)
        player.set_time(0)
        win.title(songtitle)
        update_currently_playing(songtitle)
        update_playlist_title()
        return

#this is to select the next song in the list
def add_song():
    if query_list:
        playlist.append(query_list[query_index])
        update_playlist_title()

#this function is for downloading the song
def download():
    song_url = query_list[query_index]['url']
    song_title = query_list[query_index]['title']
    outtmpl = song_title + '.%(ext)s'
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': outtmpl,
        'postprocessors': [
            {'key': 'FFmpegExtractAudio','preferredcodec': 'mp3',
             'preferredquality': '192',
            },
            {'key': 'FFmpegMetadata'},
        ],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(YOUTUBE_BASE_URL+ song_url, download=True) 

def random():
    global play_index
    counttemp = play_index
    while counttemp == play_index:
        play_index = random.randrange(len(playlist)-1)
    return

#moving through the scale for time
def timescale_move(timescale_var):
    place = player.get_time()
    if abs(int(timescale_var) - place) > 4000:
        player.set_time(int(timescale_var))

#to pause by keypress (space)
def toggle_pause1(event):
    if str(win.focus_get()) != str(".!entry"):
        toggle_pause2()
    
#to pause by keypress or click
def toggle_pause2():
    pause = player.is_playing()
    player.set_pause(pause)
    pause_button.config(text=["||","▶"][int(pause)])

#import all songs from querie
def all_songs_to_playlist():
    if query_list:
        playlist.extend(query_list)
        update_playlist_title()

#controlling the volume
def change_volume(volume_var):
    player.audio_set_volume(int(volume_var))

#clear playlist
def clear_playlist():
    global playlist
    play_index = 0
    playlist = []
    update_playlist_title()
    return

def save_playlist():
    name = search_box.get()
    if len(playlist) >1 and name != "":
        newrow = [name + "§", playlist]
        with open(os.path.join(sys.path[0], "AntiTubePlaylists.txt"), "a") as f_object:
            writer_object = writer(f_object)
            writer_object.writerow(newrow)
            f_object.close()
        playlist_list_menu.add_command(label=name, command=(lambda playlistt = playlist:  import_playlist(playlistt)))

def playlist_next():
    if playlist:
        global play_index
        if play_index < (len(playlist)-1):
            play_index+=1
        update_playlist_title()

def playlist_prev():
    if playlist:
        global play_index
        if play_index >-1:
            play_index-=1
        update_playlist_title()
        return

def playlist_remove():
    if playlist:
        del playlist[play_index+1]
        playlist_prev()
        update_playlist_title()

def playlist_go():
    if playlist:
        global play_index
        if play_index < (len(playlist)-1):
            play_index+=1
            start_new_song(playlist[play_index]['url'])

def import_playlist(playlist_import):
    global playlist, play_index
    playlist = playlist_import
    play_index = 0
    start_new_song(playlist[play_index]['url'])

def toggle_shuffle():
    global shuffle
    shuffle = not(shuffle)
    on_or_off = ["on","off"][int(shuffle)]
    playlist_menu.entryconfigure(0, label=f"turn {on_or_off} shuffle")

def set_prefered_quality_best_vid():
    global prefered_quality
    prefered_quality=10
    if player.get_time() > 1000:
        select_stream

def set_prefered_quality_best_aud():
    global prefered_quality
    prefered_quality=2

def set_prefered_quality_least_aud():
    global prefered_quality
    prefered_quality=0

main_frame = Frame(win, width = 320, height=600)
main_frame.grid(row=1, column=1, padx=0, sticky='new')
search_frame=Frame(main_frame, width = 150)
search_frame.grid(row=1, column=1, padx=0, sticky='new',rowspan=3)
playlist_frame=Frame(main_frame, width = 150)
playlist_frame.grid(row=1, column=2, padx=0, sticky='new',rowspan=3)
time_frame=Frame(main_frame,width=320)
time_frame.grid(row=4, column=1, padx=0, sticky='new',columnspan=2)
description_frame=Frame(main_frame,width=320, height = 100)
description_frame.grid(row=5, column=1, padx=0, sticky='nesw',columnspan=3, rowspan=4)
playlist_frame.bind('<space>',toggle_pause1)
search_frame.bind('<space>',toggle_pause1)
search_frame.bind("<Button-1>", lambda event: playlist_frame.focus_set())
playlist_frame.bind("<Button-1>", lambda event: playlist_frame.focus_set())
time_frame.bind("<Button-1>", lambda event: playlist_frame.focus_set())
search_box = Entry(search_frame)
search_box.pack(side='top',anchor = "w")
search_box.bind('<Return>', query_songs)
song_query = Entry(search_frame,state = DISABLED)
song_query.pack(side='top',anchor = "w")
currently_playing = Entry(playlist_frame,state = DISABLED)
currently_playing.pack(side='top',anchor = "w")
playlist_item = Entry(playlist_frame,state = DISABLED)
playlist_item.pack(side='top',anchor = "w")
volume_scale = Scale(main_frame, from_=200, to=0, orient=VERTICAL, variable = volume_var, showvalue=0, command = change_volume)
volume_scale.set(100)
volume_scale.grid(row=1, column=3, padx=0, sticky='nsew',rowspan=4)
pause_button= Button(time_frame, text = "||", command =toggle_pause2)
pause_button.pack(side='left')
button_dict = [
    Button(playlist_frame, text = "←",command = playlist_prev),
    Button(playlist_frame, text = "→",command = playlist_next),
    Button(playlist_frame, text = "X",command = playlist_remove),
    Button(playlist_frame, text = "OK",command = playlist_go),
    Button(search_frame, text = "←",command = query_prev),
    Button(search_frame, text = "→",command = query_next),
    Button(search_frame, text = "OK", command =(lambda:  start_new_song(query_list[query_index]['url']))),
    Button(search_frame, text = "+", command = add_song),
    Button(search_frame, text = "↓", command =download)
    ]
for button in button_dict:
    button.pack(side='left')
    button.bind("<Button-1>", lambda event: playlist_frame.focus_set())

time_label = Label(time_frame, text = "0:00:00 / 0:00:00")
timescale = Scale(time_frame, from_=0, to=1000, orient=HORIZONTAL, length=267,variable = timescale_var, showvalue=0, command = timescale_move)
description_label = Entry(description_frame, state = DISABLED)
description_label.pack(side='top',anchor = "w",fill=BOTH)
time_label.pack(side='left')
timescale.pack(side='left')
menubar = Menu(win)
playlist_menu = Menu(menubar, tearoff=0)
playlist_list_menu = Menu(menubar, tearoff=0)
playlist_menu.add_command(label="shuffle on",command=toggle_shuffle)
playlist_menu.add_command(label="all results to playlist", command=all_songs_to_playlist)
playlist_menu.add_command(label="clear playlist", command=clear_playlist)
playlist_menu.add_command(label="save playlist", command=save_playlist)
quality_menu = Menu(menubar, tearoff=0)
current_quality_menu = Menu(menubar, tearoff=0)
prefered_quality_menu = Menu(menubar, tearoff=0)
prefered_quality_menu.add_command(label="best video format", command=set_prefered_quality_best_vid)
prefered_quality_menu.add_command(label="best audio format", command=set_prefered_quality_best_aud)
prefered_quality_menu.add_command(label="least audio format", command=set_prefered_quality_least_aud)
try:
    with open(os.path.join(sys.path[0], "AntiTubePlaylists.txt"), "r") as playlist_file:
        csv_reader = csv.reader(playlist_file,  delimiter='§')
        for row in csv_reader:
            try:
                s = row[1][2:][:-1].replace("'",'"')
                playlist_import = json.loads(s)
                playlist_list_menu.add_command(label=row[0], command=(lambda playlist_import = playlist_import:  import_playlist(playlist_import)))
            except:
                continue
except:
    pass
menubar.add_cascade(label="Playlists", menu=playlist_menu)
menubar.add_cascade(label="Quality", menu=quality_menu)
quality_menu.add_cascade(label="Set prefered quality", menu=prefered_quality_menu)
quality_menu.add_cascade(label="Set current song quality", menu=current_quality_menu)
playlist_menu.add_cascade(label="Playlists", menu=playlist_list_menu)
win.config(menu=menubar)
search_box.focus()
if __name__ == '__main__':
    update_time()
win.mainloop()
