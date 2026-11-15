# Smart Screen

Team 13's project in the Technion course 236333, Project in IoT.

## Details about the project

A small table-side touch screen that shows useful information at a glance (time and date,
weather, room temperature and humidity, today's schedule) and makes sure reminders are not
missed: when a reminder is due, it takes over the screen until someone confirms it.

The screen is managed from a web app, so the schedule and the settings can change without
touching the device.

The project is at an early stage. This file will grow with it.

## Folder description

* `ESP32`: source code for the ESP32 side (firmware): the touch screen, the sensors, the
  Done button, the light and the sound.
* `web_app`: the web app that manages the screen, and the server code behind it.
* `Documentation`: wiring diagram + basic operating instructions.
* `Unit Tests`: tests for individual hardware components (input / output devices).
* `Parameters`: description of the parameters and settings that can be modified in the code.
* `Assets`: sounds, images, and the 3D files of the enclosure.

This project is part of ICST - The Interdisciplinary Center for Smart Technologies, Taub Faculty of Computer Science, Technion
https://icst.cs.technion.ac.il/
