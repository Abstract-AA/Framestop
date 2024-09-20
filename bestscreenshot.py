#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject
from moviepy.editor import VideoFileClip
import os
import threading
import time
from PIL import Image

#this file should be called screenshot optimizer

# Monkey patch for the deprecated Image.ANTIALIAS in PIL
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS  # Ensure compatibility with Pillow 10.x

# Initialize GTK and check if it's available
if not Gtk.init_check():
    print("Failed to initialize GTK.")
    exit(1)

class ConverterApp(Gtk.Window):

    def __init__(self):
        super().__init__(title="Screenshot Optimizer")
        self.set_border_width(10)
        self.set_default_size(600, 165)

     
    def on_select_input_file(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Input File", parent=self, action=Gtk.FileChooserAction.OPEN
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            input_file_path = dialog.get_filename()
            self.input_entry.set_text(input_file_path)
            self.input_directory = os.path.dirname(input_file_path)
            self.output_entry.set_text(self.input_directory) # Automatically set the output directory to the same folder as the input
        dialog.destroy()

    def on_select_output_directory(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Output Directory", parent=self, action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.output_entry.set_text(dialog.get_filename())
        if self.input_directory:
            dialog.set_current_folder(self.input_directory)
        dialog.destroy()


def main():
    app = ConverterApp()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()