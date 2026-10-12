"""A zoomable viewport whose public coordinates stay in image space."""
import copy
import math
import tkinter as tk
from PIL import Image, ImageTk


class ZoomCanvas(tk.Canvas):
    def __init__(self, *args, **kwargs):
        self.zoom = 1.0
        self.image_size = (1, 1)
        self._images = {}
        super().__init__(*args, **kwargs)

    def _view_coords(self, coords):
        return [float(v) * self.zoom for v in tk._flatten(coords)]

    def create_polygon(self, *coords, **kwargs):
        return super().create_polygon(*self._view_coords(coords), **kwargs)

    def create_rectangle(self, *coords, **kwargs):
        return super().create_rectangle(*self._view_coords(coords), **kwargs)

    def create_image(self, *coords, **kwargs):
        original = kwargs.pop('image')
        source = ImageTk.getimage(original)
        rendered = self._render_image(source, original)
        item = super().create_image(*self._view_coords(coords), image=rendered, **kwargs)
        # Keep PhotoImages alive for as long as their canvas items exist.
        self._images[item] = (source, original, rendered)
        self.image_size = source.size
        self._update_scrollregion()
        return item

    def _render_image(self, source, original):
        if self.zoom == 1.0:
            return original
        size = tuple(max(1, round(v * self.zoom)) for v in source.size)
        return ImageTk.PhotoImage(source.resize(size, Image.LANCZOS), master=self)

    def coords(self, item, *coords):
        if coords:
            return super().coords(item, *self._view_coords(coords))
        return [v / self.zoom for v in super().coords(item)]

    def delete(self, *items):
        for tag in items:
            for item in self.find_withtag(tag):
                self._images.pop(item, None)
        return super().delete(*items)

    def set_zoom(self, value):
        value = float(value)
        if not math.isfinite(value) or not 0.25 <= value <= 4.0:
            raise ValueError('Zoom must be between 0.25 and 4.0')
        if value == self.zoom:
            return
        super().scale('all', 0, 0, value / self.zoom, value / self.zoom)
        self.zoom = value
        for item, (source, original, _) in list(self._images.items()):
            rendered = self._render_image(source, original)
            super().itemconfigure(item, image=rendered)
            self._images[item] = (source, original, rendered)
        self._update_scrollregion()

    def _update_scrollregion(self):
        width, height = self.image_size
        self.configure(scrollregion=(0, 0, width * self.zoom, height * self.zoom))

    def bind(self, sequence=None, func=None, add=None):
        if callable(func) and sequence and ('Button' in sequence or 'Motion' in sequence):
            callback = func

            def func(event):
                model_event = copy.copy(event)
                model_event.x = super(ZoomCanvas, self).canvasx(event.x) / self.zoom
                model_event.y = super(ZoomCanvas, self).canvasy(event.y) / self.zoom
                return callback(model_event)

        return super().bind(sequence, func, add)

    def find_closest(self, x, y, halo=None, start=None):
        return super().find_closest(x * self.zoom, y * self.zoom, halo, start)

    def find_overlapping(self, x1, y1, x2, y2):
        return super().find_overlapping(*self._view_coords((x1, y1, x2, y2)))
