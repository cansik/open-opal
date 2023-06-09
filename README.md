# Open Opal

Examples to control the [Opal C1](https://opalcamera.com/) from within python. This repository has been created because
there is currently no software to control the camera under Windows. Controlling the camera parameters is
crucial for computer vision applications like in robotics or exhibitions.

Since Opal C1 is based on the [LCM48](https://docs.luxonis.com/projects/hardware/en/latest/pages/articles/sensors/imx582.html) sensor, integrated
in the [Luxonis](https://www.luxonis.com/) hardware system, it is possible to use the camera as an [OAK-1
MAX](https://docs.luxonis.com/projects/hardware/en/latest/pages/NG9096max.html#ng9096max). To read the camera image and
control the camera parameters it is possible to use the [depthai](https://docs.luxonis.com/en/latest/) python framework.

### Camera Controller

As a quick demonstration, an application has been created that streams the Opal 4k stream into [OBS](https://obsproject.com/).
Just download the executable and run it. It currently is only possible to set camera parameters like the auto-focus, lens distance, exposure and white balance. The applications has been tested on Windows x64 and MacOS arm64.

![Demo](assets/demo.jpg)

*Basic example that streams the Opal C1 4K stream into OBS.*

A prebuilt binrary is available from the [releases](https://github.com/cansik/open-opal-c1/releases/tag/v0.1.0).
To allow pyvirtualcam to run, have a look at its [virtual cameras](https://github.com/letmaik/pyvirtualcam#supported-virtual-cameras) section.

⚠️ *This is just a [proof of concept](https://en.wikipedia.org/wiki/Proof_of_concept) application and in now way intended to be used in production.*

#### Build

To build the app yourself, please [install](#Installation) the dependencies and use the following command.

```
python setup.py distribute
```

### Installation

It is recommended to use a modern python version like `3.10` and creating
a [virtual environment](https://docs.python.org/3/library/venv.html). To install all the dependencies, run the following
command.

```bash
pip install -r requirements.txt
```

### Demos

Many of the demos showed here are following directly the [depthai python examples](https://github.com/luxonis/depthai-python/tree/main/examples). Usually only the resolution and some camera specific parameters have been adapted.

🌿 More demo's are coming soon.

#### Preview Demo

This demo just opens an opencv window and displays the 4k stream.

```
python demos/preview-demo.py
```

### About

Created by cansik in 2023 as a proof of concept - I am in no way associated with Opal Camera.
