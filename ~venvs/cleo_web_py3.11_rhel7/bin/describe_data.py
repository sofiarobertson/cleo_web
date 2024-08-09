#!/users/sprobert/cleo_web/~venvs/cleo_web_py3.11_rhel7/bin/python3.11

from __future__ import print_function
import argparse
import os
from data_pub import get_data_snapshot

if __name__ == "__main__":

    ygor_telescope = os.getenv("YGOR_TELESCOPE")
    print("YGOR_TELESCOPE =", ygor_telescope)

    if ygor_telescope:
            parser = argparse.ArgumentParser(
                description='Obtain one sampler or parameter value and describe it')
            parser.add_argument('key', metavar='key', nargs=1,
                                help='The major device name.')
            args = parser.parse_args()
            key = args.key[0]

            ds = get_data_snapshot(key)

            if ds:
                print(ds)
            else:
                print("Call to system at '%s' timed out!"
                      % ygor_telescope)

    else:
        print("You must provide 'YGOR_TELESCOPE' for this to work.")
