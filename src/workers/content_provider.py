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


import functools
import hashlib
import os
import shutil
import urllib
import zipfile
import itertools

from workers.xml2obj import *

# What happens here is:
# 1. Read META-INF/container.xml that every ePub should have
# 2. From META-INF/container.xml get path to OPF file
# 3. From OPF file read every application/xhtml+xml file path and save them temporarily in self.chapter_links
# 4. From OPF file read book metadata
# 5. From OPF file read NCX file location
# 6. From NCX file read chapter list and chapter ordering
# 7. Save chapter list in self.titles with titles and path to files
# 8. Sort chapter titles and chapter links according to read ordering
# 9. Compare list from NCX with OPF list and append not chaptered files
# Every file path is created like this: path to tmp folder + path to OPF file location + path to file read from OPF/NCX
# Bonus: do bunch of other stuff like setting data based on uri, telling when book loaded etc.


# Takes a 'navPoint' node (or a 'navMap' node) returned by xml2obj and recursivly constructs a hierarchy of NavPoints
class NavPoint:
    def __init__(self, files, node, prev_sibling=None):
        self.files = files
        if node.navLabel and node.content:
            self.text = node.navLabel.text          # e.g.: "Chapter 8. Overlapping Input/Output"
            self.content = node.content.src         # e.g.: "Text/ch15.html#part3"
            self.file = self.content.split('#')[0]  # e.g.: "Text/ch15.html"
            self.has_anchor = len(self.content.split('#')) > 1
            self.file_number = self.files.index(self.file)
        else:
            self.text = "" # Only the root node ('navMap') does not have 'text' or 'content'

        # The next part looks complex, and that's because it is...
        #
        # Some NCX files, even ones that have a hierarchy, still have navPoints that are siblings
        # that really should be parent-children. Example:
        #
        #  - ch15.html
        #  - ch15.html#part1
        #  - ch15.html#part2
        #  - ch16.html
        #
        # It looks really ugly in the navigation tree,
        # so we use a heuristic to convert it to the following:
        #
        #  - ch15.html
        #    - ch15.html#part1
        #    - ch15.html#part2
        #  - ch16.html
        #
        # I think the way it is done is safe and won't mess up the treeview in any case.
        # If an epub's still looks bad it's really the epub's fault. Of course we can further
        # attempt to improve the heuristic but that would also increase the chance of breaking things.

        def shouldAddToPrevSibling(sibling, me):
            if not sibling:
                return False
            if sibling.file != me.file:
                return False
            if sibling.has_anchor:
                return False
            return me.has_anchor

        if shouldAddToPrevSibling(prev_sibling, self):
            prev_sibling.children.append(self)

        self.children = []
        if node.navPoint:
            prev_child = None
            for child in node.navPoint:
                new_child = NavPoint(self.files, child, prev_child)
                if not shouldAddToPrevSibling(prev_child, new_child):
                    self.children.append(new_child)
                    prev_child = new_child

    # This was useful when writing this class
    def print(self):
        self.__print_recursive(0)

    def __print_recursive(self, spaces):
        if self.text != "":
            print(' '*spaces + str(self.file_number) + str(self.has_anchor) + ' ' + self.text)
        # print(' '*spaces + self.content)
        for navPoint in self.children:
            navPoint.__print_recursive(spaces+2)

class ContentProvider:
    def __init__(self, window):

        """
        Manages book files and provides metadata
        :param window: Main application window reference, serves as communication hub
        """
        self.__window = window
        # Checks if cache folder exists
        self.__cache_path = self.__window.config_provider.config["Application"]["cacheDir"]
        if not os.path.exists(self.__cache_path):
            os.mkdir(self.__cache_path)  # If not create it
        self.__ready = False
        self.book_name = ""

        # The 'button' navigation in the header bar uses this. It is based on the 'spine' in the content.opf file
        self.files = []
        # The treeview navigation uses this. It is based on the NCX file.
        self.index = None



    def prepare_book(self, file_path):
        """
        Loads book meta data and chapters
        :param file_path:
        :return True when book loaded successfully, False when loading failed:
        """

        # Clears any old files from the cache
        if os.path.exists(self.__cache_path):
            shutil.rmtree(self.__cache_path)

        # Extracts new book
        try:
            zipfile.ZipFile(file_path).extractall(path=self.__cache_path)
        except:
            # Is not zip file
            self.__ready = False
            return False

        # Sets permissions
        os.system("chmod 700 " + self.__cache_path)

        # Finds opf file
        if os.path.exists(os.path.join(self.__cache_path, "META-INF/container.xml")):

            # Gets metadata
            metadata = self.__get_metadata

            # Calculates MD5 of book (for use in bookmarks)
            md5 = self.__calculate_book_md5(self.__window.filename)

            # Sets metadata
            try:
                self.book_name = str(bytes.decode(str(metadata.metadata.dc_title).encode("utf-8")))
            except AttributeError:
                self.book_name = _("Unknown book")

            try:
                raw_author = str(bytes.decode(str(metadata.metadata.dc_creator).encode("utf-8")))
                processed_author = ""
                first = True
                # Some magic to get nice list of authors names
                # TODO: Proper metadata and OPF data parsing, no dirty find_between tricks
                while "data:" in raw_author:
                    if not first:
                        processed_author += ", "
                    first = False
                    processed_author += self.find_between(raw_author, "data:'", "'")
                    raw_author = raw_author[raw_author.index("data:") + len("data:"):]
                if processed_author == "":
                    self.book_author = str(bytes.decode(str(metadata.metadata.dc_creator).encode("utf-8")))
                else:
                    self.book_author = processed_author
            except AttributeError:
                self.book_author = _("Unknown author(s)")

            self.book_md5 = md5.hexdigest()

            # Adds book to config (for use in bookmarks)
            if self.book_md5 not in self.__window.config_provider.config:
                self.__window.config_provider.add_book_to_config(self.book_md5)

            # Get oebps
            self.__oebps = self.__get_oebps

            # Loads titles and file paths
            self.__load_titles_and_files()

            # Validates files
            #self.__validate_files(metadata)

            # End of preparations
            self.__ready = True
            return True
        else:  # Else returns False to indicate errors
            self.__ready = False
            return False

    @property
    def __get_opf_file_path(self):
        """
        Finds and returns OPF file path
        :return OPF file path:
        """
        container_data = xml2obj(open(os.path.join(self.__cache_path, "META-INF/container.xml"), "r"))
        return container_data.rootfiles.rootfile.full_path

    @property
    def __get_metadata(self):
        """
        Creates and returns metadata object
        :return metadata object:
        """

        # Gets OPF file path
        opf_file_path = self.__get_opf_file_path
        # Loads OPF file and parse it
        return xml2obj(open(os.path.join(self.__cache_path, opf_file_path), "r"))

    @property
    def __get_oebps(self):
        """
        Finds and returns oebps
        :return oebps:
        """
        return os.path.split(self.__get_opf_file_path)[0]

    @property
    def __get_ncx_file_path(self):
        """
        Finds and returns NCX file path
        :return NCX file path:
        """

        # Gets metadata object
        metadata = self.__get_metadata
        # Finds NCX file
        for x in metadata.manifest.item:
            if x.media_type == "application/x-dtbncx+xml":
                return os.path.join(self.__cache_path, self.__get_oebps, x.href)

    def __calculate_book_md5(self, file_path):
        """
        Calculates and returns unique MD5 hash based on book content to be used in config
        :param file_path:
        :return MD5 hash of book content:
        """
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            while True:
                piece = f.read(28 * md5.block_size)
                if not piece:
                    break
                md5.update(piece)
        f.close()
        return md5

    def __load_titles_and_files(self):
        """
        Loads titles and chapter file paths
        """
        ncx_file_path = self.__get_ncx_file_path
        metadata = self.__get_metadata
        self.chapter_links = []
        chapter_order = []
        for x in metadata.spine.itemref:
            self.files.append([y.href for y in metadata.manifest.item if y.id == x.idref][0])

        self.titles = []
        if os.access(ncx_file_path, os.R_OK):  # Checks if NCX is accessible
            # Parse NCX file
            ncx_tree = xml2obj(open(ncx_file_path))
            self.index = NavPoint(self.files, ncx_tree.navMap)
            # self.index.print()

    def __validate_files(self, metadata):
        """
        Validates files and reloads them if necessary
        :param metadata:
        """
        # TODO: This is the most terrible way to validate anything. Needs real re-write
        # Why is it checking only one path, why does it asume any of files links from manifest are correct?
        if not os.path.exists(os.path.join(self.__cache_path, self.__oebps, self.chapter_links[0])):
            # Reloads files
            self.chapter_links = []
            for x in metadata.manifest.item:
                if x.media_type == "application/xhtml+xml":
                    self.chapter_links.append(x.href)
            self.titles = []
            i = 1
            while not len(self.titles) == len(self.chapter_links):
                self.titles.append(_("Chapter %s") % (str(i)))
                i += 1

    @property
    def chapter_count(self):
        """
        Returns number of chapters
        :return chapter number:
        """
        return len(self.files)

    @property
    def status(self):
        """
        Returns boolean status of book loading
        :return book status:
        """
        return self.__ready

    def get_chapter_file_path(self, number):
        """
        Returns a chapter file to feed into viewer
        :param number:
        :return chapter file:
        """
        return os.path.join(self.__cache_path, self.__oebps, self.files[number])


    def complete_chapter_file_path(self, partial_file_path):
        return os.path.join(self.__cache_path, self.__oebps, partial_file_path)

    def uri_to_chapter(self, uri):
        """
        Based on chapter uri finds current chapter number and tells UI elements to update
        :param uri:
        """
        uri_without_anchor = uri.split('#')[0]
        for i, filename in enumerate(self.files):
            if uri_without_anchor.endswith(filename):
                return i

    def find_between(self, s, first, last):
        """
        Help methods for parsing NCX files, finds first sub-string between two strings
        :param s: String to search in
        :param first: First sub-string
        :param last: Second sub-string
        :return: Sub-string from given string between first and second sub-string
        """
        try:
            start = s.index(first) + len(first)
            end = s.index(last, start)
            return s[start:end]
        except ValueError:
            return ""
