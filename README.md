This is a fork from the now-dead project https://github.com/michaldaniel/ebook-viewer

# Why this fork?

Even in the light of the awful code quality of the original application, I liked the simplicity of the interface a lot. No other Linux EPUB reader could beat it, in my opinion.
 - Some readers have too many features (like a "book library" in Calibre and Bookworm).
 - Others are completely outdated or have an ugly, difficult to use interface (FBreader)

# Changes made

 - Chapter data is correctly shown in a tree view (as opposed to a list view). Evidence:

![Icon](https://i.imgur.com/0Q1O3qj.png)

 - Overall improvement of code quality (more cohesion and less coupling and all that). But still pretty bad.
 - CSS background set to non-transparent. The transparent background didn't work if your GTK theme doesn't have a 'light' and a 'dark' version. So the CSS for 'day' and 'night' has been edited to have a non-transparent background.
 - CSS left and right margins are proportional to the width of the view. This gives a nicer result in my opinion.
 - Removed restoring the 'scroll' after restarting the application. I could not get this to work in a stable way. So now after restarting, the same book and chapter are shown, but the view will be at the top of the page again.

Tested with a bunch of EPUBs.

The result is quite a usable minimal application that I use myself for reading EPUBs on my computer.

Further "planned" improvements (but no promises here)
 - Remove functionality for opening MOBI files (it's implemented by secretly starting another converter program in the background, this is just cheating!!)
 - There's "import" and "open", no idea what the difference is, I've never imported anything, I'm only interested in opening.
 - Port to WebKitGTK 2 (shouldn't be too hard)
 - Throw everything away and build from scratch in Haskell

Also, pull requests welcome :-)