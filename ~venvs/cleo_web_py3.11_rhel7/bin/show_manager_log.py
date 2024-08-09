#!/users/sprobert/cleo_web/~venvs/cleo_web_py3.11_rhel7/bin/python3.11

from __future__ import print_function
from data_pub.portal import Portal
from data_pub import coerce_to_string
from time import sleep

import argparse


def callback(a, b, c):
    print(coerce_to_string(c))


def main():
    """Subcribes to a manager's log stream, and prints the log stream to
    stdout. Call with major (and optionally minor) device name on
    command line to follow that manager's log stream.

    """

    # get the arguments: major [minor]
    parser = argparse.ArgumentParser(
        description='Obtain published keys from a named device')
    parser.add_argument('major', metavar='maj', nargs=1,
                        help='The major device name.')
    parser.add_argument('minor', metavar='min', nargs='?', default='',
                        help='The minor device name.')
    parser.add_argument('-t', '--telescope', default='',
                        help='telescope installation directory')
    args = parser.parse_args()
    major = args.major[0]

    # Devices that are not subdevices (usually?) have same major and
    # minor device names, and may be specified with only one name.
    if not args.minor:
        minor = major
    else:
        minor = args.minor

    mp = None

    if args.telescope:
        inst_dir = args.telescope
        print("Using telescope installation", inst_dir)
        mp = Portal(inst_dir)
    else:
        mp = Portal()

    # subscription keys. We're interested in the 'cout' and 'cerr'
    # streams from the manager, and the NEW_INTERFACE message from the
    # directory service:
    keys = ["%s.%s:cout" % (major, minor),
            "%s.%s:cerr" % (major, minor),
            "%s.%s:Log" % (major, minor)]

    for key in keys:
        mp.subscribe(key, callback)

    while True:
        try:
            sleep(1)
        except KeyboardInterrupt:
            mp.stop()
            break


if __name__ == "__main__":
    main()
