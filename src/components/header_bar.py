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
import os

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject


class HeaderBarComponent(Gtk.HeaderBar):
    def __init__(self, window):
        """
        Provides
        :param window: Main application window reference, serves as communication hub
        """
        super(Gtk.HeaderBar, self).__init__()
        self.set_show_close_button(True)
        # Set default window title
        self.props.title = _("Easy eBook Viewer")
        self.__window = window
        self.__menu = Gtk.Menu()

        """
        Adds all default Header Bar content and connects handlers
        """

        # Adds open eBook button
        self.open_button = Gtk.Button()
        document_open_image = Gtk.Image.new_from_icon_name("document-open-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.open_button.add(document_open_image)
        self.open_button.connect("clicked", lambda button: self.emit('open_clicked'))
        self.pack_start(self.open_button)

        # Adds linked Gtk.Box to host chapter navigation Entries
        self.pages_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(self.pages_box.get_style_context(), "linked")

        # Left current page Entry
        self.current_page_entry = Gtk.Entry()
        self.current_page_entry.set_text("0")
        try:
            self.current_page_entry.set_max_width_chars(3)
        except AttributeError:
            self.current_page_entry.set_max_length(3)
            print("Gtk-WARNING **: GTK+ ver. below 3.12 will cause application interface to misbehave")
        self.current_page_entry.set_width_chars(3)
        self.current_page_entry.connect("activate", self.__on_activate_current_page_entry)
        self.pages_box.pack_start(self.current_page_entry, False, False, 0)
        # Right of all pages Entry
        self.number_pages_entry = Gtk.Entry()
        self.number_pages_entry.set_placeholder_text(_("of 0"))
        self.number_pages_entry.set_editable(False)
        try:
            self.number_pages_entry.set_max_width_chars(len(_("of 0"))+2)
        except AttributeError:
            self.number_pages_entry.set_max_length(len(_("of 0"))+2)
            print("Gtk-WARNING **: GTK+ ver. below 3.12 will cause application interface to misbehave")
        self.number_pages_entry.set_width_chars(len(_("of 0"))+2)
        self.number_pages_entry.set_can_focus(False)
        self.pages_box.pack_end(self.number_pages_entry, False, False, 0)
        self.pack_start(self.pages_box)

        # Adds linked Gtk.Box to host chapter navigation buttons
        navigation_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        Gtk.StyleContext.add_class(navigation_box.get_style_context(), "linked")

        # Adds left arrow chapter navigation button
        self.left_arrow_button = Gtk.Button()
        self.left_arrow_button.add(Gtk.Arrow(Gtk.ArrowType.LEFT, Gtk.ShadowType.NONE))
        self.left_arrow_button.set_sensitive(False);
        self.left_arrow_button.connect("clicked", self.__on_left_arrow_clicked)
        navigation_box.add(self.left_arrow_button)

        # Adds right arrow chapter navigation button
        self.right_arrow_button = Gtk.Button()
        self.right_arrow_button.add(Gtk.Arrow(Gtk.ArrowType.RIGHT, Gtk.ShadowType.NONE))
        self.right_arrow_button.set_sensitive(False);
        self.right_arrow_button.connect("clicked", self.__on_right_arrow_clicked)
        navigation_box.add(self.right_arrow_button)

        self.pack_start(navigation_box)

        # Adds show chapters index toggle button
        self.show_index_button = Gtk.ToggleButton()
        index_icon = Gtk.Image.new_from_icon_name("view-list-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.show_index_button.add(index_icon)
        self.show_index_button.connect("toggled", lambda button: self.emit('navigation_toggled', button.get_active()))
        self.pack_start(self.show_index_button)

        # Adds Preferences context settings menu item
        preferences_menu_item = Gtk.MenuItem(_("Preferences"))
        preferences_menu_item.connect("activate", lambda item: self.emit("preferences_clicked"))
        self.__menu.append(preferences_menu_item)

        # Adds About context settings menu item
        about_menu_item = Gtk.MenuItem(_("About"))
        about_menu_item.connect("activate", lambda item: self.emit("about_clicked"))
        self.__menu.append(about_menu_item)

        self.__menu.show_all()

        # Adds settings menu button
        self.properties_button = Gtk.Button()
        document_properties_image = Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.SMALL_TOOLBAR)
        self.properties_button.add(document_properties_image)
        self.properties_button.connect("clicked", self.__on_properties_clicked)
        self.pack_end(self.properties_button)

    def __on_properties_clicked(self, button):
        """
        Handles settings button clicked event and displays context menu
        :param button:
        """
        self.__menu.popup(None, button, None, button, 0, Gtk.get_current_event_time())

    def __on_right_arrow_clicked(self, button):
        """
        Handles Right Arrow clicked navigation event, moves one chapter to the right
        :param button:
        """
        self.__attempt_change_chapter(self.selected_chapter + 1)

    def __on_left_arrow_clicked(self, button):
        """
        Handles Left Arrow clicked navigation event, moves one chapter to the left
        :param button:
        """
        self.__attempt_change_chapter(self.selected_chapter - 1)

    def __on_activate_current_page_entry(self, widget):
        """
        Handles enter key on current page entry and validates what user set and loads that chapter
        :param wiget:
        :param data:
        """
        try:
            chapter_number = int(widget.get_text()) - 1
            self.__attempt_change_chapter(chapter_number)
        except ValueError:
            self.__attempt_change_chapter(-1) # this will reset the value in the box

    def __attempt_change_chapter(self, chapter_number):
        if self.chapter_count > chapter_number >= 0:
            self.selected_chapter = chapter_number
            self.current_page_entry.set_text(str(chapter_number + 1))
            self.left_arrow_button.set_sensitive(chapter_number != 0)
            self.right_arrow_button.set_sensitive(chapter_number != self.chapter_count-1)
            self.emit("chapter_changed", chapter_number)
            return True
        else:
            self.current_page_entry.set_text(str(self.selected_chapter + 1))
            return False

    # Updates the chapter in the bar. This will not cause a 'chapter_changed' signal to be emitted.
    def select_chapter(self, chapter_number):
        """
        Updates current chapter in entry if navigation came from somewhere else
        :param i:
        """
        self.selected_chapter = chapter_number
        self.left_arrow_button.set_sensitive(chapter_number != 0)
        self.right_arrow_button.set_sensitive(chapter_number != self.chapter_count-1)
        self.current_page_entry.set_text(str(chapter_number + 1))

    def set_chapter_count(self, n):
        """
        Sets text of "maximum" chapter entry ie. of X
        :param i:
        """
        self.chapter_count = n
        self.number_pages_entry.set_placeholder_text(_("of %s") % (str(n)))

    def show_jumping_navigation(self):
        """
        Enables entry based navigation, to be used when book is loaded
        """
        self.pages_box.show()

    def hide_jumping_navigation(self):
        """
        Disables entry based navigation, to be used when no book is loaded
        """
        self.pages_box.hide()

GObject.type_register(HeaderBarComponent)
# We register a bunch of custom signals for this class:
# emitted when the user choose a different chapter in the header bar.
GObject.signal_new("chapter_changed", HeaderBarComponent, GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [GObject.TYPE_INT])
# emitted when user clicks the 'open' button
GObject.signal_new("open_clicked", HeaderBarComponent, GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [])
# emitted when user clicks 'about' option in menu
GObject.signal_new("about_clicked", HeaderBarComponent, GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [])
# emitted when user clicks 'preferences' option in menu
GObject.signal_new("preferences_clicked", HeaderBarComponent, GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [])
# emitted when 'show navigation' is toggled
GObject.signal_new("navigation_toggled", HeaderBarComponent, GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [GObject.TYPE_BOOLEAN])
