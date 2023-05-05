# Open Opal C1

Examples to control the [Opal C1](https://opalcamera.com/) from within python. This repository has been created because
Opal currently does not provide software control of the camera under Windows. Controlling the camera parameters is
crucial for computer vision applications like in robotics or exhibitions.

Since Opal C1 is based on
the [LCM48](https://docs.luxonis.com/projects/hardware/en/latest/pages/articles/sensors/imx582.html) sensor, integrated
in the [Luxonis](https://www.luxonis.com/) hardware system, it is possible to use the camera as an (OAK-1
MAX)[https://docs.luxonis.com/projects/hardware/en/latest/pages/NG9096max.html#ng9096max]. To read the camera image and
control the camera parameters it is possible to use the [depthai](https://docs.luxonis.com/en/latest/) python framework.

### Installation

It is recommended to use a modern python version like `3.9` and creating
a [virtual environment](https://docs.python.org/3/library/venv.html). To install all the dependencies, run the following
command.

```bash
pip install -r requirements.txt
```

### Usage

Many of the demos showed here are following directly the depthai python demos. Usually only the resolution and some
camera specific parameters have been adapted.

tbd

### About

Developed by cansik 2023