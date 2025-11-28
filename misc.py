import requests
from datetime import datetime
import time

class Api:
    def __init__(self):
        # EN: Fetch sample product data from a public fake store API.
        # HU: Példa termékadatok lekérése egy nyilvános „fake store” API-ról.
        response = requests.get('https://fakestoreapi.com/products')
        # EN: Parse JSON response into a Python object (list of dicts).
        # HU: A JSON válasz Python objektummá alakítása (szótárak listája).
        self.products = response.json()

class Screen:
    def __init__(self, window, app_width,app_height):
        # EN: Store window reference and desired app size; compute geometry.
        # HU: Az ablak hivatkozásának és a kívánt méretnek eltárolása; geometria számítása.
        self.screen_height = None
        self.screen_width = None
        self.window = window
        self.app_width = app_width
        self.app_height = app_height
        self.screen_geometry()

    def screen_geometry(self):
        # EN: Read physical screen size from the windowing system.
        # HU: A fizikai képernyőméret lekérdezése az ablakkezelőtől.
        self.screen_width = self.window.winfo_screenwidth()
        self.screen_height = self.window.winfo_screenheight()
        # EN: Center the window: compute top-left corner (x, y).
        # HU: Középre igazítás: a bal felső sarok (x, y) koordinátáinak számítása.
        x = (self.screen_width / 2) - (self.app_width / 2)
        y = (self.screen_height / 2) - (self.app_height / 2)
        # EN: Apply width x height and position to the window geometry string.
        # HU: A szélesség x magasság és pozíció beállítása az ablak geometriáján.
        self.window.geometry(f"{self.app_width}x{self.app_height}+{int(x)}+{int(y)}")
