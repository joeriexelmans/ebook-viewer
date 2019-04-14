#!/usr/bin/env python3

# Easy eBook Viewer by Michal Daniel

# Easy eBook Viewer is free software; you can redistribute it and/or modify it under the terms
# of the GNU General Public Licence as published by the Free Software Foundation.

# Easy eBook Viewer is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE.  See the GNU General Public Licence for more details.

# You should have received a copy of the GNU General Public Licence along with
# Easy eBook Viewer; if not, write to the Free Software Foundation, Inc., 51 Franklin Street,
# Fifth Floor, Boston, MA 02110-1301, USA.
import threading
import constants
import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject
from components import header_bar, viewer, chapters_tree
from workers import config_provider as config_provider_module, content_provider as content_provider_module
import sys
import os
from pathlib import Path


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, file_path=None):
        # Creates Gtk.Window and sets parameters
        Gtk.Window.__init__(self)
        self.set_border_width(0)
        self.set_default_size(800, 800)
        self.connect("destroy", self.__on_exit)
        self.connect("key-press-event", self.__on_keypress_viewer)
        self.job_running = False

        # Use panned to display book on the right and toggle chapter & bookmarks on the left
        self.paned = Gtk.Paned.new(Gtk.Orientation.HORIZONTAL)
        self.add(self.paned)

        # Gets application config from ConfigProvider
        try:
            self.config_provider = config_provider_module.ConfigProvider()
        except:
            # Could not save configuration file
            # TODO: Migrate to custom dialog designed in line with elementary OS Human Interface Guidelines
            error_dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.ERROR, Gtk.ButtonsType.OK,
                                             _("Could not write configuration file."))
            error_dialog.format_secondary_text(_("Make sure $XDG_CONFIG_HOME/easy-ebook-viewer.conf is accessible and try again."))
            error_dialog.run()
            exit()

        # Gets application content from ContentProvider
        self.content_provider = content_provider_module.ContentProvider(self)

        # Creates and sets HeaderBarComponent that handles and populates Gtk.HeaderBar
        self.header_bar_component = header_bar.HeaderBarComponent(self)
        self.header_bar_component.connect("chapter_changed", self.__on_header_bar_chapter_changed)
        self.set_titlebar(self.header_bar_component)

        # Prepares scollable window to host WebKit Viewer
        self.right_scrollable_window = Gtk.ScrolledWindow()
        self.right_scrollable_window.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        # self.right_scrollable_window.get_vscrollbar().connect("show", self.__restore_scroll_position)
        self.right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.paned.pack2(self.right_box, True, True)  # Add to right panned

        # Prepares scollable window to host Chapters and Bookmarks
        self.left_scrollable_window = Gtk.ScrolledWindow()
        self.left_scrollable_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        # Don't show it after startup ie. don't pack it to self.panned
        self.is_paned_visible = False;

        # Adds WebKit viewer component from Viewer component

        self.viewer = viewer.Viewer(self, self.right_scrollable_window)
        print("Displaying blank page.")
        self.viewer.load_uri("about:blank")  # Display a blank page
        # self.viewer.connect("load-finished", self.__on_viewer_load_finished)
        self.viewer.connect("chapter_changed", self.__on_viewer_chapter_changed)
        self.right_box.pack_end(self.right_scrollable_window, True, True, 0)
        # Create Chapters List component and pack it on the left
        self.chapters_tree_component = chapters_tree.ChaptersTreeComponent()
        self.chapters_tree_component.connect("chapter_changed", self.__on_treeview_chapter_changed)

        self.right_scrollable_window.add(self.viewer)

        self.left_scrollable_window.add(self.chapters_tree_component)

        self.spinner = Gtk.Spinner()
        self.spinner.set_margin_top(50)
        self.spinner.set_size_request(50, 50)

        # Update WebView and light / dark GTK style theme according to settings
        self.__update_night_day_style()

        # Create context menu for right click
        self.menu = Gtk.Menu()
        menu_item = Gtk.MenuItem("Copy")
        menu_item.connect("activate", self.__on_copy_activate)
        self.menu.append(menu_item)
        self.menu.show_all()

        # Initial book load

        self.book_loaded = False
        # If book came from arguments ie. was oppened using "Open with..." method etc.
        if file_path is not None:
            # Load new book
            self.load_book(sys.argv[1])
            self.book_loaded = True
        else:
            # Reload last book
            if "lastBook" in self.config_provider.config['Application']:
                last_book_file = Path(self.config_provider.get_last_book())
                if last_book_file.is_file():
                    # Load new book
                    self.load_book(self.config_provider.get_last_book())
                    self.book_loaded = True

    @property
    def __scroll_position(self):
        """
        Returns position of scroll in Scrollable Window
        :return:
        """
        return self.right_scrollable_window.get_vadjustment().get_value()

    def __load_chapter_pos(self):
        """
        Return chapter position obtained from config provider
        """
        self.load_chapter(int(self.config_provider.config[self.content_provider.book_md5]["chapter"]))

    def __on_exit(self, window, data=None):
        """
        Handles application exit and saves all unsaved config data to file
        :param window:
        :param data:
        """

        # Save book data
        if self.content_provider.status:
            self.config_provider.save_chapter_position(self.content_provider.book_md5,
                                                       self.current_chapter,
                                                       self.__scroll_position)

    # There are 4 ways a navigation action can be initiated:
    #
    #  1. The ChaptersTreeComponent emitting a 'chapter_changed' event
    #      -> when the user selects a different chapter
    #  2. The HeaderBarComponent emitting a 'chapter_changed' event
    #      -> when the left/right button is clicked in the header bar, or
    #      -> when a new chapter number is entered followed by 'enter'
    #  3. The Viewer emitting a 'chapter_changed' event
    #      -> when the user clicks a link
    #  4. By pressing the Left/Right arrow keys on the keyboard
    #
    # The handlers for those events are below:

    def __on_header_bar_chapter_changed(self, header_bar, chapter_number):
        chapter_file = self.content_provider.get_chapter_file_path(chapter_number)
        self.chapters_tree_component.select_chapter(chapter_number)
        self.viewer.load_path(chapter_file)
        self.current_chapter = chapter_number

    def __on_treeview_chapter_changed(self, treeview, chapter_number, navpoint):
        chapter_file = self.content_provider.complete_chapter_file_path(navpoint.content)
        self.header_bar_component.select_chapter(navpoint.file_number)
        self.viewer.load_path(chapter_file)
        self.current_chapter = navpoint.file_number

    def __on_viewer_chapter_changed(self, viewer, uri):
        if not uri == "about:blank":
            chapter_number = self.content_provider.uri_to_chapter(uri)
            self.header_bar_component.select_chapter(chapter_number)
            self.chapters_tree_component.select_uri(uri)
            self.current_chapter = chapter_number

    def __on_keypress_viewer(self, wiget, data):
        """
        Handles Left and Right arrow key presses
        :param wiget:
        :param data:
        """
        if self.content_provider.status:
            chapter = -1
            key_value = Gdk.keyval_name(data.keyval)
            if key_value == "Right":
                chapter = self.current_chapter + 1
                if chapter >= self.content_provider.chapter_count:
                    return
            elif key_value == "Left":
                chapter = self.current_chapter - 1
                if chapter < 0:
                    return
            else:
                return

        self.header_bar_component.select_chapter(chapter)
        self.chapters_tree_component.select_chapter(chapter)
        chapter_file = self.content_provider.get_chapter_file_path(chapter)
        self.viewer.load_path(chapter_file)
        self.current_chapter = chapter

    def __update_night_day_style(self):
        """
        Sets GTK theme and Viwer CSS according to application settings
        """
        self.settings = Gtk.Settings.get_default()
        if self.config_provider.config["Application"]["stylesheet"] == "Day":
            self.viewer.set_style_day()
            self.settings.set_property("gtk-application-prefer-dark-theme", False)
        else:
            self.viewer.set_style_night()
            self.settings.set_property("gtk-application-prefer-dark-theme", True)

    def __on_copy_activate(self, widget):
        """
        Provides dirty clipboard hack to get selection from inside of WebKit
        :param widget:
        """
        primary_selection = Gtk.Clipboard.get(Gdk.SELECTION_PRIMARY)
        selection_clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        # It does wait some short time for that text, it seems to update every now and then
        # Can get selection from anywhere in the system, no real way to tell
        selection_clipboard.set_text(primary_selection.wait_for_text(), -1)

    def __show_left_paned(self):
        """
        Shows left paned panel
        """
        self.paned.pack1(self.left_scrollable_window, False, False)  # Add to right panned
        self.paned.show_all()

    def __remove_left_paned(self):
        """
        Hides left paned panel
        """
        self.paned.remove(self.left_scrollable_window)
        self.paned.show_all()

    def __bg_import_book(self, filename):
        self.filename = filename
        os.system("ebook-convert \"" + filename + "\" /tmp/easy-ebook-viewer-converted.epub --pretty-print")
        self.job_running = False

    def __check_on_work(self):
        if not self.job_running:
            self.__continue_book_loading("/tmp/easy-ebook-viewer-converted.epub")
            return 0
        return 1

    def __continue_book_loading(self, filename):
        self.spinner.stop()
        self.viewer.show()
        self.right_box.remove(self.spinner)
         # Try to load book, returns true when book loaded without errors
        if self.content_provider.prepare_book(filename):
            # If book loaded without errors

            # Update chapter list
            self.chapters_tree_component.reload_treeview(self.content_provider.index)

            # Load recent chapter and scroll
            recent_chapter = int(self.config_provider.config[self.content_provider.book_md5]["chapter"])
            recent_scroll = float(self.config_provider.config[self.content_provider.book_md5]["position"])

            recent_file = self.content_provider.files[recent_chapter]
            recent_path = self.content_provider.complete_chapter_file_path(recent_file)

            self.current_chapter = recent_chapter
            self.header_bar_component.set_chapter_count(self.content_provider.chapter_count)
            self.header_bar_component.select_chapter(recent_chapter)
            self.chapters_tree_component.select_chapter(recent_chapter)
            self.viewer.load_path(recent_path, recent_scroll)

            # Open book on viewer
            self.header_bar_component.set_title(self.content_provider.book_name)
            self.header_bar_component.set_subtitle(self.content_provider.book_author)

            # Show to bar pages jumping navigation
            self.header_bar_component.show_jumping_navigation()

            self.config_provider.save_last_book(self.filename)
        else:
            # If book could not be loaded display dialog
            # TODO: Migrate to custom dialog designed in line with elementary OS Human Interface Guidelines
            error_dialog = Gtk.MessageDialog(self, 0, Gtk.MessageType.WARNING, Gtk.ButtonsType.OK,
                                             _("Could not open the book."))
            error_dialog.format_secondary_text(
                _("Make sure you can read the file and the book you are trying to open is in supported format and try again."))
            error_dialog.run()
            error_dialog.destroy()

    def load_book(self, filename):
        """
        Loads book to Viwer and moves to correct chapter and scroll position
        :param filename:
        """
        self.spinner.start()
        self.viewer.hide()
        self.right_box.add(self.spinner)
        self.filename = filename
        if not filename.upper().endswith(tuple(constants.NATIVE)):
            convert_thread = threading.Thread(target=self.__bg_import_book, args=(filename,))
            self.job_running = True
            convert_thread.start()
            GObject.timeout_add(100, self.__check_on_work)
        else:
            self.__continue_book_loading(filename)

    def show_menu(self):
        """
        Displays right click context menu
        """
        if self.content_provider.status:
            self.menu.popup(None, None, None, None, 0, Gtk.get_current_event_time())

    def toggle_left_paned(self):
        """
        Shows and hides left paned panel depending on it's current state
        """
        if self.is_paned_visible:
            self.__remove_left_paned()
            self.is_paned_visible = False
        else:
            self.__show_left_paned()
            self.is_paned_visible = True
