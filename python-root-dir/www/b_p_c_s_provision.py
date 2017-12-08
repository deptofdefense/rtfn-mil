#!/usr/bin/env python
'''
 * FILENAME: b_p_c_s_provision.py
 * PURPOSE: Allow the use of python virtual environment through a webserver call. 
            Provisions UNI to UNI connections through Level3/CenturyLink.
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
# this activates the python virtual environment
activate_env="/home/id22/.virtualenvs/ydk-py/bin/activate_this.py"
execfile(activate_env, dict(__file__=activate_env))
import sys
# this sets the python path for execution
sys.path.insert(0, "/home/id22/Desktop/ydk-py-master/core/samples")
import Calls2Level3 as L3_io
import secondAsrConfig as ASR_io
import json
import cgi,os

__name__ == "__main__"
GET={}
args=os.getenv("QUERY_STRING").split('&')
print ("Content-Type: text/html\r\nAccess-Control-Allow-Origin: *\r\n"+
"Access-Control-Allow-Credentials: true\r\nAccess-Control-Allow-Methods:*\r\n"+
"Access-Control-Allow-Headers:*\r\nAccess-Control-Expose-Headers\r\n")

for arg in args:
	t = arg.split('=')
	if len(t) > 1: 
		k, v = arg.split('=')
		GET[k] = v
		print(k + " :" + v)

# based on the UI this is missing the Credit Card / Payment info this is intentional
# for this stage of development.
request=L3_io.provisionConnection(GET['uni1'], GET['celan1'], GET['uni2'], GET['speed'])

if request: print '{PROVsuccess:true}'
else: print '{PROVsuccess:false}'
