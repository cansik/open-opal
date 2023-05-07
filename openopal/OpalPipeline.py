import threading
from datetime import timedelta
from typing import Optional, List, Callable

import cv2
import depthai as dai
import pyvirtualcam


class OpalPipeline:
    def __init__(self):
        self.input_width = 3840
        self.input_height = 2160

        self.on_new_frame: Optional[Callable[["OpalPipeline"], None]] = None

        # settings
        self._focus_mode: dai.RawCameraControl.AutoFocusMode = dai.RawCameraControl.AutoFocusMode.AUTO
        self._manual_lens_pos: int = 0

        self._auto_exposure: bool = True
        self._exposure: timedelta = timedelta(microseconds=30)
        self._iso_sensitivity: int = 400

        self._auto_white_balance: bool = True
        self._white_balance: int = 1000

        self._flip_channels: bool = False

        # pipeline
        self.pipeline = dai.Pipeline()

        # camera specific parameters
        self.cam = self.pipeline.create(dai.node.ColorCamera)
        self.cam.setBoardSocket(dai.CameraBoardSocket.RGB)
        self.cam.setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
        self.cam.setVideoSize(self.input_width, self.input_height)
        self.cam.setColorOrder(dai.ColorCameraProperties.ColorOrder.BGR)
        # self.cam.setIspScale(1, 2)
        self.cam.setInterleaved(False)

        self.rgb_stream_name = "rgb"
        self.x_out = self.pipeline.create(dai.node.XLinkOut)
        self.x_out.setStreamName(self.rgb_stream_name)
        self.cam.video.link(self.x_out.input)

        self.isp_stream_name = "isp"
        self.isp_out = self.pipeline.create(dai.node.XLinkOut)
        self.isp_out.setStreamName(self.isp_stream_name)
        self.cam.isp.link(self.isp_out.input)

        self.control_in_name = "control_in"
        self.control_in = self.pipeline.create(dai.node.XLinkIn)
        self.control_in.setStreamName(self.control_in_name)
        self.control_in.out.link(self.cam.inputControl)

        self.control_queue: Optional[dai.DataInputQueue] = None

        self.camera_thread: Optional[threading.Thread] = None
        self._running_flag = False

        self._is_camera_running = False

    def start(self):
        self._running_flag = True
        self.camera_thread = threading.Thread(daemon=True, target=self._camera_loop)
        self.camera_thread.start()

    def stop(self):
        if self.camera_thread is not None:
            self._running_flag = False
            self.camera_thread.join(5000)

    def _camera_loop(self):
        with dai.Device(self.pipeline) as device, \
                pyvirtualcam.Camera(width=self.input_width, height=self.input_height, fps=30) as uvc:
            self._is_camera_running = True

            print('Connected cameras:', device.getConnectedCameraFeatures())
            # Print out usb speed
            print('Usb speed:', device.getUsbSpeed().name)
            # Bootloader version
            if device.getBootloaderVersion() is not None:
                print('Bootloader version:', device.getBootloaderVersion())
            # Device name
            print('Device name:', device.getDeviceName())

            self.control_queue = device.getInputQueue(self.control_in_name)
            rgb_queue = device.getOutputQueue(name=self.rgb_stream_name, maxSize=4, blocking=False)
            isp_queue = device.getOutputQueue(name=self.isp_stream_name, maxSize=1, blocking=False)

            while self._running_flag:
                isp_frames: List[dai.ImgFrame] = isp_queue.tryGetAll()
                for isp_frame in isp_frames:
                    self._manual_lens_pos = isp_frame.getLensPosition()
                    self._iso_sensitivity = isp_frame.getSensitivity()
                    self._exposure = isp_frame.getExposureTime()
                    self._white_balance = isp_frame.getColorTemperature()

                frame = rgb_queue.get().getCvFrame()

                if self._flip_channels:
                    frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

                uvc.send(frame)

                if self.on_new_frame is not None:
                    self.on_new_frame(self)

            print("shutting down camera")
            self._is_camera_running = False

    def get_flip_channels(self) -> bool:
        return self._flip_channels

    def set_flip_channels(self, value: bool):
        self._flip_channels = value

    def get_camera_state(self) -> str:
        if self._is_camera_running:
            return "running"
        else:
            return "starting up..."

    def get_auto_focus(self) -> bool:
        return self._focus_mode == dai.RawCameraControl.AutoFocusMode.AUTO

    def set_auto_focus(self, value: bool):
        if not self._is_camera_running:
            return

        print(f"setting auto focus to: {value}")
        ctrl = dai.CameraControl()
        if value:
            self._focus_mode = dai.RawCameraControl.AutoFocusMode.AUTO
            ctrl.setAutoFocusMode(dai.RawCameraControl.AutoFocusMode.AUTO)
            ctrl.setAutoFocusTrigger()
        else:
            self._focus_mode = dai.RawCameraControl.AutoFocusMode.OFF
            ctrl.setAutoFocusMode(dai.RawCameraControl.AutoFocusMode.OFF)
        self.control_queue.send(ctrl)

    def get_manual_lens_pos(self) -> int:
        return self._manual_lens_pos

    def set_manual_lens_pose(self, position: int):
        ctrl = dai.CameraControl()

        position = max(0, min(255, position))

        ctrl.setManualFocus(position)
        self.control_queue.send(ctrl)

    def get_auto_exposure(self) -> bool:
        return self._auto_exposure

    def set_auto_exposure(self, value: bool):
        if not self._is_camera_running:
            return

        print(f"setting auto exposure to: {value}")
        ctrl = dai.CameraControl()
        self._auto_exposure = value
        if value:
            ctrl.setAutoExposureEnable()
        else:
            ctrl.setManualExposure(self._exposure, self._iso_sensitivity)
        self.control_queue.send(ctrl)

    def get_exposure(self) -> int:
        return int(self._exposure.total_seconds() * 1000 * 1000)

    def set_exposure(self, value: int):
        if not self._is_camera_running:
            return

        ctrl = dai.CameraControl()
        value = max(1, min(60 * 1000 * 1000, value))
        exposure = timedelta(microseconds=value)
        ctrl.setManualExposure(exposure, self._iso_sensitivity)
        self.control_queue.send(ctrl)

    def get_iso_sensitivity(self) -> int:
        return self._iso_sensitivity

    def set_iso_sensitivity(self, value: int):
        if not self._is_camera_running:
            return

        ctrl = dai.CameraControl()
        value = max(100, min(1600, value))
        ctrl.setManualExposure(self._exposure, value)
        self.control_queue.send(ctrl)

    def get_auto_white_balance(self) -> bool:
        return self._auto_white_balance

    def set_auto_white_balance(self, value: bool):
        if not self._is_camera_running:
            return

        print(f"setting auto white balance to: {value}")
        ctrl = dai.CameraControl()
        self._auto_white_balance = value
        if value:
            ctrl.setAutoWhiteBalanceMode(dai.RawCameraControl.AutoWhiteBalanceMode.AUTO)
        else:
            ctrl.setAutoWhiteBalanceMode(dai.RawCameraControl.AutoWhiteBalanceMode.OFF)
        self.control_queue.send(ctrl)

    def get_white_balance(self) -> int:
        return self._white_balance

    def set_white_balance(self, value: int):
        if not self._is_camera_running:
            return

        ctrl = dai.CameraControl()
        value = max(1000, min(12000, value))
        ctrl.setManualWhiteBalance(value)
        self.control_queue.send(ctrl)
