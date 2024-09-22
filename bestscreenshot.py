#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject, GdkPixbuf, GLib
from moviepy.editor import VideoFileClip
import os
from PIL import Image

# Monkey patch for the deprecated Image.ANTIALIAS in PIL
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS  # Ensure compatibility with Pillow 10.x

# Initialize GTK and check if it's available
if not Gtk.init_check():
    print("Failed to initialize GTK.")
    exit(1)

class ScreenshotOptmizer(Gtk.Window):

    def __init__(self):
        super().__init__(title="Screenshot Optimizer")
        self.set_border_width(10)
        self.set_default_size(800, 600)  # Adjusted initial size to accommodate larger frame area

        # Create main box
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(vbox)

        # Create main grid
        grid = Gtk.Grid()
        grid.set_column_homogeneous(False)
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        vbox.pack_start(grid, True, True, 0)  # Add grid to vbox

        # Input file path
        input_label = Gtk.Label(label="Input File:")
        grid.attach(input_label, 0, 0, 1, 1)

        self.input_entry = Gtk.Entry(hexpand=True)
        grid.attach(self.input_entry, 1, 0, 1, 1)

        input_file_button = Gtk.Button(label="Select Input File")
        input_file_button.connect("clicked", self.on_select_input_file)
        grid.attach(input_file_button, 2, 0, 1, 1)

        # Output file path
        output_label = Gtk.Label(label="Output Folder:")
        grid.attach(output_label, 0, 1, 1, 1)

        self.output_entry = Gtk.Entry(hexpand=True)
        grid.attach(self.output_entry, 1, 1, 1, 1)

        output_directory_button = Gtk.Button(label="Select Output Folder")
        output_directory_button.connect("clicked", self.on_select_output_directory)
        grid.attach(output_directory_button, 2, 1, 1, 1)

        # Scrollable area to display video frames, allow both horizontal and vertical expansion
        self.frame_area = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        self.frame_area.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        grid.attach(self.frame_area, 0, 2, 3, 1)

        # Frame selection slider
        self.frame_slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL)
        self.frame_slider.set_range(0, 0)  # Will be updated after frames are loaded
        self.frame_slider.connect("value-changed", self.on_frame_slider_changed)
        grid.attach(self.frame_slider, 0, 3, 3, 1)

        # Status Label (Moved below the frame area)
        self.status_label = Gtk.Label(label="")
        grid.attach(self.status_label, 0, 4, 3, 1)

        # Screenshot button
        screenshot_button = Gtk.Button(label="Take Screenshot")
        screenshot_button.connect("clicked", self.on_take_screenshot)
        grid.attach(screenshot_button, 0, 5, 3, 1)

        self.frame_images = []  # List to store Image objects
        self.current_frame = 0
        self.video = None  # Placeholder for the loaded video
        self.pixbuf_cache = []  # Cache GdkPixbuf for smoother scrolling

    def update_status(self, message):
        GLib.idle_add(self.status_label.set_text, message)

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
            self.output_entry.set_text(self.input_directory)  # Automatically set the output directory
            self.load_video_frames(input_file_path)  # Load video and display frames
        dialog.destroy()

    def load_video_frames(self, input_file):
        if not input_file:
            print("No input file selected.")
            return
        
        # Error handling for invalid video files
        try:
            self.video = VideoFileClip(input_file)
        except Exception as e:
            self.show_error_dialog("Error: Invalid video file selected.")
            return
        
        self.frame_images.clear()
        self.pixbuf_cache.clear()

        # Extract frames
        for i, frame in enumerate(self.video.iter_frames(fps=1)):  # Adjust fps for fewer frames
            image = Image.fromarray(frame)
            self.frame_images.append(image)

        # Update the slider based on the number of frames
        self.frame_slider.set_range(0, len(self.frame_images) - 1)
        self.frame_slider.set_value(0)  # Set to first frame by default

        self.update_frame_display(0)  # Display the first frame

    def show_error_dialog(self, message):
        dialog = Gtk.MessageDialog(
            parent=self, flags=0, message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK, text="Input Error"
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def on_select_output_directory(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Output Directory", parent=self, action=Gtk.FileChooserAction.SELECT_FOLDER
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.output_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def on_frame_slider_changed(self, widget):
        self.current_frame = int(self.frame_slider.get_value())
        self.update_frame_display(self.current_frame)

    def update_frame_display(self, frame_index):
        if not self.frame_images:
            return

        image = self.frame_images[frame_index]

        # Clear previous image from frame_area
        for child in self.frame_area.get_children():
            self.frame_area.remove(child)

        if frame_index < len(self.pixbuf_cache):
            pixbuf = self.pixbuf_cache[frame_index]
        else:
            buffer = image.tobytes()  # This Converts images to bytes for GdkPixbuf
            pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                buffer,
                GdkPixbuf.Colorspace.RGB,
                False, 8,
                image.width, image.height,
                image.width * 3
            )
            self.pixbuf_cache.append(pixbuf)

        image_widget = Gtk.Image.new_from_pixbuf(pixbuf)
        self.frame_area.add(image_widget)
        self.frame_area.show_all()

    def on_take_screenshot(self, widget):
        if not self.frame_images:
            self.show_error_dialog("Error: Please select a proper video file.")
            return

        output_folder = self.output_entry.get_text()

        if not output_folder:
            self.show_error_dialog("Error: Please select a proper output folder.")
            return

        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        # Save only the selected frame
        selected_frame = self.frame_images[self.current_frame]
        selected_frame.save(os.path.join(output_folder, f"frame_{self.current_frame}.jpg"))

        self.update_status(f"Screenshot of frame {self.current_frame} saved.")
        print(f"Screenshot of frame {self.current_frame} saved.")

def main():
    app = ScreenshotOptmizer()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
