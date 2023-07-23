import argparse
import logging

from flask import Flask
from flask import render_template

import psutil
from os import getpid

from camcorder import Camcorder

my_process = psutil.Process(getpid())
app = Flask(__name__)

camcorder = None


@app.route('/')
def index():
    """Home page"""
    return render_template("index.html")
    
@app.route('/resources_usage')
def resources_usage():
    """Resource usage"""
    return render_template("resources.html", pname=my_process.name(), pid=my_process.pid, cpu=my_process.cpu_percent(interval=0.5), mem=my_process.memory_percent())

if __name__ == '__main__':
    logging.basicConfig(format='%(asctime)s - %(message)s', level=logging.DEBUG)
    
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--port", type=int, default=9000, help="port, the server listen to (1024 to 65535)")
    args = vars(ap.parse_args())
    
    resolution = (1024, 768)
    framerate = 2
    
    logging.info("camcorder - start")
    camcorder = Camcorder(resolution, framerate, 'output', max_fragment_duration=900)
    camcorder.start()
    logging.debug("camcorder - started")
    
       
    logging.info("application - start")
    # here is an explanation of arguments
    # https://www.twilio.com/blog/how-run-flask-application
    app.run(host='0.0.0.0', port=args["port"], debug=True, threaded=True, use_reloader=False)
    
    logging.info("application - stopped")
    camcorder.stop()
    logging.debug("camcorder - stopped")
