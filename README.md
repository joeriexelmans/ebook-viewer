![Icon](https://cloud.githubusercontent.com/assets/1345297/18609855/7f6c13b2-7d0c-11e6-9fc7-0a23a251d2ea.png)

# easy-ebook-viewer
Modern GTK Python app to easily read ePub files

Ebook Viewer is currently in early stages of development. It's a re-write of old ebook reader called [pPub.](https://github.com/sakisds/pPub)

Planned for first public release:
- [x] ePub opening & display
- [x] Basic chapter navigation
- [x] Restoring of reading position
- [ ] Importing from other ebook file formats
- [x] Chapter jumping
- [x] Chapter index based navigation
- [ ] Per book bookmarks
- [ ] Switching between light and dark style
- [ ] Text size control

Future plans:
- [ ] eBook font picker
- [ ] Content searching
- [ ] Pernament highlighting
- [ ] Book metadata display
- [ ] Ability to edit book metadata

## Installing

**Requires**: gir1.2-webkit-3.0, gir1.2-gtk-3.0, python3-gi (PyGObject for Python 3)

Download or clone this repository then run in project directory:

```sudo make install```

Note the lack of configure step so make sure you have all dependencies.

## Screenshots

Dark theme

![Dark theme](https://cloud.githubusercontent.com/assets/1345297/19221520/4357d038-8e45-11e6-849b-d83a9fe496ba.png)

Light theme

![Light theme](https://cloud.githubusercontent.com/assets/1345297/19221521/43b2f698-8e45-11e6-839c-e9c41ab0aea6.png)
