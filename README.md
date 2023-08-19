# videorecorder

## description
The idea of this project is to make a simple videorecorder for car using RaspberryPi Zero.
The basic functionality assumes:
 - capture video in realtime by RPI camera module
 - write videofootage by chunks with given duration
 - allow control by user via web-interface (stream the video into browser, optionally)

The choice of Raspberry Pi Zero is not determined by any analysis of single-board computers.
I bought it a 5 years ago, had played enough and since that time the RPI Zero is gathering a dust on my table.

Instead of attach and setup a touch-screen I've choosen web-interface as a solution to control my videorecorder
because something bad happened with HDMI port and any display when I plug it to my RPI shows only a blank screen
(sometimes the message 'no signal').


## architecture
The initial design is depictured below.

![Architecture](./assets/architecture.drawio.svg)

The Camera class is responsible for acquiring videostream from RPI camera module. It starts a worker thread to capture frames and put these frames into queues. The one of the queues 
is a frames' source for Flask application, the second one is a source for the instance of FileWriter class. The Flask application is responsible for serving user requests to stream 
video and setup videorecorder. The video is streamed with MJPEG protocol, Flask framework provides support of that with concept of 'generator' function 
([see here](https://blog.miguelgrinberg.com/post/video-streaming-with-flask)) . The class FileWriter provides functionality to merge received frames into media-container (AVI only).
The instance of FileWriter starts worker thread which pull frames from queue and process them - the frame taken from queue is resized if needed and appended to media-container.

### Design changes (07 Jul 2023)
During the experimental operation it was found that Flask application (http server) becomes irresponsive when using camera resolution 1024 x 768. 
I decided to simplify design by eliminating the streaming of the video into browser. Also it was revealed that camera is able to give only 2 frames per second.
I'm going to explore the [picamera API documentation](https://picamera.readthedocs.io/en/release-1.13/index.html) to get more understanding and might be I will manage to eliminate limitation of 2 FPS.


### run as a service
It looks obvious that the videorecorder should be started automatically when system startup. There are a few ways to do it:
- rc.local
- .bashrc
- init.d
- systemd
- cron 

[Run a program on Raspberry Pi at startup](https://www.dexterindustries.com/howto/run-a-program-on-your-raspberry-pi-at-startup/?ref=nickjvturner.com)

Because our service is not trivial and rely on the network and storage subsystems I choose the **systemd** because it allows 
to define when a service starts, which resources it is allowed to access and which dependencies need to be met.

### systemd units
The resources that systemd manages are called **units**. There are different types of them: services, sockets, targets, etc. Units are described
in special configuration files that called unit files. The systemd manager scans [many directories to load unit files](https://man7.org/linux/man-pages/man5/systemd.unit.5.html) .

### system and user services
systemd supports both *system* and *user* services. Regular services are usually found at /etc/systemd/system/ and managed with root privileges.
The other type of systemd services is user ones. They are designed to be run by unprivileged users.

Our service is going to be called 'videorecorder.service' and the corresponding unit file would be placed in ~/.config/systemd/user/videorecorder.service :

```
[Unit]
Description=videorecorder
After=network.target

[Service]
WorkingDirectory=/home/pi/videorecorder
ExecStart=python3 videorecorder.py -f /media/pi/REMOVABLE/output
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
```

Depending on systemd version it might be necessary to reload the user daemon so that our service could be found and started.

`$ systemctl --user daemon-reload`

To start the service

`$ systemctl --user start videorecorder`

And to run it after every boot

`$ systemctl --user enable videorecorder`
