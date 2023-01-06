# gui-youtube-player
![Screenshot from 2022-12-30 14-09-37](https://user-images.githubusercontent.com/121669504/210073639-b2aad203-f4db-4743-a6be-03c64ebf874c.png)

This is a multimedia player that gets its material from the database of www.youtube.com. 
It can play audio only (the original concept of this program), but can play video as well. 
Selecting such preferences happens under the menu „quality“.
It‘s also possible to make playlists, which can be saved in a csv file. 

The code as it is now is – I think – a pretty good base for further development. Points of which I know that they need development are:
-the csv module („filehandler“). The functions are very inefficient and complex. They could be reduced to just a reader and a writer, and in between some manipulation that just works on the material that has been read. 
-more generally, the work with importing and exporting playlists has been made a bit sloppily. 

In coding this, I developped a few principles:
„one-way-dependancy“: classes should only refer to their functions and atttributes, so that they can be imported anywhere, without being dependant on the class that imports them. 
„mono-functionality“: classes should have one function only, which can be tested by looking for a singular word (be it a neologism) to describe the function of the class. 
„terminological homogenity“: more of a pedantic thing, but for this project I tried to find terms that all have a Latin etymology, to give descriptions to objects. 

I didn‘t keep my own rules 100%, but know I could correct a few things to change that. And I think that these rules are a good precondition for readable and usable code. 
