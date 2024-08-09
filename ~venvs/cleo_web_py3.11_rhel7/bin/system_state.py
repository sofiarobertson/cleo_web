#!/users/sprobert/cleo_web/~venvs/cleo_web_py3.11_rhel7/bin/python3.11
######################################################################
#  system_state.py - Subscribes to a list of system keys. For now,
#  read those keys from a file, and save a log of all the
#  results. More later.
#
#  Copyright (C) 2018 Associated Universities, Inc. Washington DC, USA.
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful, but
#  WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#  General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 675 Mass Ave, Cambridge, MA 02139, USA.
#
#  Correspondence concerning GBT software should be addressed as follows:
#  GBT Operations
#  National Radio Astronomy Observatory
#  P. O. Box 2
#  Green Bank, WV 24944-0002 USA
#
######################################################################

from __future__ import print_function
from future import standard_library
standard_library.install_aliases()
from builtins import str
import argparse
import sys
import os
import signal
import configparser
import queue
import logging
import redis
import msgpack

from data_pub import Portal
from data_pub import get_device_keys
from datetime import datetime, timedelta

log = None
handler = None
last_ready = False
channel = queue.Queue(500)


def read_key_config_file(filename):
    """Reads the configuration file, and loads up the conf dictionary with
    devices to listen to and the parameters to listen for.

    """
    conf = {"keys": {},
            "BadDevices": set(),
            "BadDeviceCheckPeriod": timedelta(minutes=60),
            "YgorTelescope": os.getenv('YGOR_TELESCOPE')}

    try:
        config = configparser.ConfigParser()
        # keep case of keys and values
        config.optionxform = str
        log.debug("in read_key_config_file(%s)" % filename)
        log.debug("reading config file")
        config.read(filename)

        log.debug("attempting to set environment")
        try:
            ygor_telescope = config.get("System", "YgorTelescope")
            conf["YgorTelescope"] = ygor_telescope
            os.environ["YGOR_TELESCOPE"] = ygor_telescope
            check_period = int(config.get("System", "bad_device_check_period"))
            conf["BadDeviceCheckPeriod"] = timedelta(minutes=check_period)
        except configparser.NoSectionError:
            pass
        except configparser.NoOptionError:
            pass
        except ValueError as e:
            # protect from our int cast above
            log.exception(e)

        log.debug("reading devices")
        devices = config.sections()
        # remove "System", it does not name a device.
        devices.remove("System")

        for device in devices:
            subdevices = config.items(device)

            for subdev in subdevices:
                devname = device + "." + subdev[0]

                if devname not in conf["keys"]:
                    conf["keys"][devname] = []

                if subdev[1] == "all":
                    params = get_device_keys(device, subdev[0], timeout=1000)

                    if not params:
                        conf["BadDevices"].add(devname)
                        log.warning("Device %s does not appear to be up!"
                                    % devname)
                else:
                    # TBF: If specified, they are parameters.
                    ps = subdev[1].split(',')
                    params = [devname + ":P:" + x for x in ps]

                # for now, reject any data & sampler keys, they are
                # high volume
                params = [x for x in params if ":P:" in x]
                log.debug("read parameters %s" % str(params))

                for p in params:
                    conf["keys"][devname].append(p)
    except configparser.Error as e:
        log.debug(str(e))
        return {}

    log.debug("exiting")
    return conf


def log_item(log_file, item):
    """Logs an item to the named log file."""

    if log_file is not None:
        with open(log_file, 'a') as lf:
            lf.write(str(item) + '\n')


def log_item_to_redis(rclient, item):
    def put_val(key, val):
        rclient.lpush(key, val)
        rclient.ltrim(key, 0, 50000)

    # the log format is specific, so if it is not met item[1], the log
    # item, will be None.
    if rclient is not None and len(item) == 2 and item[1] is not None:
        try:
            key, val = item
            put_val(key, val)
        except redis.ResponseError:
            rclient.delete(key)
            put_val(key, val)


def encode_item(item):
    encoded = None

    if len(item) == 3:
        ts, key, value = item
        val = {}
        val["time"] = ts.isoformat()
        val["val"] = value
        encoded = msgpack.dumps(val)

    return (key, encoded)


def print_default_item(time, key, val):
    """The default printer. Prints a simple item, i.e. 'state' or 'status'"""
    try:
        print("%sZ--%s--%s" % (time.isoformat(), key, str(val)))
    except TypeError:
        log.error("Type Error printing %s, %s", key, str(val))
    except KeyError:
        log.error("Key Error printing %s, %s", key, str(val))


def print_dict_item(time, key, val):
    try:
        print("%sZ--%s:" % (time.isoformat(), key))

        for key in list(val.keys()):
            print("{0:{fill}{align}16}".format(str(key),
                                               fill=' ', align=">"), end=' ')
            print(":", end=' ')
            print("{0:{fill}{align}16}".format(str(val[key]),
                                               fill=' ', align="<"))

    except TypeError:
        log.error("Type Error printing %s, %s", key, str(val))
    except KeyError:
        log.error("Key Error printing %s, %s", key, str(val))


def print_players(time, key, val):
    try:
        print("%sZ--%s: (" % (time.isoformat(), key), end=' ')

        for i in val:
            for k in i:
                n = i[k]

                if len(n) == 0:
                    break

                if k == "player":
                    print("(%s," % str(n), end=' ')

                if k == "host":
                    print("%s)" % str(n), end=' ')
        print(")")
    except TypeError:
        log.error("Type Error printing %s, %s", key, str(val))
    except KeyError:
        log.error("Key Error printing %s, %s", key, str(val))


def print_modes(time, key, val):
    try:
        print("%sZ--%s: (" % (time.isoformat(), key), end=' ')

        for i in val:
            for k in i:
                n = i[k]

                if len(n) > 0:
                    print("%s" % str(n), end=' ')
                else:
                    break

        print(")")
    except TypeError:
        log.error("Type Error printing %s, %s", key, str(val))
    except KeyError:
        log.error("Key Error printing %s, %s", key, str(val))


# Some common non-trivial parameters
printers = {"subsystemSelect": print_dict_item,
            "startTime": print_dict_item,
            "requestedStartTime": print_dict_item,
            "scanLength": print_dict_item,
            "list_available_players": print_players,
            "list_active_players": print_players,
            "list_btl_modes": print_modes}


def print_item(item):
    """Prints an item to the console."""
    global printers
    global last_ready
    time, key, val = item
    pn = key.split(":")[-1]

    # To make it easier to differentiate between spurts of activates
    # print a space when the previous state was Ready and the current
    # one Activating. TBF, this is simplistic but may do for now.
    if pn == "state":
        if last_ready and val == "Activating":
            print()
            last_ready = False
        elif val == "Ready":
            last_ready = True
        else:
            last_ready = False

    # Choose the best printer for the parameter.
    if pn in printers:
        cp = printers[pn]
    else:
        cp = print_default_item

    cp(time, key, val)


def signal_handler(sig, frame):
    global done

    if sig == signal.SIGHUP:
        sys.exit()

    if sig == signal.SIGINT:
        channel.put((-1, -1, -1))
        log.info("Received SIGINT, terminating system state monitor.")


def callback_function(time, key, value):
    channel.put((time, key, value))


# If the config reader finds 'all' for parameters it needs to query
# the device for the parametes. If it doesn't get a response the
# device is placed into a 'BadDevices' list. This function is called
# to periodically attempt to connect, since the Portal will have never
# attempted itself.

def check_bad_devices(mp, config):
    still_bad = set()

    for device in config["BadDevices"]:
        log.debug("bad device: %s", device)
        major, minor = device.split(".")

        # 2 possibilities: 'all' keys were specified, in which case
        # config["keys"][device] will be [], need to fill it

        if len(config["keys"][device]) == 0:
            params = get_device_keys(major, minor, 500)

            # params will be [] if no connection.
            if len(params) == 0:
                log.debug("still bad device 1, %s", device)
                still_bad.add(device)
                continue

            params = [x for x in params if ":P:" in x]

            for key in params:
                config["keys"][device].append(key)

            log.info("Device is back: %s", device)

        # or there *are* keys, but possibly still no device. Note that
        # if the above succeeds for an 'all' manager, then this loop
        # will subscribe it.

        for key in config["keys"][device]:
            success, msg = mp.subscribe(key, callback_function)

            if success:
                log.info("Device is back: %s", device)
            else:
                log.debug("still bad device 2, %s", device)
                still_bad.add(device)
                break  # no sense trying the other keys

    config["BadDevices"] = still_bad
    return config


def main(config_file, log_file, redis_server, silent):
    """
    Subcribes to the ScanCoordinator's and the give device's log
    streams, and prints the log stream to stdout. Call with the minor
    VEGAS device name on command line to work with that manager's log
    stream.

    """
    log.debug("in main(%s, %s, %s)" %
              (config_file, str(log_file), str(redis_server)))
    rc = None
    log.debug("set interrupt handler.")
    def_int_hndlr = signal.signal(signal.SIGINT, signal_handler)
    log.info("reading configuration file")
    configuration = read_key_config_file(config_file)
    log.debug("configuration map: %s", str(configuration))
    log.info("creating portal for %s" % configuration["YgorTelescope"])
    mp = Portal(configuration["YgorTelescope"])
    log.debug("portal created.")
    log.info("subscribing to keys:")

    for device in configuration["keys"]:
        for key in configuration["keys"][device]:
            log.info("key = %s" % key)
            success, msg = mp.subscribe(key, callback_function)

            if not success:
                log.warning("Subscribe failed: %s", msg)

                if "is not known" in msg:
                    # perhaps the device is down; add to "BadDevices" for
                    # future attempts to connect.
                    configuration["BadDevices"].add(device)
                    log.debug("added %s to BadDevices", device)
                    break

    log.debug("creating redis server")

    if redis_server is not None:
        host, port = redis_server.split(":")
        port = int(port)
        rc = redis.Redis(host=host, port=port)

    log.debug("dropping into main loop")
    last_bad_device_check = datetime.utcnow()
    check_interval = configuration["BadDeviceCheckPeriod"]
    log.debug("next bad device check at %s",
              last_bad_device_check + check_interval)

    while True:
        try:
            item = channel.get(True, 2)
            log.debug("item = %s", str(item))

            if item == (-1, -1, -1):
                log.debug("busting out...")
                break

            log_item(log_file, item)

            if not silent:
                print_item(item)

            log_item_to_redis(rc, encode_item(item))
        except queue.Empty:
            pass

        check_p = datetime.utcnow()

        if check_p > (last_bad_device_check + check_interval):
            log.debug("Bad device check, before: %s",
                      configuration["BadDevices"])
            configuration = check_bad_devices(mp, configuration)
            log.debug("after: %s", configuration["BadDevices"])
            last_bad_device_check = check_p
            log.debug("next bad device check at: %s",
                      last_bad_device_check + check_interval)

    log.info("Terminating main loop...")
    mp.stop()
    signal.signal(signal.SIGINT, def_int_hndlr)


if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        description='Runs a system state monitor and logger')
    parser.add_argument('-c', '--config', default='sys_mon.conf',
                        help='Configuration file.',
                        type=str)
    parser.add_argument('-o', '--log_output', default=None,
                        help='The output log file.',
                        type=str)
    parser.add_argument('-r', '--redis', default=None,
                        help='The redis server, host:port',
                        type=str)
    parser.add_argument('-v', '--verbose', default=False,
                        help='Enables debugging output',
                        action='store_true')
    parser.add_argument('-vv', '--vverbose', default=False,
                        help='More extensive debugging messages',
                        action='store_true')
    parser.add_argument('-s', '--silent', default=False,
                        help="Do not output to the console",
                        action='store_true')

    args = parser.parse_args()

    if args.verbose:
        print("log level: INFO")
        logging.basicConfig(level=logging.INFO)
    elif args.vverbose:
        print("log level: DEBUG")
        logging.basicConfig(level=logging.DEBUG)
    else:
        print("log level: WARNING")
        logging.basicConfig(level=logging.WARNING)

    log = logging.getLogger("system_state")
    # handler = logging.StreamHandler()
    # log.addHandler(handler)

    config_file = args.config
    log_file = args.log_output
    redis_server = args.redis
    silent = False

    if args.silent:
        silent = True

    print("config_file =", config_file)
    print("log_file =", log_file)
    print("redis_server =", redis_server)
    print("silent =", silent)

    main(config_file, log_file, redis_server, silent)
