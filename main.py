#!/usr/bin/python3

"""
The MIT License (MIT)

Copyright (c) 2025 Scott Moreau <oreaus@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from ctypes import CDLL
CDLL('libgtk4-layer-shell.so')

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Gtk4LayerShell", "1.0")
from gi.repository import Gtk, Gdk, Gio, Pango, Gtk4LayerShell


class LaserButton(Gtk.Button):

    def __init__(self, name, desc, exe):
        super().__init__()
        self.name = name
        self.desc = desc
        self.exe = exe

class LaserSearchWindow(Gtk.ApplicationWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.app = self.get_application()

        self.set_title("Laser Search")

        Gtk4LayerShell.init_for_window(self)
        Gtk4LayerShell.set_namespace(self, "com.roundabout_host.panorama.laser_search")
        Gtk4LayerShell.set_layer(self, Gtk4LayerShell.Layer.OVERLAY)

        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.TOP, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.BOTTOM, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.LEFT, True)
        Gtk4LayerShell.set_anchor(self, Gtk4LayerShell.Edge.RIGHT, True)
        Gtk4LayerShell.set_keyboard_mode(self, Gtk4LayerShell.KeyboardMode.EXCLUSIVE)
        main_layout = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_layout.set_size_request(-1, 200)
        main_layout.set_valign(Gtk.Align.CENTER)
        main_layout.set_halign(Gtk.Align.CENTER)
        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_size_request(700, 50)
        self.search_entry.set_margin_bottom(25)
        self.search_entry.connect("search-changed", self.laser_search_changed)
        self.search_entry.connect("activate", self.laser_activate)
        self.search_entry.connect("stop-search", self.laser_search_stop)
        main_layout.append(self.search_entry)
        self.app_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.app_box.set_halign(Gtk.Align.CENTER)
        self.app_box.set_spacing(10)
        main_layout.append(self.app_box)
        hbox = Gtk.CenterBox()
        hbox.set_hexpand(True)
        hbox.set_vexpand(True)
        hbox.set_center_widget(main_layout)
        self.set_child(hbox)
        self.add_css_class("laser_search")
        display = self.get_display()
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(" \
            window.laser_search { \
                background-color: rgba(0, 0, 0, 0.5); \
            } \
            button.flat { \
                border-width: 0; \
                background-image: none; \
                background-color: transparent; \
                transition: background-color 0.3s ease-in-out; \
            } \
            button.flat:hover { \
                background-color: #3337; \
            } \
            label.custom_text { \
                color: #EEE; \
                font-size: 12px; \
            } \
            image.custom_size { \
                -gtk-icon-transform: scale(1.7); \
                margin-bottom: 20px; \
                padding-top: 15px; \
            }")
        Gtk.StyleContext.add_provider_for_display(display, css_provider, Gtk.STYLE_PROVIDER_PRIORITY_USER)
        self.app_info_monitor = Gio.AppInfoMonitor.get()
        self.app_info_monitor.connect("changed", self.populate_menu_entries)
        self.populate_menu_entries()

        self.present()

        self.search_entry.grab_focus()

    def laser_search_stop(self, laser_search_stop):
        self.app.quit()

    def laser_search_changed(self, search_entry):
        while True:
            child = self.app_box.get_first_child()
            if not child:
                break
            self.app_box.remove(child)
        i = 0
        text = self.search_entry.get_text().lower()
        if not text:
            return
        for button in self.cached_buttons:
            if (button.name and text in button.name.lower()) or \
               (button.desc and text in button.desc.lower()) or \
               (button.exe and text in button.exe.lower()):
                self.app_box.append(button)
                i = i + 1
            if i > 7:
                break

    def laser_activate(self, search_entry):
        if len(self.app_box.observe_children()) != 1:
            return
        button = self.app_box.get_first_child()
        button.launch()
        self.app.quit()

    def app_button_clicked(self, button):
        button.launch()
        self.app.quit()

    def populate_menu_entries(self, app_info_monitor=None):
        app_infos = Gio.AppInfo.get_all()
        app_infos.sort(key=lambda app_info: app_info.get_display_name().lower())
        self.cached_buttons = []

        for app_info in app_infos:
            app_categories = app_info.get_categories()
            if app_categories == None:
                continue
            app_name = app_info.get_display_name()
            command = app_info.get_executable()
            app_button = LaserButton(app_name, app_info.get_description(), command)
            app_button.launch = app_info.launch
            app_button.set_tooltip_text(app_name)
            app_label = Gtk.Label(label=app_name)
            app_label.add_css_class("custom_text")
            app_label.set_ellipsize(Pango.EllipsizeMode.END)
            app_label.set_max_width_chars(7)
            app_button_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
            app_button_box.set_size_request(50, -1)
            app_button_box.append(app_label)
            app_button.set_child(app_button_box)
            app_button.set_has_frame(False)
            app_button.add_css_class("flat")

            image = Gtk.Image()
            image.add_css_class("custom_size")
            image.set_icon_size(Gtk.IconSize.LARGE)
            icon = app_info.get_icon()
            if icon:
                icon_name = icon.to_string()
                if not Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).has_icon(icon_name):
                    continue
                if icon_name[0] == '/':
                    image.set_from_file(icon_name)
                else:
                    image.set_from_icon_name(icon_name)
            else:
                if not Gtk.IconTheme.get_for_display(Gdk.Display.get_default()).has_icon(app_name.lower()):
                    continue
                image.set_from_icon_name(app_name.lower())

            app_button.connect("clicked", self.app_button_clicked)
            app_button_box.prepend(image)
            self.cached_buttons.append(app_button)

class LaserSearch(Gtk.Application):
    def __init__(self):
        super().__init__(flags=Gio.ApplicationFlags.FLAGS_NONE)
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        win = LaserSearchWindow(application=app)

if __name__ == "__main__":
    app = LaserSearch()
    app.run(None)
