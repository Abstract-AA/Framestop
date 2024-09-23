#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject, GdkPixbuf, GLib
from moviepy.editor import VideoFileClip
import os
from PIL import Image

if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.Resampling.LANCZOS  # Ensure compatibility with Pillow 10.x

if not Gtk.init_check():
    print("Failed to initialize GTK.")
    exit(1)

class ScreenshotOptmizer(Gtk.Window):

    def __init__(self):
        super().__init__(title="Screenshot Optimizer")
        self.set_border_width(10)
        self.set_default_size(800, 600)  

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(vbox)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(False)
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        vbox.pack_start(grid, True, True, 0)

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

        self.frame_area = Gtk.ScrolledWindow(hexpand=True, vexpand=True)
        self.frame_area.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        grid.attach(self.frame_area, 0, 2, 3, 1)

        adjustment = Gtk.Adjustment(value=0, lower=0, upper=0, step_increment=1, page_increment=1)
        self.frame_slider = Gtk.Scale(orientation=Gtk.Orientation.HORIZONTAL, adjustment=adjustment)
        self.frame_slider.set_digits(0)
        self.frame_slider.connect("value-changed", self.on_frame_slider_changed)
        grid.attach(self.frame_slider, 0, 3, 3, 1)

        # Checkbox for applying optimization
        self.optimize_checkbox = Gtk.CheckButton(label="Apply Screenshot Optimization")
        grid.attach(self.optimize_checkbox, 0, 4, 3, 1)

        self.status_label = Gtk.Label(label="")
        grid.attach(self.status_label, 0, 5, 3, 1)

        # Screenshot button
        screenshot_button = Gtk.Button(label="Take Screenshot")
        screenshot_button.connect("clicked", self.on_take_screenshot)
        grid.attach(screenshot_button, 0, 6, 3, 1)

        self.frame_images = []
        self.current_frame = 0
        self.video = None
        self.pixbuf_cache = []

        #a sidebar for further options and fine tuning adjustments could be included, consider this later

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
            self.output_entry.set_text(self.input_directory)
            self.load_video_frames(input_file_path)
        dialog.destroy()

    def load_video_frames(self, input_file):
        if not input_file:
            print("No input file selected.")
            return
        try:
            self.video = VideoFileClip(input_file)
        except Exception as e:
            self.show_error_dialog("Error: Invalid video file selected.")
            return
        
        self.frame_images.clear()
        self.pixbuf_cache.clear()

        for i, frame in enumerate(self.video.iter_frames()):
            image = Image.fromarray(frame)
            self.frame_images.append(image)

        self.frame_slider.get_adjustment().set_lower(0)
        self.frame_slider.get_adjustment().set_upper(len(self.frame_images) - 1)
        self.frame_slider.set_value(0)

        self.update_frame_display(0)

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

        for child in self.frame_area.get_children():
            self.frame_area.remove(child)

        if frame_index < len(self.pixbuf_cache):
            pixbuf = self.pixbuf_cache[frame_index]
        else:
            buffer = image.tobytes()
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

        selected_frame = self.frame_images[self.current_frame]

        if self.optimize_checkbox.get_active():
            self.update_status("Optimization placeholder applied... (logic pending)")
            # Placeholder: Apply screenshot optimization here
            # Future algorithm will modify `selected_frame` before saving.
            pass

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
