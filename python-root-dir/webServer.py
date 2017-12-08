#!/usr/bin/env python
'''
 * FILENAME: webServer.py
 * PURPOSE: Deploy a python based webserver. This runs forever.
 * AUTHORS: Mr. David J. Stern
 * DATE: DEC 2017
 * AGENCY: Defense Information Systems Agency
 * DEPARTMENT: Defense
 * GOVERNMENT: United States
 * THIS WORK IS IN THE PUBLIC DOMAIN. See relevant license information for its
   intended use. 
 * This work is solely a Government work product and no contractors participated
   in its creation.
'''
import BaseHTTPServer
import CGIHTTPServer
import cgitb; cgitb.enable()   #troubleshooting

webServer = BaseHTTPServer.HTTPServer
wsHandler = CGIHTTPServer.CGIHTTPRequestHandler
wsParameters = ("",8000)   #TODO: move to SSL
wsHandler.cgi_directories = ["/www"] #TODO: update this for traversal, security, etc.

httpd = webServer(wsParameters,wsHandler)
httpd.serve_forever()
