import threading
from typing import Optional, Sequence, List, Callable

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
            isp_queue = device.getOutputQueue(self.isp_stream_name, maxSize=1, blocking=False)

            while self._running_flag:
                isp_frames: List[dai.ImgFrame] = isp_queue.tryGetAll()
                for isp_frame in isp_frames:
                    self._manual_lens_pos = isp_frame.getLensPosition()

                frame = rgb_queue.get().getCvFrame()
                uvc.send(frame)
                # time.sleep(0.01)

                if self.on_new_frame is not None:
                    self.on_new_frame(self)

            print("shutting down camera")
            self._is_camera_running = False

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
