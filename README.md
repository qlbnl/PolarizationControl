# M-Node Polarization Control

## Overview

This repository contains the `pol_ctl` program for controlling the polarization of light. It is designed to perform polarization stability control in fiber optic testbed environments. The program assumes the availability of an electronic polarization controller (EPC) and a polarimeter accessible via USB. The current version is implemented with drivers for an OZOptics EPC-400 and a Thorlabs PAX1000 polarimeter; however, other hardware devices could be introduced as needed.

The `pol_ctrl` program performs polarization stabilization using a measurement feedback loop and a gradient ascent approach for converging on a desired state of polarization. The functions of the program may also be controlled through a text-based protocol over TCP.

## Installation
The `pol_ctl.py` script may be executed directly from the polctl folder. Alternatively, the program can be installed in your environment with

```
pip install .
```

## Usage

When first started, pol_ctl will simply enter a measurement state and report the state of polarization as read from the polarimeter. A TCP listener will start on port 6000 by default. A client may connect to this port and issue a number of commands with arguments as detailed below.

| Name         | Command  | Arguments                    |  Description                                          | Example (single line) |
| ------------ | -------- | ---------------------------- | ----------------------------------------------------- | ------- |
| Capture      | C        | [N]                          | Save the current SOP using _N_ samples.                 | C 5     |
| Transform    | T        | [theta]                      | Transform the current saved (captured) SOP by _theta_ | T 90    |
| Set          | S        | [SOP \| T \| C ] [fidelity]  | Calibrate to desired target state. SOP can be Stokes parameter of the form _S1,S2,S3_. Character _T_ is the current saved transformed value. Character _C_ is the current saved captured SOP. The _fidelity_ argument specifies the threshold to reach before the returning from the calibration routing. | S C 0.999 |
| Maintain     | M        | [SOP \| T \| C ] [fidelity]  | Same as calibrate but continue to compensate to maintain the desired target SOP. | M C 0.999 |
| Get          | G        | [ C \| T ]                   | Get the currently saved _C_ or _T_ values.            | G C |


