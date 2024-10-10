#!/usr/bin/env python3
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GObject, GdkPixbuf, GLib, Gdk
from moviepy.editor import VideoFileClip
import os
from PIL import Image
from basic_colormath import get_delta_e

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
        self.output_auto = True  # Automatically assign input folder to output folder by default
        self.frame_skip_value = 1
        self.frame_analysis_value=5
        self.threshold = 5

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=5)
        self.add(vbox)

        grid = Gtk.Grid()
        grid.set_column_homogeneous(False)
        grid.set_column_spacing(10)
        grid.set_row_spacing(10)
        vbox.pack_start(grid, True, True, 0)
        self.frame_skip_value = 1 

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

        # HBox to hold checkbox and + / - buttons
        hbox_controls = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        # Checkbox for applying optimization
        self.optimize_checkbox = Gtk.CheckButton(label="Apply Screenshot Optimization")
        #self.optimize_checkbox.connect("clicked",<aqui vai a integração com a função de otimizar o screenshot>)
        hbox_controls.pack_start(self.optimize_checkbox, False, False, 0)

        # Add frame button
        addframe_button = Gtk.Button(label="+ X frame(s)")
        addframe_button.connect("clicked", self.on_add_frame)
        hbox_controls.pack_start(addframe_button, False, False, 0)

        # Remove frame button
        removeframe_button = Gtk.Button(label="- X frame(s)")
        removeframe_button.connect("clicked", self.on_remove_frame)
        hbox_controls.pack_start(removeframe_button, False, False, 0)

        #Skip X frames forward or backwards 
        self.frame_skip_spinner = Gtk.SpinButton()
        self.frame_skip_spinner.set_range(1, 100)
        self.frame_skip_spinner.set_increments(1, 10)
        self.frame_skip_spinner.set_value(self.frame_skip_value)
        self.frame_skip_spinner.connect("value-changed", self.on_frame_skip_value_changed)
        hbox_controls.pack_start(Gtk.Label(label="Skip X frames:"), False, False, 0)
        hbox_controls.pack_start(self.frame_skip_spinner, False, False, 0)

        # Copy current frame to clipboard button next to the frame buttons
        copytoclip_button = Gtk.Button(label="Copy frame to clipboard")
        copytoclip_button.connect("clicked", self.copytoclip)
        hbox_controls.pack_start(copytoclip_button, False, False, 0)

        # Settings button next to the frame buttons
        settings_button = Gtk.Button(label="Settings")
        settings_button.connect("clicked", self.on_open_settings)
        hbox_controls.pack_start(settings_button, False, False, 0)

        grid.attach(hbox_controls, 0, 4, 3, 1)

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
        # TODO add functionality of copying screenshot directly to clipboard

    def update_status(self, message):
        GLib.idle_add(self.status_label.set_text, message)

    def copytoclip(self,widget):
        if not self.frame_images:
            self.show_error_dialog("Error: No frame to copy. Load a video first.")
            return

        # Get the current frame image (PIL.Image object)
        selected_frame = self.frame_images[self.current_frame]

        # Convert the PIL Image to a GdkPixbuf object
        buffer = selected_frame.tobytes()
        pixbuf = GdkPixbuf.Pixbuf.new_from_data(
            buffer,
            GdkPixbuf.Colorspace.RGB,
            False, 8,
            selected_frame.width, selected_frame.height,
            selected_frame.width * 3
        )

        # Get the clipboard object and set the Pixbuf
        clipboard = Gtk.Clipboard.get(Gdk.SELECTION_CLIPBOARD)
        clipboard.set_image(pixbuf)

        # Update the status to inform the user
        self.update_status(f"Copied frame {self.current_frame} to clipboard.")
        print(f"Copied frame {self.current_frame} to clipboard.")

    def on_frame_skip_value_changed(self, widget):
        self.frame_skip_value = widget.get_value_as_int()

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
            if self.output_auto:
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
            old_frame = self.current_frame
            self.update_status("Searching for the best frames...")
            selected_frame, self.current_frame = self.getBestFrame()
            selected_frame.save(os.path.join(output_folder, f"frame_{self.current_frame}.jpg"))
            self.update_status(f"Screenshot saved. Best frame at {self.current_frame}th frame ({abs(old_frame - self.current_frame)} frame{'s' if abs(old_frame - self.current_frame) != 1 else ''} away)")
            #TODO mover preview para o frame atual
        else:
            selected_frame.save(os.path.join(output_folder, f"frame_{self.current_frame}.jpg"))
            self.update_status(f"Screenshot of frame {self.current_frame} saved.")
            print(f"Screenshot of frame {self.current_frame} saved.")

    def neighbour_pixel_values(self,loaded_img, x,y):
        cima = loaded_img[x,y-1]
        direita = loaded_img[x+1, y]
        baixo = loaded_img[x, y+1]
        esquerda = loaded_img[x-1, y]
        return [cima, direita, baixo, esquerda]

    def imageRating(self,img):
        largura, altura = img.size
        loaded_img = img.load()
        mudancas = 0
        for linha in range(1, altura-1):
            for coluna in range(1, largura-1):
                if (linha%2 == 0 and coluna%2 == 0) or (linha%2 == 1 and coluna%2 == 1):
                    for pixel in self.neighbour_pixel_values(loaded_img, coluna, linha):
                        dE = get_delta_e(loaded_img[coluna, linha], pixel)
                        if dE > self.threshold:
                            mudancas += round(dE, 2)
        return mudancas*2/(largura*altura) #como estamos filtrando metade dos pixels, multiplicamos por 2
    
    def getBestFrame(self):
        #TODO melhorar range de frames quando está perto do início ou fim
        half_frames = self.frame_analysis_value // 2
        start_frame = int(max(0, self.current_frame - half_frames))
        end_frame = int(min(len(self.frame_images), self.current_frame + half_frames))
        frames_to_analyze_array = list(range(start_frame, end_frame))
        ratings = {}
        for frame_index in frames_to_analyze_array:
            copia = self.frame_images[frame_index].copy()
            copia.thumbnail((100,100))
            ratings[frame_index] = self.imageRating(copia)
        best_frame_index = max(ratings, key=ratings.get)
        return [self.frame_images[best_frame_index], best_frame_index]

    def on_add_frame(self, widget):
        # Move slider value forward by 1 frame
        current_value = self.frame_slider.get_value()
        self.frame_slider.set_value(min(current_value + self.frame_skip_value, len(self.frame_images) - 1))

    def on_remove_frame(self, widget):
        # Move slider value backward by 1 frame
        current_value = self.frame_slider.get_value()
        self.frame_slider.set_value(max(current_value - self.frame_skip_value, 0))

    def on_open_settings(self,widget):
        # this creates a dialog window for settings
        dialog = Gtk.Dialog(title="Settings", transient_for=self, flags=0)
        dialog.add_buttons(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        # Get the content area of the dialog
        content_area = dialog.get_content_area()
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=15)
        content_area.pack_start(vbox, False, False, 0)
        dialog.set_default_size(420, 180)

        # Create the grid
        grid2 = Gtk.Grid()
        grid2.set_column_homogeneous(False)
        grid2.set_column_spacing(10)
        grid2.set_row_spacing(10)
        vbox.pack_start(grid2, True, True, 0)

        # Label for the output folder
        autoassignfoldercb_label = Gtk.Label(label="For saving Files:")
        grid2.attach(autoassignfoldercb_label, 0, 0, 1, 1)  # Left column (0), top row (0)

        # Checkbox to set output folder
        self.autoassignfoldercb = Gtk.CheckButton(label="Automatically set input folder as output folder")
        self.autoassignfoldercb.set_active(self.output_auto)
        self.autoassignfoldercb.connect("toggled", self.on_toggle_auto_output_folder)
        grid2.attach(self.autoassignfoldercb, 1, 0, 1, 1)  # Right column (1), same row (0)

        # Label for frame analysis range
        frame_analysis_label = Gtk.Label(label="Frame range for analysis:")
        grid2.attach(frame_analysis_label, 0, 1, 1, 1)  # Next row

        # SpinButton to set the frame analysis range
        self.frame_analysis_adj = Gtk.Adjustment(value=self.frame_analysis_value, lower=1, upper=100, step_increment=1, page_increment=10, page_size=0)
        self.frame_analysis_spin = Gtk.SpinButton(adjustment=self.frame_analysis_adj)
        self.frame_analysis_spin.connect("value-changed", self.on_frame_analysis_value_changed)

        self.frame_analysis_spin.set_halign(Gtk.Align.CENTER)  # Align to the right of the cell
        self.frame_analysis_spin.set_size_request(10,10)  # Adjust this value to control the width
        grid2.attach(self.frame_analysis_spin, 1, 1, 1, 1)  # Right column, same row as label (1)

        # Label for threshold range
        threshold_label = Gtk.Label(label="Frame selection Threshold:")
        grid2.attach(threshold_label, 0, 2, 1, 1)  

        # SpinButton to set the threshold range
        self.threshold_adj = Gtk.Adjustment(value=self.threshold, lower=1, upper=10, step_increment=1, page_increment=10, page_size=0)
        self.threshold_spin = Gtk.SpinButton(adjustment=self.threshold_adj)
        self.threshold_spin.connect("value-changed", self.on_threshold_value_changed)

        self.threshold_spin.set_halign(Gtk.Align.CENTER)  # Center it
        self.threshold_spin.set_size_request(100, 10)  # Adjust width as needed
        grid2.attach(self.threshold_spin, 1, 2, 1, 1)  # Attach the spin button


        #TODO add the screenshot configurations here

        # Show the dialog with its contents
        dialog.show_all()

        # Wait for user response (OK or Cancel)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.frame_analysis_value = self.frame_analysis_spin.get_value_as_int()
            self.threshold = self.threshold_spin.get_value_as_int()

        dialog.destroy()

    def on_toggle_auto_output_folder(self, widget):
        self.output_auto = widget.get_active()
        print(f"Automatic output folder selection: {self.output_auto}")

    def on_frame_analysis_value_changed(self, widget):
        self.frame_analysis_value = widget.get_value()
        print(f"Frames to analyze: {self.frame_analysis_value}")
    
    def on_threshold_value_changed(self, widget):
        self.threshold_value = (widget.get_value())/10
        print(f"Threshold set at: {self.threshold_value}")

def main():
    app = ScreenshotOptmizer()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()

if __name__ == "__main__":
    main()
