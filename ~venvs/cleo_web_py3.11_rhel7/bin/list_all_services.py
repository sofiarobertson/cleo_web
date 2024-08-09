#!/users/sprobert/cleo_web/~venvs/cleo_web_py3.11_rhel7/bin/python3.11
######################################################################
#
#  list_all_services.py -- Requests a list of all service URLs from
#  the directory service.
#
#  Usage:
#      list_all_services.py
#
#  Copyright (C) 2012 Associated Universities, Inc. Washington DC, USA.
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
import zmq
from data_pub import get_directory_endpoints, to_request_protobuf
from zmq import Poller, POLLIN


def main():
    """ main method """

    context = zmq.Context(1)
    request = context.socket(zmq.REQ)
    req_url = get_directory_endpoints('request')
    print("request URL =", req_url)
    request.connect(req_url)
    poller = Poller()
    poller.register(request, flags=POLLIN)
    request.send(b"LIST")

    # don't wait forever.
    events = dict(poller.poll(10000))

    if request in events:
        buffers = request.recv_multipart()

        for buf in buffers:
            if buf != b"END":
                reqb = to_request_protobuf(buf)
                print("*->", reqb.major, reqb.minor, reqb.errors, reqb.host)
                print("\tPublisher:", reqb.publish_url)
                print("\t Snapshot:", reqb.snapshot_url)
                print("\t  Control:", reqb.control_url)
    else:
        print("'LIST' call to the Directory Server timed out!")

    request.close()


if __name__ == "__main__":
    main()
