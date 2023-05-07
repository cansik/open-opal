import gc
from typing import Optional

import nanogui as ng

from openopal.OpalPipeline import OpalPipeline


class ControlUI:
    def __init__(self):
        self.width = 500
        self.height = 700

        self.screen: Optional[ng.Screen] = None
        self.window: Optional[ng.Window] = None
        self.gui: Optional[ng.FormHelper] = None

        self.pipeline = OpalPipeline()
        self.pipeline.on_new_frame = self._on_new_frame

    def run(self):
        ng.init()
        self.screen = ng.Screen(ng.Vector2i(self.width, self.height), "Open Opal")

        self.gui = ng.FormHelper(self.screen)

        self.window = self.gui.add_window(ng.Vector2i(0, 0), "Open Opal")
        self.window.set_width(self.width)
        self.window.set_height(self.height)

        self._create_ui()

        self.screen.set_visible(True)
        self.screen.perform_layout()

        self.screen.set_resize_callback(self._on_resize)

        # starting camera
        self.pipeline.start()
        ng.mainloop(refresh=0)
        self.pipeline.stop()

        self.screen = self.gui = self.window = None
        gc.collect()
        ng.shutdown()

    def _on_new_frame(self, pipeline: OpalPipeline):
        self.gui.refresh()

    def _on_resize(self, *args):
        self.window.set_width(self.screen.width())
        self.window.set_height(self.screen.height())
        self.screen.perform_layout()

    def _create_ui(self):
        def _none_setter(*args):
            pass

        self.gui.add_group("Camera")
        self.gui.add_string_variable("State", _none_setter, self.pipeline.get_camera_state, editable=False)

        self.gui.add_group("Controls")
        self.gui.add_bool_variable("Flip Channels", self.pipeline.set_flip_channels, self.pipeline.get_flip_channels)

        self.gui.add_bool_variable("Auto Focus", self.pipeline.set_auto_focus, self.pipeline.get_auto_focus)
        self.gui.add_int_variable("Lens Position", self.pipeline.set_manual_lens_pose, self.pipeline.get_manual_lens_pos)

        self.gui.add_bool_variable("Auto Exposure", self.pipeline.set_auto_exposure, self.pipeline.get_auto_exposure)
        self.gui.add_int_variable("Exposure", self.pipeline.set_exposure, self.pipeline.get_exposure)
        self.gui.add_int_variable("ISO", self.pipeline.set_iso_sensitivity, self.pipeline.get_iso_sensitivity)

        self.gui.add_bool_variable("Auto White Balance", self.pipeline.set_auto_white_balance, self.pipeline.get_auto_white_balance)
        self.gui.add_int_variable("White Balance", self.pipeline.set_white_balance, self.pipeline.get_white_balance)
