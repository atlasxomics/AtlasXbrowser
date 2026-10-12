"""Exercise the real Tk viewport; skip when desktop dependencies are unavailable."""
import math
import os
from types import SimpleNamespace
import unittest
from unittest.mock import patch

try:
    import tkinter as tk
    from PIL import Image, ImageTk
    from zoom_canvas import ZoomCanvas
except ImportError:
    ZoomCanvas = None


@unittest.skipUnless(ZoomCanvas is not None and os.environ.get('ATLAS_TEST_GUI') == '1',
                     'Set ATLAS_TEST_GUI=1 with Tk, Pillow and a display for viewport checks')
class ZoomCanvasTests(unittest.TestCase):
    def setUp(self):
        try:
            self.root = tk.Tk(baseName='AtlasXBrowser', className='AtlasXBrowser')
        except tk.TclError as error:
            self.skipTest(str(error))
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.canvas = ZoomCanvas(self.root, width=100, height=100)
        self.canvas.pack()
        self.photo = ImageTk.PhotoImage(Image.new('RGB', (200, 150)))
        self.image = self.canvas.create_image(0, 0, image=self.photo, anchor='nw')

    def test_image_and_overlay_scale_without_changing_model_coordinates(self):
        points = [10, 20, 30, 20, 30, 40, 10, 40]
        polygon = self.canvas.create_polygon(points, fill='red')
        rect = self.canvas.create_rectangle(10, 20, 30, 40)
        for zoom in (2.0, 0.25, 4.0, 1.0):
            self.canvas.set_zoom(zoom)
            self.assertEqual(self.canvas.coords(polygon), points)
            self.assertEqual(tk.Canvas.coords(self.canvas, polygon),
                             [v * zoom for v in points])
            self.assertEqual(self.canvas.coords(rect), [10, 20, 30, 40])
            rendered = self.canvas._images[self.image][2]
            self.assertEqual((rendered.width(), rendered.height()),
                             (round(200 * zoom), round(150 * zoom)))
        self.assertEqual(self.canvas.image_size, (200, 150))

    def test_drawing_selection_and_dragging_after_zoom_and_pan(self):
        self.canvas.set_zoom(2)
        polygon = self.canvas.create_polygon(10, 20, 30, 20, 30, 40, 10, 40,
                                             fill='red')
        self.assertEqual(self.canvas.find_closest(20, 30), (polygon,))
        self.assertIn(polygon, self.canvas.find_overlapping(15, 25, 25, 35))
        self.canvas.xview_moveto(0.4)
        self.canvas.yview_moveto(0.3)
        observed = []
        with patch.object(tk.Canvas, 'bind') as bind:
            self.canvas.bind('<Button1-Motion>', observed.append)
            callback = bind.call_args.args[1]
        original = SimpleNamespace(x=12, y=14, widget=self.canvas)
        callback(original)
        event = observed[0]
        self.assertEqual(event.x, tk.Canvas.canvasx(self.canvas, 12) / 2)
        self.assertEqual(event.y, tk.Canvas.canvasy(self.canvas, 14) / 2)
        self.assertGreater(event.x, 12 / 2)
        self.assertEqual((original.x, original.y), (12, 14))
        self.canvas.coords(polygon, event.x, event.y, 30, 20, 30, 40, 10, 40)
        self.canvas.set_zoom(1)
        self.assertEqual(self.canvas.coords(polygon)[:2], [event.x, event.y])

    def test_replacement_images_and_invalid_zoom(self):
        for value in (0, 5, math.nan, math.inf):
            with self.assertRaises(ValueError):
                self.canvas.set_zoom(value)
        self.canvas.set_zoom(2)
        self.canvas.delete('all')
        self.assertEqual(self.canvas._images, {})
        photo = ImageTk.PhotoImage(Image.new('RGB', (50, 60)))
        item = self.canvas.create_image(0, 0, image=photo, anchor='nw', tag='image')
        self.assertEqual(self.canvas.image_size, (50, 60))
        self.assertEqual(self.canvas._images[item][2].width(), 100)
        self.canvas.delete('image')
        self.assertEqual(self.canvas._images, {})

    def test_crop_and_roi_use_image_dimensions_at_any_zoom(self):
        from draggable_quad import DrawShapes
        from draggable_square import DrawSquare
        self.canvas.set_zoom(4)
        roi = DrawShapes(self.canvas, [0])
        crop = DrawSquare(self.canvas)
        self.assertEqual(self.canvas.coords(roi.current),
                         [20, 15, 180, 15, 180, 135, 20, 135])
        self.assertEqual(self.canvas.coords('crop'), [20, 15, 180, 175])
        crop.on_motion(SimpleNamespace(x=30, y=25))
        crop.on_release(None)
        self.canvas.set_zoom(0.25)
        self.assertEqual(self.canvas.coords('crop'), [30, 25, 180, 175])

    def test_application_slider_and_reset(self):
        from test_chip_geometry import load_class
        Gui = load_class('bsa_gui.py', 'Gui', {},
                         methods=['change_zoom', 'apply_zoom', 'reset_zoom'])
        gui = Gui()
        gui.newWindow = self.root
        gui.my_canvas = self.canvas
        gui.zoom_value = tk.DoubleVar(master=self.root, value=1)
        gui.zoom_label = tk.Label(self.root, text='100%')
        gui._zoom_pending = None
        gui.zoom_value.set(2)
        gui.change_zoom('2')
        self.assertEqual(gui.zoom_label.cget('text'), '200%')
        self.root.after_cancel(gui._zoom_pending)
        gui.apply_zoom()
        self.assertEqual(gui.my_canvas.zoom, 2)
        gui.reset_zoom()
        self.assertEqual(gui.my_canvas.zoom, 1)
        self.assertEqual(gui.zoom_label.cget('text'), '100%')

    def test_sidebar_survives_large_images_and_zoom_starts_hidden(self):
        from tkinter import ttk
        from test_chip_geometry import load_class
        Gui = load_class('bsa_gui.py', 'Gui',
                         {'tk': tk, 'ttk': ttk, 'ZoomCanvas': ZoomCanvas},
                         methods=['build_viewport', 'fit_window', 'change_zoom',
                                  'apply_zoom', 'reset_zoom', 'show_loaded_controls',
                                  'update_tool_scrollregion', 'resize_tool_view'])
        self.canvas.destroy()
        gui = Gui()
        # Lay out a fixed-size host without mapping a native window. This also
        # works where a sandbox prevents macOS from showing windows.
        host = tk.Frame(self.root)
        host.minsize = self.root.minsize

        def geometry(value):
            width, height = map(int, value.split('x'))
            host.place(x=0, y=0, width=width, height=height)

        host.geometry = geometry
        gui.newWindow = host
        gui.screen_width, gui.screen_height = 1200, 900
        gui.fit_window(2000)
        gui.build_viewport()
        for name in ('Rotation', 'Cropping', 'ROI', 'Overlay'):
            tk.LabelFrame(gui.right_canvas, text=name, width=260, height=180).pack(
                anchor='w', padx=12, pady=5)
        self.root.update_idletasks()
        self.assertEqual(gui.zoom_frame.winfo_manager(), '')
        self.assertFalse(gui.image_loaded)
        self.assertEqual(gui.sidebar.winfo_width(), 340)
        self.assertEqual(host.winfo_width(), 1200)
        gui.my_canvas.config(width=3000)
        gui.show_loaded_controls()
        self.root.update_idletasks()
        self.assertEqual(gui.zoom_frame.winfo_manager(), 'grid')
        self.assertTrue(gui.image_loaded)
        self.assertEqual(gui.sidebar.winfo_width(), 340)
        self.assertGreater(gui.image_frame.winfo_width(), 0)
        self.assertLess(gui.zoom_frame.winfo_y(), gui.tool_view.winfo_y())
        self.assertLessEqual(gui.sidebar.winfo_x() + gui.sidebar.winfo_width(),
                             host.winfo_width())
        host.geometry('640x400')
        self.root.update_idletasks()
        self.assertEqual(gui.sidebar.winfo_width(), 340)
        self.assertGreater(gui.image_frame.winfo_width(), 0)
        self.assertLess(gui.tool_view.yview()[1], 1)


if __name__ == '__main__':
    unittest.main()
