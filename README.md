This is a fork from the now-dead project https://github.com/michaldaniel/ebook-viewer

# Why this fork?

What I liked about the original application is the simplicity of the interface. An EPUB is just a ordered list of HTML files and the original application just displayed those files and let you navigate between them with a side panel. Other Linux EPUB readers typically try to do too much and get "in the way":
 - In Calibre, there's no way to just open a file and read it. You have to import it into your library, as a result the file actually gets copied to another folder, etc.
 - Bookworm is simpler but there is no way to show the book and navigation at the same time. Also, too many animations.
 - FBreader is outdated (hasn't seen development in like 10 years) and also, no navigation panel.
 - It looks like Evince (GNOME's PDF reader) is getting simple EPUB support along the lines of this application. But it doesn't quite look 'finished' and I don't want to dive in the codebase of an application that has been around for so long.

# Changes made

 - Chapter data is correctly parsed from the EPUB and is shown in a tree view (as opposed to a list view). Evidence:

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

Also, pull requests welcome, as long as you maintain the perspective of keeping the application really simple and minimal.