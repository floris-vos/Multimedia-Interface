# gui-youtube-player

![Screenshot from 2023-02-28 23-06-13](https://user-images.githubusercontent.com/121669504/221992385-2d19a9ee-f2bc-49ee-8ea3-2ea998219c7c.png)

For watching videos from 5 streaming websites, including a very basic google search function

With this tool, one can search videos for:

-Youtube -Dailymotion -Vimeo -Odysee -Archive.org

And display them. For YT, DM, and Vimeo, the streaming happens through Yt-Dlp, the other two just have the relevant urls on the page, gotten with requests.

There is a very basic google search function. It only show the p, h and pre tags of the body of websites. Which is in fact very nice, for informative websites it is sufficient. With optional JS rendering, though as of yet the JS rendering is not optimal, because of trouble in the HTMLsession library.

There will be some problems in Windows with scrolling. Also the "xwindow" command should be changed to "hwnd" for windows. 
