import time
import math

from flask import Flask, request
import requests
import logging
import socket
import os
logging.basicConfig(level=logging.DEBUG)

NAMESPACE = 'vpa'

PORT = 80
CPU_UNIT = 1000
MEM_TEMPLATE = "stress-ng --vm 1 --vm-bytes '{}M' --vm-hang 10 &"
CPU_TEMPLATE = "stress-ng --cpu 1 --cpu-load '{}' &"
SUCCESS_MESSAGE = "Resources allocated successfully"
app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():

    try:
        logging.info('killing previous stress-ng procceses...')
        os.system("killall -9 stress-ng")
    except Exception as e:
        logging.warning(e)
        pass

    try:

        logging.info("received new configuration from utilization-server: {}".format(
            request.form
        ))

        ram = int(request.args.get('ram'))
        command = MEM_TEMPLATE.format(ram)
        logging.info('running RAM stress-ng: "{}"'.format(command))
        os.system(command)

        # get busy dedicated cores
        cpu = int(request.args.get('cpu'))
        n_cores = math.floor(cpu / CPU_UNIT)
        for i in range(n_cores):
            command = CPU_TEMPLATE.format(100)
            logging.info('running stress-ng: "{}"'.format(command))
            os.system(command)

        # get busy extended cpu
        extended = cpu - n_cores * CPU_UNIT
        command = CPU_TEMPLATE.format(extended / 1000 * 100)
        logging.info('running stress-ng: "{}"'.format(command))
        os.system(command)

        logging.info(SUCCESS_MESSAGE)
        return SUCCESS_MESSAGE
    except Exception as e:
        logging.error(e)
        return 'An issue faces, please check out the logs.'


if __name__ == '__main__':
    # get hostname of current machine
    hostname = socket.gethostname()
    command = None

    logging.info('trying to connect to the utilization-server')
    while True:
        try:
            # register into controller and setup the stress
            controller = requests.get('http://utilization-server.{}.svc/metrics/{}/'.format(NAMESPACE, hostname))

            if controller.status_code == 404:
                logging.info(controller.content)
                time.sleep(1)
                continue

            content = controller.json()
            logging.info("got resources: {}".format(content))

            # running stress
            command = COMMAND_TEMPLATE.format(
                content.get('ram'),
                content.get('cpu'),
            )
            break

        except Exception as e:
            logging.error(e)
            exit(-1)

    logging.info('running stress-ng: "{}"'.format(command))
    os.system(command)

    logging.info("serving 'app' on port {}".format(PORT))
    app.run(host="0.0.0.0", port=PORT, debug=True, use_reloader=False)
