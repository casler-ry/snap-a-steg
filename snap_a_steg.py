# Snap-A-Steg: secure image steganography app
# Copyright (C) 2025 argeincharge
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.


from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.button import Button
from kivy.graphics.texture import Texture
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.core.clipboard import Clipboard
from kivy.uix.label import Label
from kivy.core.window import Window
from kivy.uix.relativelayout import RelativeLayout
from kivy.clock import Clock
from kivy.utils import get_color_from_hex
import numpy as np
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image as PILImage
from cryptography.fernet import InvalidToken
import re
import os

import encode_decode as ed
import ui_helpers as ui

Window.size = (800, 600)
Window.clearcolor = (.1, .1, .1, 1)  # Blackbackground


class StegoUI(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'  # vertical layout: preview above, buttons below

        # Preview container with relative layout to stack image and label
        self.preview = RelativeLayout(size_hint_y=0.8)
        self.add_widget(self.preview)

        # Background color canvas (gray)
        with self.preview.canvas.before:
            from kivy.graphics import Color, Rectangle
            Color(0,0, 0, 1)
            self.bg_rect = Rectangle(pos=self.preview.pos, size=self.preview.size)
        self.preview.bind(pos=self.update_bg_rect, size=self.update_bg_rect)

        # Image widget fills the container
        self.img_widget = Image(allow_stretch=True,keep_ratio=True,size_hint=(1, 1),pos_hint={'center_x': 0.5, 'center_y': 0.5})
        self.preview.add_widget(self.img_widget)

        # "No Image Loaded" label stacked on top, centered
        self.no_image_label = Label(
            text="No Image Loaded\nClick 'Load Image'",
            halign="center",
            valign="middle",
            color=(0, 0, 0, 1),
            font_size=20,
            size_hint=(1, 1),
            pos_hint={'center_x': 0.5, 'center_y': 0.5}
        )
        self.no_image_label.bind(size=self.no_image_label.setter('text_size'))
        self.preview.add_widget(self.no_image_label)

        # Controls below the preview, horizontal buttons
        self.controls = BoxLayout(size_hint_y=0.2, spacing=15, padding=[20,20])
        self.add_widget(self.controls)

        self.btn_load = Button(text="Load Image")
        self.btn_load.bind(on_release=self.open_file_chooser)
        self.controls.add_widget(self.btn_load)

        self.btn_encode = Button(text="Encode Message")
        self.btn_encode.bind(on_release=lambda x: self.open_encode_popup())
        self.controls.add_widget(self.btn_encode)

        self.btn_decode = Button(text="Decode Message")
        self.btn_decode.bind(on_release=lambda x: self.open_decode_popup())
        self.controls.add_widget(self.btn_decode)

        # Init variables
        self.original_image = None
        self.edited_image = None

        for btn in [self.btn_load, self.btn_encode, self.btn_decode]:
            btn.background_color = (0.2, 0.6, 0.9, 1)
            btn.color = (1, 1, 1, 1)
            btn.font_size = 16
            btn.size_hint_x = 1

    def update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def show_progress_popup(self):
        layout= BoxLayout(orientation='vertical', padding=20)
        label = Label(text="Encoding in progress...\nPlease wait.")
        layout.add_widget(label)
        popup = Popup(title="Encoding", content=layout, size_hint=(0.5, 0.3) ,auto_dismiss=False)
        popup.open()
        return popup 

    def load_image(self, path):
        pil_image = PILImage.open(path).convert('RGB')
        self.original_image = pil_image.copy()
        self.edited_image = pil_image

        img_array = np.array(pil_image)
        buf = img_array.tobytes()

        texture = Texture.create(size=(pil_image.width, pil_image.height))
        texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        texture.flip_vertical()

        self.img_widget.texture = texture
        self.img_widget.size = texture.size

        # Hide the no image label when image is loaded
        self.no_image_label.opacity = 0

    def open_file_chooser(self, instance):
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.askopenfilename(
            filetypes=[("Image Files", "*.png *.jpg *.jpeg")],
            title="Select an image"
        )
        root.destroy()

        if file_path:
            self.load_image(file_path)

    def save_embedded_image(self, image_data):
        root = tk.Tk()
        root.withdraw()
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("Lossless Images (PNG, BMP, TIFF)", "*.png *.bmp *.tiff"),
                ("PNG Image (recommended)", "*.png"),
                ("BMP Image", "*.bmp"),
                ("TIFF Image", "*.tiff"),
                ("All Files (advanced / unsafe)", "*.*")
            ],
        title="Save Image As"
        )

        root.destroy()

        if not file_path:
            return  # User cancelled save dialog
        
        #If user forgot to type an extension, force PNG
        if not os.path.splitext(file_path)[1]:
            file_path += ".png"

        ext = os.path.splitext(file_path)[1].lower()
        
        #Formats that will destroy stego data
        lossy_formats = ['.jpg', '.jpeg', '.webp', '.heic']

        if ext in lossy_formats:
            proceed = messagebox.askyesno(
                "Warning: Data Loss Possible",
                "This image format uses lossy compression.\n\n"
                "Saving in this format may corrupt or destroy the hidden message.\n\n"
                "Are you sure you want to proceed?"
                )
            if not proceed:
                return  # User chose not to proceed
            
        #Force pillor to use PNG for lossless formats
        format_map = {
            '.png': 'PNG',
            '.bmp': 'BMP',
            '.tiff': 'TIFF',
            '.tif': 'TIFF',
            '.jpg': 'JPEG',
            '.jpeg': 'JPEG',
            '.webp': 'WEBP',
            '.heic': 'HEIC'
        }

        fmt = format_map.get(ext, 'PNG')  # Default to PNG if unknown

        try:
            image_data.save(file_path, format=fmt)
            print(f"Image saved to: {file_path}")
        except Exception as e:
            messagebox.showerror("Error Saving Image", f"An error occurred while saving the image:\n{e}")
        
        
        # if file_path:
        #     try:
        #         image_data.save(file_path)
        #         print(f"Image saved to: {file_path}")
        #     except Exception as e:
        #         print(f"Error saving image: {e}")

    def on_encode(self, secret_input, password_input, status_text, btn_copy_key):
        popup = self.show_progress_popup()
        def do_encode(dt):
            try:
                secret_text = secret_input.text.strip()
                pwd = password_input.text.strip()
                if not secret_text or not pwd:
                    status_text.text = "Please enter both message and password."
                    btn_copy_key.disabled = True
                    return
                if not self.edited_image:
                    status_text.text = "Load an image first."
                    btn_copy_key.disabled = True
                    return
                try:
                    max_bytes = ed.calculate_max_message_size(self.edited_image)
                    message_bytes = len(secret_text.encode("utf-8"))
                    if message_bytes > max_bytes:
                        status_text.text = f"Message too long! Max: {max_bytes} bytes.\nYour message: {message_bytes} bytes."
                        btn_copy_key.disabled = True
                        return

                    self.edited_image, key = ed.encrypt_and_embed_message(
                        image=self.edited_image,
                        message=secret_text,
                        password=pwd
                    )
                    status_text.text = f"Encoded! Key:\n{key.decode()}"
                    status_text.text += f"\nUsed: {message_bytes}/{max_bytes} bytes"
                    btn_copy_key.disabled = False
                    self.save_embedded_image(self.edited_image)
                    self.update_preview()
                except Exception as e:
                    status_text.text = f"Error: {str(e)}"
                    btn_copy_key.disabled = True
            except Exception as e:
                status_text.text = f"Error: {str(e)}"
                btn_copy_key.disabled = True
            finally:
                popup.dismiss()
        Clock.schedule_once(do_encode, 0.1)

    def on_decode(self, password_input, key_input, status_text, btn_copy_message):
        pwd = password_input.text.strip()
        key_str = key_input.text.strip()
        if not pwd or not key_str:
            status_text.text = "Password and key required."
            btn_copy_message.disabled = True
            return
        if not self.edited_image:
            status_text.text = "Load an image first."
            btn_copy_message.disabled = True
            return
        try:
            # Decode the key from string to bytes
            key = key_str.encode()
            # Use the new unified function for extraction + decryption
            message = ed.extract_and_decrypt_message(self.edited_image, pwd, key)

            status_text.text = f"Decoded message:\n{message}"
            btn_copy_message.disabled = False

        except InvalidToken:
            status_text.text = "Failed to decode. \nThe encryption key or password may be incorrect."
            btn_copy_message.disabled = True
        except ValueError as ve:
            status_text.text = str(ve)
            btn_copy_message.disabled = True
        except Exception as e:
            status_text.text = f"An error occurred while decoding.\nError: {e}"
            btn_copy_message.disabled = True

    def on_copy_key(self, status_text):
        lines = status_text.text.splitlines()
        if len(lines) >= 2 and lines[0].startswith("Encoded! Key:"):
            Clipboard.copy(lines[1])
            print("Encryption key copied to clipboard.")
            status_text.text += "\n(Note: Clipboard clears in 20 seconds)"
            Clock.schedule_once(lambda dt: Clipboard.copy(""),20) # Clear clipboard after 20 seconds

    def update_preview(self):
        if not self.edited_image:
            return

        img_array = np.array(self.edited_image)
        buf = img_array.tobytes()

        texture = Texture.create(size=(self.edited_image.width, self.edited_image.height))
        texture.blit_buffer(buf, colorfmt='rgb', bufferfmt='ubyte')
        texture.flip_vertical()

        self.img_widget.texture = texture
        self.img_widget.size = texture.size

    def open_encode_popup(self, password=""):
        layout = BoxLayout(
            orientation='vertical'
            ,padding=10
            ,spacing=10
        )
        secret_input = TextInput(
            hint_text="Enter secret message"
            ,multiline=True
            ,size_hint_y=.3
            
        )
        bytes_info = Label(
            text="0 / ? bytes used"
            ,size_hint_y=None
            ,height=20
            ,color=(1, 1, 1, 1)
        )
        pwd_layout = BoxLayout(
            orientation='horizontal'
            ,size_hint_y=None
            ,height=40
            ,spacing=5)
        password_input = TextInput(
            text=password,
            hint_text="Enter password",
            password=True,
            size_hint_x=0.85
        )
        btn_toggle_pwd = Button(
            text="View"
            ,size_hint_x=0.15
        )

        btn_toggle_pwd.bind(on_release=lambda x: ui.toggle_password_visibility(password_input, btn_toggle_pwd))
        pwd_layout.add_widget(password_input)
        pwd_layout.add_widget(btn_toggle_pwd)

        # Password requirements checklist
        requirements = {
            "At least 12 characters": lambda s: len(s) >= 12,
            "At least one lowercase letter": lambda s: re.search(r"[a-z]", s),
            "At least one uppercase letter": lambda s: re.search(r"[A-Z]", s),
            "At least one digit": lambda s: re.search(r"\d", s),
            "At least one special character": lambda s: re.search(r"[^\w\s]", s),
        }

        checklist_labels = {}
        checklist_layout = BoxLayout(
            orientation='vertical'
            ,size_hint_y=None
        )
        
        checklist_layout.height = 20 * len(requirements)

        def create_label(text):
            return Label(
                text=text,
                size_hint_y=None,
                height=20,
                color=get_color_from_hex("#FF0000")  # start red (not met)
            )

        for req in requirements:
            lbl = create_label(f"❌ {req}")
            checklist_labels[req] = lbl
            checklist_layout.add_widget(lbl)

        btn_encode = Button(
            text="Encode and Save"
            ,size_hint_y=None
            ,height=40
            ,disabled=True
        )
        btn_copy_key = Button(
            text="Copy Key"
            ,size_hint_y=None, height=40, disabled=True
        )
        status_text = TextInput(
            text=""
            ,readonly=True
            ,size_hint_y=None
            ,height=80
            ,background_color=(0, 0, 0, 0)
            ,foreground_color=(1, 1, 1, 1)
        )

        # Bind the update function to both inputs
        password_input.bind(text=lambda inst, val: ui.update_checklist_and_button(
            password_input, secret_input, checklist_labels, requirements, bytes_info, btn_encode, self.edited_image, ed.calculate_max_message_size))
        secret_input.bind(text=lambda inst, val: ui.update_checklist_and_button(
            password_input, secret_input, checklist_labels, requirements, bytes_info, btn_encode, self.edited_image, ed.calculate_max_message_size))
        btn_encode.bind(on_release=lambda x: self.on_encode(secret_input, password_input, status_text, btn_copy_key))
        btn_copy_key.bind(on_release=lambda x: self.on_copy_key(status_text))
        
        # Add all widgets to the layout
        layout.add_widget(secret_input)
        layout.add_widget(bytes_info)
        layout.add_widget(pwd_layout)
        layout.add_widget(checklist_layout)
        layout.add_widget(btn_encode)
        layout.add_widget(status_text)
        layout.add_widget(btn_copy_key)

        btn_close = Button(
            text="Close"
            ,size_hint_y=None
            ,height=40
        )
        popup = Popup(
            title="Encode Secret Message"
            ,content=layout
            ,size_hint=(None, None)
            ,size=(600, 600)
        )

        def close_popup(instance):
            popup.dismiss()

        btn_close.bind(on_release=close_popup)
        layout.add_widget(btn_close)
        popup.open()


    def open_decode_popup(self, password=""):
        layout = BoxLayout(
            orientation='vertical'
            ,spacing=10
            ,padding=10
        )
        password_input = TextInput(
            text=password
            ,hint_text="Enter password"
            ,password=True
            ,size_hint_y=None
            ,height=40
        )
        key_input = TextInput(
            hint_text="Enter encryption key"
            ,size_hint_y=None
            ,height=60
        )
        status_text = TextInput(
            text=""
            ,readonly=True
            ,size_hint_y=None
            ,height=80
            ,background_color=(0, 0, 0, 0)
            ,foreground_color=(1, 1, 1, 1)
            ,multiline=True
        )
        btn_decode = Button(
            text="Decode Secret"
            ,size_hint_y=None
            ,height=40
        )
        btn_copy_message = Button(
            text="Copy Decoded Message"
            ,size_hint_y=None
            ,height=40
            ,disabled=True
        )

        def on_copy_message(instance):
            if status_text.text.startswith("Decoded message:\n"):
                Clipboard.copy(status_text.text.split('\n', 1)[1])
                print("Decoded message copied to clipboard.")

        btn_decode.bind(on_release=lambda x: self.on_decode(password_input, key_input, status_text, btn_copy_message))

        btn_copy_message.bind(on_release=on_copy_message)

        layout.add_widget(password_input)
        layout.add_widget(key_input)
        layout.add_widget(btn_decode)
        layout.add_widget(status_text)
        layout.add_widget(btn_copy_message)

        btn_close = Button(
            text="Close"
            ,size_hint_y=None
            ,height=40
        )
        popup = Popup(
            title="Decode Secret Message"
            ,content=layout
            ,size_hint=(0.8, 0.8)
        )

        def close_popup(instance):
            popup.dismiss()
        btn_close.bind(on_release=close_popup)

        layout.add_widget(btn_close)
        popup.open()


class SnapAStegApp(App):
    def build(self):
        return StegoUI()


if __name__ == '__main__':
    SnapAStegApp().run()
