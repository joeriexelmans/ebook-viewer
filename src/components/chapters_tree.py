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
from gi.repository import Gtk
from gi.repository import Pango
from gi.repository import GObject


class ChaptersTreeComponent(Gtk.TreeView):
    def __init__(self):
        """
        Provides the List Box with chapters index and navigation based around them
        :param window: Main application window reference, serves as communication hub
        """
        super(Gtk.TreeView, self).__init__()

        model = Gtk.TreeStore(GObject.TYPE_STRING, GObject.TYPE_PYOBJECT)
        self.set_model(model)
        selection = self.get_selection()
        # Only one chapter can be selected at a time
        selection.set_mode(Gtk.SelectionMode.SINGLE)
        selection.connect('changed', self.__on_selection_changed)
        self.ignore_next_selection_signal = False

        # Helpers for finding the right Treeiter by chapter number and chapter anchor
        self.chapter_number_to_iter = {}
        self.chapter_anchor_to_iter = {}

        self.append_column(Gtk.TreeViewColumn("Navigation", Gtk.CellRendererText(), text=0))


    def reload_treeview(self, index):
        """
        Reloads all List Box element by first removing them and then calling __populate_treeview()
        """
        children = self.get_children()
        for element in children:
            self.remove(element)

        for child in index.children:
            self.__populate_recursive(child, None)
        self.show_all()

    def __populate_recursive(self, navpoint, parent_treeiter):
        model = self.get_model()
        treeiter = model.append(parent_treeiter, [navpoint.text, navpoint])
        self.chapter_anchor_to_iter[navpoint.content] = treeiter
        if navpoint.file_number not in self.chapter_number_to_iter:
            self.chapter_number_to_iter[navpoint.file_number] = treeiter
        for child in navpoint.children:
            self.__populate_recursive(child, treeiter)

    # Check if an item for the given URI is present and select it.
    # If no such item exists, the selection will be cleared.
    # No 'chapter_changed' signal will be emitted as a result of this call.
    def select_uri(self, uri):
        found = False
        for chapter_anchor in self.chapter_anchor_to_iter:
            if uri.endswith(chapter_anchor):
                self.__set_selection(self.chapter_anchor_to_iter[chapter_anchor])
                found = True
                break
        if not found:
            self.__set_selection(None)


    # Check if an item for the given chapter number is present and select it.
    # If no such item exists, the selection will be cleared.
    # No 'chapter_changed' signal will be emitted as a result of this call.
    def select_chapter(self, chapter_number):
        """
        Called during navigation sets current chapter based on reader position
        :param chapter: integer with chapter number
        """
        if chapter_number in self.chapter_number_to_iter:
            treeiter = self.chapter_number_to_iter[chapter_number]
            self.__set_selection(treeiter)
        else:
            self.__set_selection(None)

    # Helper for setting the selection.
    # Expands the items in the view such that the selected item is visible,
    # and makes sure that we don't respond to the selection 'changed' signal by emitting a 'chapter_changed'
    def __set_selection(self, treeiter):
        self.ignore_next_selection_signal = True

        if treeiter:
            parentiter = self.get_model().iter_parent(treeiter)
            if parentiter:
                treepath = self.get_model().get_path(parentiter)
                self.expand_to_path(treepath)
            self.get_selection().select_iter(treeiter)
        else:
            self.get_selection().unselect_all()

    # Handler for selection changed signal
    def __on_selection_changed(self, selection):
        if self.ignore_next_selection_signal:
            self.ignore_next_selection_signal = False
            return

        model, paths = selection.get_selected_rows()
        if len(paths) == 1:
            path = paths[0]
            navpoint = model.get_value(model.get_iter(path), 1)
            self.emit("chapter_changed", navpoint.file_number, navpoint)

# Register a signal for our component
# The 'chapter_changed' signal is emitted as the result of a user clicking on an item in the view
GObject.type_register(ChaptersTreeComponent)
GObject.signal_new("chapter_changed", ChaptersTreeComponent, GObject.SIGNAL_RUN_LAST, GObject.TYPE_NONE, [GObject.TYPE_INT, GObject.TYPE_PYOBJECT])
