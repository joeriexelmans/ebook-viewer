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

import gi

gi.require_version('Gtk', '3.0')
gi.require_version('WebKit', '3.0')
from gi.repository import GObject
from gi.repository import WebKit


class Viewer(WebKit.WebView):
    def __init__(self, window, scrollable):
        """
        Provides Webkit WebView element to display ebook content
        :param window: Main application window reference, serves as communication hub
        """
        WebKit.WebView.__init__(self)

        # Allow transparency so we can use GTK theme as background
        # Can be overridden by CSS background property, needs to be rgba(0,0,0,0)
        self.set_transparent(True)

        # Sets WebView settings for ebook display
        # No java script etc.
        self.set_full_content_zoom(True)
        settings = self.get_settings()
        settings.props.enable_scripts = False
        settings.props.enable_plugins = False
        settings.props.enable_page_cache = False
        settings.props.enable_java_applet = False
        try:
            settings.props.enable_webgl = False
        except AttributeError:
            pass

        # Disable default menu: contains copy and reload options
        # Reload messes with custom styling, doesn't reload CSS
        # App is using own "copy" right click hack
        # It will allow in future to add more options on right click
        settings.props.enable_default_context_menu = False

        settings.props.enable_html5_local_storage = False

        self.connect('context-menu', self.callback)
        self.connect('load-finished', self.__on_load_finished)
        self.ignore_next_load_finished_signal = False

        self.scrollable = scrollable
        self.scroll_to_set = None

        self.__window = window

    # Load a file in the view. Will not cause a 'chapter_changed' event to be emitted.
    def load_path(self, path, scroll_to_set = None):
        self.ignore_next_load_finished_signal = True
        if scroll_to_set:
            self.scroll_to_set = scroll_to_set
        try:
            file = path.split('#')[0]
            with open(file) as file_open:
                self.load_html_string(file_open.read(), "file://" + path)
                print("Loaded: " + path)
        except IOError:
            print("Could not read: ", path)


    def set_style_day(self):
        """
        Sets style to day CSS
        """
        settings = self.get_settings()
        settings.props.user_stylesheet_uri = "file:///usr/share/easy-ebook-viewer/css/day.css"
        # TODO: Prefix location of day.css so it can be set during install

    def set_style_night(self):
        """
        Sets style to night CSS
        """
        settings = self.get_settings()
        settings.props.user_stylesheet_uri = "file:///usr/share/easy-ebook-viewer/css/night.css"
        # TODO: Prefix location of night.css so it can be set during install

    def callback(self, webview, context_menu, hit_result_event, event):
        self.__window.show_menu()

    def __on_load_finished(self, webview, event):
        # Currently disabled, wasn't stable:
        #
        # if self.scroll_to_set:
        #     print("setting scroll")
        #     old_adjustment = self.scrollable.get_vadjustment()
        #     old_adjustment.set_value(float(self.scroll_to_set))
        #     print("scroll set to")
        #     print(old_adjustment.get_value())
        #     # self.scrollable.set_vadjustment(old_adjustment)
        #     self.scroll_to_set = None

        if self.ignore_next_load_finished_signal:
            self.ignore_next_load_finished_signal = False
        else:
            self.emit('chapter_changed', event.get_uri())

# The 'chapter_changed' signal is emitted when the user navigated to a different page by clicking on a link.
GObject.type_register(Viewer)
GObject.signal_new("chapter_changed", Viewer, GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [GObject.TYPE_STRING])