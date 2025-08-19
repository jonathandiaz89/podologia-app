from kivy.uix.textinput import TextInput
import re

class RUTTextInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        allowed_chars = "0123456789kK-"
        s = ''.join([c for c in substring if c in allowed_chars])
        return super().insert_text(s, from_undo=from_undo)

class PhoneTextInput(TextInput):
    def insert_text(self, substring, from_undo=False):
        allowed_chars = "0123456789+"
        s = ''.join([c for c in substring if c in allowed_chars])
        return super().insert_text(s, from_undo=from_undo)