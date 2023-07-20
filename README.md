# videorecorder
The idea of this project is to make a simple videorecorder for car using RaspberryPi Zero.
The basic functionality assumes:
 - capture video in realtime by RPI camera module
 - write videofootage by chunks with given duration
 - allow control by user via web-interface (stream the video into browser, optionally)

The choice of Raspberry Pi Zero is not determined by any anakysis of single-board computers.
I bought it a 5 years ago, had played enough and since that time the RPI Zero is gathering a dust on my table.

Instead of attach and setup a touch-screen I've choosen web-interface as a solution to control my videorecorder
because something bad happened with HDMI port and any display when I plug it to my RPI shows only a blank screen
(sometimes the message 'no segnal').

