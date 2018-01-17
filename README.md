# Real Time Forwarding Network - Military (RTFN-MIL)

What problem does this code solve?<br>
How does the United States Government (USG)/ Department of Defense (DoD) achieve reliable and guaranteed on demand (i.e. <=3 minutes) network connectivity between any two commercial endpoints worldwide. These endpoints are not only traditional carrier demarcation points, but will include non-traditional locations on college campuses, commercial datacenters, commercial carriers locations at conference centers, business parks, malls, offices, hotel rooms, etc., “Any to Any” on demand and reliable.

How did we got here?<br>
This effort began as a concept between Level3 Communications and the Defense Information Systems Agency (DISA) as a follow on to internal efforts to automate the DISA core. This concept morphed into a Cooperative Research and Development Agreement between Level3 (now CenturyLink) and DISA to promote this technology. Collaboratively this effort started by connecting a DISA facility in Maryland to various datacenter locations throughout the world, on demand. Level3 developed an Application Program Interface (API) and installed networking automation equipment that allowed a DISA orchestrator to communicate requirements and setup information. Likewise, DISA also automated the configuration of it's communication equipment at the Maryland facility to completely automate the setup of the connectivity.

What are the envisioned uses?<br>
RTFN is a dual use technology being developed that benefits national interests for civilian and defense needs. For humanitarian operations, this technology can serve the world by integrating the best network, compute, storage, and security capabilities that the world has to offer. This technology can serve as the way to integrate disparate systems/capabilities in a PRIVATE and MANAGED network to enable operations that require discretion due to the privacy and security requirements. Also, this technology could serve to post publicly releasable schedules such as seaport and airport relief deliveries while restricting access to securely edit and maintain that information on a multi-national basis. This reduced and/or removes the equipment needed to secure these types of networks from the entire Internet. Likewise, when you consider the military supporting various operations from forward locations, this capability will allow the the DOD to quickly establish virtual networks through commercial carriers. These private virtual networks may be more resilient than other network connection technologies in use today.

Installation Instructions we used for the private Map Server:
1. We  followed instructions to install a private open street map tile server to serve tiles to leaflet. https://switch2osm.org/serving-tiles/manually-building-a-tile-server-14-04/

Installation Instructions we used for the Apache Web Server (on Map Server):
1. Follow https://help.ubuntu.com/lts/serverguide/httpd.html or similar guide to install an httpd Apache2 server on your OS. We used Apache2 2.4.10-1 for an AMD processor on Ubuntu 14.04 Trusty Tahr.
2. We used the default /var/www location to store our files. The Repo files in the www location are those that we used.
3. We added a service config entry similar to https://ubuntuforums.org/showthread.php?t=2337048 to start the webserver on apache restart. sudo systemctl enable apache2.service then sudo systemctl start apache2.service

Dependency Instructions for Javascript and CSS delivered by Apache Web Server (on Map Server):
1. JS Frameworks (and CSS) used:
    * leaflet-src
    * jquery-ui-themes-1.12.1
    * font-awesome-4.7.0
    * bootstrap-3.3.7-dist
    * leaflet-control-window-master
    * jquery-3.2.1.js
    * jquery-ui-1.12.1

Installation Instructions we used for the Python:
1. We used pyenv to setup our development environment, you may or may not do that. See http://ydk.cisco.com/py/docs/getting_started.html for instructions.
    * our virtual environment home is "/home/id22/.virtualenv/ydk-py/"
    * we built the YDK package and inserted our code into that package.
    * we activate this environment for initiation through a cgi call via a
      python webserver that we run continuously.
    * see python-root-dir for python code. Our root for executing the python      scripts was "/home/id22/Desktop/ydk-py-master/core/samples".
    * python-root-dir/www is the destination directory for calls to the python
      webserver.
2. We operate in a development environment where connectivity to the internet does not exist locally. The following commands have been helpful.
    * pip install --no-index --file-links /. {archiveName}
    * sudo apt-get [TODO: add install from local repo ...]
    * [TODO: add determining packages required so you can do it once]
3. We used an Ubuntu 14.04 Trusty Tahr environment with python 2.X installed. There is not reason not to use python 3.x if the following packages will support that.
4. use pip install for the following packages. 
    *  certifi (2017.11.5)
    *  chardet (3.0.4)
    *  ecdsa (0.13)
    *  enum34 (1.1.3)
    *  idna (2.6)
    *  ipaddress (1.0.9)
    *  lxml (3.4.4)
    *  ncclient (0.5.3)
    *  paramiko (1.15.2)
    *  pip (9.0.1)
    *  protobuf (3.0.0b2.post2)
    *  pyang (1.6)
    *  pyasn1 (0.2.2)
    *  pycparser (2.17)
    *  pycrypto (2.6.1)
    *  requests (2.18.4)
    *  setuptools (28.8.0)
    *  six (1.10.0)
    *  Twisted (16.1.1)
    *  urllib3 (1.22)
    *  wheel (0.29.0)
    *  ydk (0.5.2)
    *  ydk-models-cisco-ios-xr (6.1.2)
    *  ydk-models-ietf (0.1.1)
    *  ydk-models-openconfig (0.1.1)
    *  zope.interface (4.3.3)
5. We have decided not to include the YDK or other source code from dependency libraries. In place we will list the files that we used in the directories here so that you can reproduce the environment if you choose to do so.
Files not included here but present in the /home/id22/Desktop/ydk-py-master/core/samples directory-compiled files excluded:
    * \_\_init\_\_.py
    * _config_builder.py
    * add new interfaces
    * bgp.py
    * bgp_codec.py
    * bgp_netconf.py
    * ietf_system.py
    * int.txt
    * oc-interfaces.py
    * session_mgr.py
    * timetest.py
    * (other folders as part of the ydk or ubuntu installation have been ommitted)

See Git Wiki for more information about the what, where, why that we don't cover here.