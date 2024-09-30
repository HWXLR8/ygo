#!/usr/bin/env python3

import miniupnpc

port = 6969
upnp = miniupnpc.UPnP()
upnp.discoverdelay = 10
upnp.discover()
upnp.selectigd()

# addportmapping(external-port, protocol, internal-host, internal-port, description, remote-host)
p = upnp.addportmapping(port, 'TCP', upnp.lanaddr, port, 'ygo', '')
if p:
    print("done")
