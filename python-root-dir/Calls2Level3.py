#!/usr/bin/env -u python
'''
 * FILENAME: Calls2Level3.py
 * PURPOSE: Manage api calls to Level3, this likely will change with scale.
 *          This really is the beginning of a multi-vendor solution.
 * AUTHORS: Mr. David J. Stern
 * DATE: DEC 2017
 * AGENCY: Defense Information Systems Agency
 * DEPARTMENT: Defense
 * GOVERNMENT: United States
 * THIS WORK IS IN THE PUBLIC DOMAIN. See relevant license information for its
   intended use. 
 * This work is solely a Government work product and no contractors participated
   in its creation.
 * TODOs
    - Turn global variables into an object.
'''
import hmac
import hashlib
import base64
import time
import httplib,urllib, urllib2
import ssl
import json
import secondAsrConfig as ASR_io
import requests
import time,sys,os
import warnings
# this was used before SSL/TLS packages were upgraded
#from requests.packages.urllib3.exceptions import SNIMissingWarning,InsecurePlatformWarning

#SET GLOBAL VARIABLES

#set details of User/Network Network Interface to carrier.
bandwidthAvailable={} #key is str of UNI Id, value is available in int
usgConnections={} #key is str of UNI id, value is carrier id
currentLastMileInterfacePort="GigabitEthernet0/0/0/19" # str: vendor port ident.
#TODO: get this from overhead tooling
currentUsgConnection = "{redacted}" # i.e "XX/XXXX/XXXXXX/XXXX"
currentLastMileDevice = "{redacted}" # friendly name i.e. "ROUTER(.50)"
currentLastMileIp ="{redacted}" # use an IP address , we used ipv4
currentCarrierAccountNumbers={}
#account number for our endpoint(s)
currentCarrierAccountNumbers['Level3'] = 0 #{redacted}
#account number for aws endpoint(s)
currentCarrierAccountNumbers['Level3-aws-endpoints'] = 0 #{redacted} 
currentCarrierBgpIp={}
currentCarrierBgpIp['Level3']="{redacted}"
currentVlans=[]

#set details of End Point Use like this one for a datacenter at the end of the UNI.
##Datacenter Account Numbers
currentDcAccountNumbers={}
currentDcAccountNumbers['AWS'] = 0 #{redacted}  #various DataCenter Account Numbers.
currentDcAccountNumbers['AWS_ID'] =  0 #{redacted}  #ID is an internal org DataCenter Account Numbers.
currentDcAccountNumbers['AWS_GOVCLOUD'] = 0 #{redacted}  #this is the GovCloud account.
##Anonymous System Numbers By Connection Provider
currentDcAsnByConnection={}
currentDcAsnByConnection['AWS']=0 #{redacted}  # this is the AWS DC ASN for some DC's
##Authentication Information (note: this is POC level not production grade yet)
currentDcBgpAuthenticationKey={}
currentDcBgpAuthenticationKey['AWS']='{redacted}'  # i.e. "TEST123"
currentDcDefaultSiteUni = "{redacted}" # i.e "XX/XXXX/XXXXXX/XXXX"
currentDcVirtualGatewayId = "{redacted}" # i.e. "vgw-XXXXXXXX"
currentDcSecurityToken = "{redacted}" # i.e. "arn:aws:iam::XXXXXXX:role/XXXXX"
# TODO: as this grows build a centralized datastore for vgw/region values.
# TODO: allow creation and use of new vgw's per region on demand.
currentDcRegionVgwByUni = {
    "redacted_uni":{"awsRegionId":"us-east-1","AwsVirtualGatewayId":"vgw-redacted"},
    "redacted_uni2":{"awsRegionId":"us-west-1","AwsVirtualGatewayId":"vgw-redacted"},
    "redacted_uni3":{"awsRegionId":"...","AwsVirtualGatewayId":"..."},
    "redacted_uni4":{"awsRegionId":"...","AwsVirtualGatewayId":"..."},
    "redacted_uni5":{"awsRegionId":"...","AwsVirtualGatewayId":"..."}
}; 

#set details for User/Network Network Interface overhead to carrier.
#TODO: may consider a different hash as this is more NNI than UNI.
currentDcAsnByConnection['Level3']=0 #{redacted} # ASN to use for carrier connect.
currentCarrierApplicationKey={}
currentCarrierApplicationKey['Level3']='{redacted}' # i.e. "APPKEYXXXXXXXXXXXXX"
currentCarrierApplicationSecret={}
currentCarrierApplicationSecret['Level3']='{redacted}'
currentCarrierURI={}
currentCarrierURI['Level3']='{redacted}' # i.e. "https://somewhere.com" use https
currentCarrierApiVersion={}
currentCarrierApiVersion['Level3']="{redacted}" # i.e. "1.2"
currentCarrierCustomerEmail={} # used in provisioning
currentCarrierCustomerEmail['Level3']="{redacted}" # i.e. email@someserver.mil

###end move me

# Method: getL3Digest
# Parameters: version (decimal)
# Description: Digest for API Communication with Level3
# Returns: Digest (str), currentEpochTime (int)

def getL3Digest(version):
    """
    Returns a Digest for API Communication with Level3
    
    Author:
    David J. Stern, Level3 Communications
    (based on External API User Guide Dynamic Connections v 1.2)
    (you will need to coordinate with Level3 to get a connection and API)
    
    Date:
    DEC 2017
    
    Parameters: 
    version: (Decimal): Version number to use [currently a placeholder/not used]
    
    Returns:
    a: (String): The digest
    epochTime: (String): epoch time 
    """
    appKeySecret = currentCarrierApplicationSecret['Level3']; # this is your secret key
    epochTime = str(int(time.time()))
    a = base64.b64encode(hmac.new(appKeySecret, msg=epochTime, digestmod=hashlib.sha256).digest())
    return (a,epochTime)
    
def queryUnisByAccount(accountId,version_string):
    """
    Returns dict object of unis in Level3 format
    
    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    accountId: (int): Level3 account number to query against
    version_string: (str): Version number to use, "" is default/latest
    
    Returns:
    objResponse['unis']: (dict): Level3 format for list of unis per accountId
    """
    if version_string=="" or version_string=="2.0": #@latest version per Level3 External API v1.2 10/31/2017
        digestPair=getL3Digest("1.0")
        headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
        req=urllib2.Request(currentCarrierURI['Level3']+"/Network/v2/DynamicConnection/unis?billingAccountNumber="+str(accountId),None,headers)
        r1 = urllib2.urlopen(req)
        objResponse = json.loads(r1.read())
        return objResponse['unis']
    elif version_string=="1.0": # first API version
        digestPair=getL3Digest("1.0")
        headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
        req=urllib2.Request(currentCarrierURI['Level3']+"/Network/v1/DynamicConnection/queryUnisByAccount?accountId="+str(accountId),None,headers)
        r1 = urllib2.urlopen(req)
        objResponse = json.loads(r1.read())
        return objResponse['unis']			

def queryUnisByAccountJSON(accountId,version_string):
    """
    Returns dict object of unis in Level3 format
    
    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    accountId: (int): Level3 account number to query against
    version_string: (str): Version number to use, "" is default/latest
    
    Returns:
    objResponse['unis']: (dict): Level3 format for list of unis per accountId
    """    
    if version_string=="" or version_string=="2.0": #@latest version per Level3 External API 10/31/2017
        digestPair=getL3Digest("1.0")
        headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
        req=urllib2.Request(currentCarrierURI['Level3']+"/Network/v2/DynamicConnection/unis?billingAccountNumber="+str(accountId),None,headers)
        try:
            r1 = urllib2.urlopen(req)
        except urllib2.URLError as e:
            if hasattr(e, 'reason'):
                print 'We failed to reach a server.'
                print 'Reason: ', e.reason
                return e.reason
            elif hasattr(e, 'code'):
                print 'The server couldn\'t fulfill the request.'
                print 'Error code: ', e.code
                return e.code
        return r1.read()
    elif version_string=="1.0": # first API version
		digestPair=getL3Digest("1.0")
		headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
		req=urllib2.Request(currentCarrierURI['Level3']+"/Network/v1/DynamicConnection/queryUnisByAccount?accountId="+str(accountId),None,headers)
		try:
			r1 = urllib2.urlopen(req)
		except urllib2.URLError as e:
			if hasattr(e, 'reason'):
				print 'We failed to reach a server.'
				print 'Reason: ', e.reason
				return e.reason
			elif hasattr(e, 'code'):
				print 'The server couldn\'t fulfill the request.'
				print 'Error code: ', e.code
				return e.code
		return r1.read()

def queryConnectionsByAccount(accountId,version_string):
    """
    Returns dict object of EVC connections in Level3 format
    
    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    accountId: (int): Level3 account number to query against
    version_string: (str): Version number to use, "" is default/latest
    
    Returns:
    objResponse['evcs']: (dict): Level3 format for list of EVC connections
    per accountId. This returns inactive and active accounts. In fact all 
    connections ever made.
    """   
    if version_string=="" or version_string=="2.0": #@latest version per Level3 External API 10/31/2017	
        digestPair=getL3Digest("1.0")
        headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
        req=urllib2.Request(currentCarrierURI['Level3']+"/Network/v2/DynamicConnection/evcs?billingAccountNumber="+str(accountId)+"&source=dynamic",None,headers)
        r1 = urllib2.urlopen(req)
        objResponse = json.loads(r1.read())
        #print objResponse['evcs']
        return objResponse['evcs']
    elif version_string=="1.0": # first API version
        digestPair=getL3Digest("1.0")
        body1 = "{\"accountId\":\""+str(accountId)+"\"}"
        headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
        response = requests.request("POST", currentCarrierURI['Level3']+"/Network/v1/DynamicConnection/queryConnectionsByAccount", data=body1, headers=headers)
        objResponse = json.loads(response.text)
        return objResponse['connections']

def queryConnectionsByAccountJSON(accountId,version_string):
    """
    Returns JSON formatted dict object of EVC connections in Level3 format
    
    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    accountId: (int): Level3 account number to query against
    version_string: (str): Version number to use, "" is default/latest
    
    Returns:
    objResponse['evcs']: (dict): Level3 format for list of EVC connections
    per accountId. This returns inactive and active accounts. In fact all 
    connections ever made.
    """   
    if version_string=="" or version_string=="2.0": #@latest version per Level3 External API 10/31/2017	
        digestPair=getL3Digest("1.0")
        headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
        req=urllib2.Request(currentCarrierURI['Level3']+"/Network/v2/DynamicConnection/evcs?billingAccountNumber="+str(accountId)+"&source=dynamic",None,headers)
        r1 = urllib2.urlopen(req)
        objResponse = json.loads(r1.read())
        return json.dumps(objResponse['evcs'])
    elif version_string=="1.0": # first API version
        digestPair=getL3Digest("1.0")
        body1 = "{\"accountId\":\""+str(accountId)+"\"}"
        headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
        response = requests.request("POST", currentCarrierURI['Level3']+"/Network/v1/DynamicConnection/queryConnectionsByAccount", data=body1, headers=headers)
        return response.text

def createLevel3Connection(payload, version_string):
    """
    Creates Level3 Connection using payload that is passed in
    
    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    payload: (str): payload to be used as data element in AJAX request obj
    version_string: (str): Version number to use, "" is default/latest
    
    Returns:
    success: (boolean): returns True if successful. 
    objResponse['evcServiceId']: (String): Return the vendor connection id.
    """
    digestPair=getL3Digest("1.0")
    if version_string=="" or version_string=="2.0": #@latest version per Level3 External API 10/31/2017	
        body1 = payload
        headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
        print (" sending to: "+currentCarrierURI['Level3']+"/Network/v2/DynamicConnection/evcs", body1)
        response = requests.request("POST", currentCarrierURI['Level3']+"/Network/v2/DynamicConnection/evcs", data=body1, headers=headers,verify=False)	
        objResponse = json.loads(response.text)
        print (objResponse)	
        return (True,objResponse['evcServiceId'])
    elif version_string=="1.0": #first API version
        body1 = payload
        headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
        print (" sending to: "+currentCarrierURI['Level3']+"/Network/v1/DynamicConnection/createConnectionpayload", body1)
        response = requests.request("POST", currentCarrierURI['Level3']+"/Network/v1/DynamicConnection/createConnection", data=body1, headers=headers)	
        objResponse = json.loads(response.text)
        print (objResponse)	
        return (True,objResponse['serviceId'])		

def queryRequestsById(accountId,connectionServiceId,version_string):
    """
    Queries completion status of Connections Requested by account id
    
    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    accountId: (str): Level3 account number to query against
    connectionServiceId: (str): Vendor connection id to query
    version_string: (str): Version number to use, "" is default/latest
    
    Returns:
    success: (boolean): returns True if successful. 
    objResponse['requests']: (Object): Returns level3 object that includes status
    """    
    if version_string=="" or version_string=="2.0": #@latest version per Level3 External API 10/31/2017		
        digestPair=getL3Digest("1.0")
        headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
        req=urllib2.Request(currentCarrierURI['Level3']+"/Network/v2/DynamicConnection/requests?billingAccountNumber="+str(accountId)+"&evcServiceId="+str(connectionServiceId),None,headers)
        r1 = urllib2.urlopen(req)
        objResponse = json.loads(r1.read())
        return (True, objResponse['requests'])
    elif version_string=="1.0": # first API version
        digestPair=getL3Digest("1.0")
        body1 = "{\"serviceId\":\""+str(connectionServiceId)+"\"}"
        headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
        try:
            response = requests.request("POST", currentCarrierURI['Level3']+"/Network/v1/DynamicConnection/queryRequestsById", data=body1, headers=headers)
        except:
            return (False,{})
        objResponse = json.loads(response.text)
        return 

def getConnectionDetailsById(connectionServiceId):
    """
    Get Details of a connection
    
    TODO: need to add v2 call, this was missed in last api upgrade
    
    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    connectionServiceId: (str): Vendor connection id to query
    
    Returns:
    success: (boolean): returns True if successful. 
    objResponse['connections']: (Object): Returns hash of level3 connection obj
    """    
    digestPair=getL3Digest("1.0")
    body1 = "{\"serviceId\":\""+str(connectionServiceId)+"\"}"
    headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
    try:
        response = requests.request("POST", currentCarrierURI['Level3']+"/Network/v1/DynamicConnection/queryConnectionsById", data=body1, headers=headers)
    except:
        return (False)
    objResponse = json.loads(response.text)
    print objResponse	
    return (True,objResponse["connections"])
    
def deleteConnection(connectionServiceId,version_string):
    """
    Deletes a connection
    
    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    connectionServiceId: (str): Vendor connection id to delete
    version_string: (str): Version number to use, "" is default/latest    
    
    Returns:
    success: (boolean): returns True if successful 
    objResponse: v2 (Obj): Obj contains dict with success key. True means delete
                           completed successfully
    objResponse: v1 (Boolean): Success is True    
    """
    try:
        if (version_string=="" or version_string=="2.0"): #@latest version per Level3 External API 10/31/2017		
            digestPair=getL3Digest("1.0")
            headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
            body="{}"
            strConn = currentCarrierURI['Level3'].replace("https://","")
            conn = httplib.HTTPSConnection(strConn)
            conn.request("DELETE","/Network/v2/DynamicConnection/evcs/"+connectionServiceId,body,headers)
            res=conn.getresponse()
            objResponse = json.loads(res.read())
            status=False
            if (res.status==202):
				status=True
            conn.close()
            return (status, objResponse)
        elif version_string=="1.0": # first API version	
            digestPair=getL3Digest("1.0")
            body1 = "{\"serviceId\":\""+str(connectionServiceId)+"\"}"
            headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}		
            response = requests.request("POST", currentCarrierURI['Level3']+"/Network/v1/DynamicConnection/deleteConnection", data=body1, headers=headers)
            objResponse = json.loads(response.text)
            print (objResponse)
            return (True)
    except Exception as e:
        print ("error with the Delete Connection",e)
        return False
    return False

def generateDisaToAwsConnectionPayload(bandwidth,localUni,localVlan,awsUni,awsRegionId,AwsWanIpAndCidr,DisaWanIpAndCidr,AwsVirtualGatewayId,AwsArnSecurityToken,version_string):
    """
    Generates the AWS Connection Payload based on Level3's requirements.
    
    TODO:
    consider implementing the requestId feature of API
    
    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    bandwidth: (int): bandwidth requested in bits per second
    localUni: (str): UNI of the service provider connection being used
    localVlan: (int): Vlan being used on the local interface associated with UNI
    awsUni: (str): UNI of the service provider to AWS
    awsRegionId: (str): AWS region id i.e. "us-east-1"
    AwsWanIpAndCidr: (str): AWS Interface WAN IP address and CIDR
                            i.e. "10.X.X.2/31"
    DisaWanIpAndCidr: (str): DISA Interface WAN IP address and CIDR
                             i.e. "10.X.X.3/31"
    AwsVirtualGatewayId: (str): AWS Virtual Gateway id i.e. "vgw-123456789"
    AwsArnSecurityToken: (str): AWS ARN security token i.e. "arn:aws:iam:1a..55"
    version_string: (str): Version number to use, "" is default/latest    
    
    Returns:
    payload: (str): returns the str payload for the data portion of an AJAX
                    request.
    """
    if (version_string=="2.0" or version_string==""):
        payload = "{\"userEmail\":\""+str(currentCarrierCustomerEmail['Level3'])+"\",\"billingAccountNumber\":\""+str(currentCarrierAccountNumbers['Level3'])+"\",\"bandwidth\":\""+bandwidth+"\",\"cos\":\"Basic\", "\
        +"\"endPoint1\":{\"uniServiceId\":\""+localUni+"\",\"ceVlan\":\""+localVlan+"\"}," \
        +"\"endPoint2\":{\"awsConnectionProfile\":{\"awsRegionId\":\""+awsRegionId+"\",\"customerAwsAccount\":\""+str(currentDcAccountNumbers['AWS'])+"\",\"customerAsn\":\""+str(currentDcAsnByConnection['Level3'])+"\",\"autoGenerateBgpPeerAddress\":\"false\",\"customerBgpPeerAddress\":\""+DisaWanIpAndCidr+"\",\"awsBgpPeerAddress\":\""+AwsWanIpAndCidr+"\",\"autoGenerateBgpAuthenticationKey\":\"false\",\"bgpAuthenticationKey\":\""+str(currentDcBgpAuthenticationKey['AWS'])+"\",\"autoAcceptConnection\":\"true\",\"virtualGatewayId\":\""+AwsVirtualGatewayId+"\",\"arnSecurityToken\":\""+AwsArnSecurityToken+"\"}}}"
        return payload
    elif version_string=="1.0":
        payload = "{\"userEmail\":\""+str(currentCarrierCustomerEmail['Level3'])+"\",\"billingAccountNumber\":\""+str(currentCarrierAccountNumbers['Level3'])+"\",\"bandwidth\":\""+bandwidth+"\",\"cos\":\"Basic\", "\
        +"\"endPoint1\":{\"uniId\":\""+localUni+"\",\"ceVlan\":\""+localVlan+"\"}," \
        +"\"endPoint2\":{\"awsConnectionProfile\":{\"awsRegionId\":\""+awsRegionId+"\",\"customerAwsAccount\":\""+str(currentDcAccountNumbers['AWS'])+"\",\"customerAsn\":\""+str(currentDcAsnByConnection['Level3'])+"\",\"autoGeneratePeerIPs\":\"false\",\"customerPeerIPs\":\""+DisaWanIpAndCidr+"\",\"awsPeerIPs\":\""+AwsWanIpAndCidr+"\",\"autoGenerateBgpAuthenticationKey\":\"false\",\"bgpAuthenticationKey\":\""+str(currentDcBgpAuthenticationKey['AWS'])+"\",\"autoAcceptConnection\":\"true\",\"virtualGatewayId\":\""+AwsVirtualGatewayId+"\",\"arnSecurityToken\":\""+AwsArnSecurityToken+"\"}}}"
        return payload	

def getL3ActiveConnections():
    """
    Prints active connections to stdout.

    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    (None)  
    
    Returns:
    (boolean): True always returns true
    """
    dictConnections=queryConnectionsByAccount(currentCarrierAccountNumbers['Level3'],"")
    print ("\nDISA Current Connections through Level3: "+currentUsgConnection)
    print ("*"*60)
    flag=False
    for connection in dictConnections:
        success=_printLevel3ConnectionsByAccount(connection,True) #True indicates active connections
        if success: flag=True
    if not flag: print ("No Active Connections\n") 
    return True
    

def getServiceIdsForActiveL3Connections():
    """
    Provides list of active connection ids from Level3

    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    (None)  
    
    Returns:
    (list) : list of (str) connection ids that are active
    """    
    listServiceIds=[]
    dictConnections=queryConnectionsByAccount(currentCarrierAccountNumbers['Level3'],"")
    for connection in dictConnections:
        value=_getLevel3ServiceIdFromConnection(connection,True)
        if str(value)!="": listServiceIds.append(value)
    return listServiceIds


def _printLevel3UnisByAccount(uni):
    """
    Helper Function: prints key value of iterable object passed. Not recursive.

    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    uni (obj): iterable object with key value pairs
    
    Returns:
    (None)
    """        
    for k,v in uni.iteritems():
        print(k+": "+str(v))

def _printLevel3ConnectionsByAccount(uni,active):
    """
    Helper Function: Prints Connections by account. Based on active, prints
    disconnected and errored requests if false.

    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    uni: (object): response object from Level3 AJAX request to get Level3
                   connections by account.
    active: (boolean): True if you only want active conections. False format    
                       active, disconnected, and errored.
    
    Returns:
    (boolean): True if there are entries printed. False if none printed.
    """        
    if currentCarrierApiVersion['Level3']=="2.0" or currentCarrierApiVersion['Level3']=="":
        if active and (str(uni['connectionStatus'])=="disconnected" or str(uni['connectionStatus'])=="error_creating"): return False
        for k,v in uni.iteritems():
            print(k+": "+str(v))
        print("\n")
        return True
    else:
        if active and str(uni['status'])=="disconnected": return False
        for k,v in uni.iteritems():
            print(k+": "+str(v))
        print("\n")
        return True	
        
def _getLevel3ServiceIdFromConnection(connection,active):
    """
    Helper Function: Prints Connections by account. Based on active, prints
    disconnected and errored requests if false.

    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    connection: (object): response object from Level3 AJAX request to get Level3
                   connections.
    active: (boolean): True if you only want active conections. False format    
                       active, disconnected, and errored.
    
    Returns:
    evcServiceId: (str): Service id contained in connection object. Returns ""
                         if there are no entries based on conditions.
    """ 
    if currentCarrierApiVersion['Level3']=="2.0" or currentCarrierApiVersion['Level3']=="":
        if active and (str(connection['connectionStatus'])=="disconnected" or str(connection['connectionStatus'])=="error_creating"): return ""
    else:
        if active and str(connection['status'])=="disconnected": return ""	
    return str(connection['evcServiceId'])

def _minBandwidthAvailable(a,b):
    """
    Helper Function: Prints lowest of two bandwidth amounts

    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    a: (int): number
    b: (int): number
    
    Returns:
    (int) lowest of two numbers compared.
    """ 
    return sorted([a,b])[0]	

def _maxBandwidthAvailable(a,b):
    """
    Helper Function: Prints highest of two bandwidth amounts

    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    a: (int): number
    b: (int): number
    
    Returns:
    (int) highest of two numbers compared. The number if they are equal.
    """ 
    return sorted([a,b], reverse = True)[0]	

def _intToStrBandwidth(bandwidth):
    """
    Helper Function: Provide print friendly bps to Mbps string

    TODO: expand this with Kb, Mb, Gb, and Tb (logic exists in javascript)

    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    bandwidth: (int): number

    Returns:
    (str) bps (int) converted to Mbps combined with " Mbps"
    """    
    try:
        if int(bandwidth)>0:
            return str(int(bandwidth)/1000000)+" Mbps"
        else:
            return "0 Mbps"
    except:
        return "0 Mbps"

class Tee(object):
    """
    Provides a custom STD out tee to log STDOUT and send it to CGI (for demos)

    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    Object: (object) Object to instantiate

    Returns:
    (None)
    """    
    def __init__(self,*files):
        self.files=files 
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

def provisionConnection(uni1,uni1CeLan,uni2,speed):
    """
    Main Provisioning script for this capability. Provides UNI to UNI connection
    through Level3. Since we are using AWS on distant end there is no distant 
    VLAN.
    
    TODO:
    Add ability to modify features of a current local interface
    Add ability to read status of current local interface
    Deconflict carrier VLAN availability and local availability
    Add reset of local interface to what the carrier has provisioned. Baseline
        from what carrier shows.
    Consider creds as persistent obj or obtaining them is a more scalable manner.
    Make overhead VLAN scale as it won't always be 989. Includes some input checks.
    Build a vendor agnostic version of this when second carrier is onboarding.
    Expand UNI receipt from carrier to handle multiple endpoints, current 1 for 
        OHcontrol.
    Move getting level3 vlans to helper function. API v1.2 has this in AJAX 
        response now.
    For CLI actions, instead of exit after one action reintiate loop and get new
        calls to device and Level3 to represent changes.
    Update ASN neighbors calls to handle multiple ASNs both from our device and
        the distant end.
    Expand ASN neighbors to span multiple physical connections.
    Expand VLANS used to ~4096 from ~1024 based on local equipment and vendor
        capabilities. Feasible now with v2 Level3 API's.
    Add int type enforcement to entry for bandwidth amount requested.
    Add additional Vlan limitations into entry CLI.
    Refactor the AWS region associations. Gov Cloud and Normal Cloud have
        separate creds, permissions, etc.
    Add provisioning actions for Internal WAN, VRFs, and other interconnects
    ASN conflict should be handled instead of just exiting.
    Add numbering system for auditing of connections. Add Id at final message.
    Delete process initially but build in UI for delete and checks of 
        status.
    Work local demarcation location out or break site into another variable.
        Using Maryland for now.

    Author:
    David J. Stern
    
    Date:
    DEC 2017
    
    Parameters: 
    uni1: (str): Carrier User Network Interface id for local connection
    uni1CeLan: (str): Virtual LAN to use on uni1 side i.e. 200
    uni2: (str): Carrier User Network Interface id for distant end
    speed: (int): bandwidth in bits per second (bi-directional).

    Returns:
    (boolean) if called by CGI then boolean of True for end ping success. False
    for end ping failure.
    """
    
    """Code to handle demos with the CGI interface"""	
    cgiProv=False
    if (uni1 !="" and uni1CeLan !="" and uni2 != "" and speed !=""):
        cgiProv=True
        f = open ('output.txt', 'w')
        original = sys.stdout
        sys.stdout = Tee(sys.stdout, f)

    """Determine local demarcation carrier connection VLAN ports used"""
    currentVlans = ASR_io.getVlansInUse("asr",currentLastMileInterfacePort)
    print ("Maryland Demarc: "+currentLastMileDevice+": "+currentLastMileInterfacePort+" ")
    print ("*"*60)
    ASR_io.printVlans(currentVlans)
    print ("")
    print ("Carrier OH Control Vlan: "+"989")
    
    """Determine Level 3 ports used"""
    vlansLevel3=[]
    dictUnis=queryUnisByAccount(currentCarrierAccountNumbers['Level3'],"")
    if currentCarrierApiVersion['Level3']=="2.0" or currentCarrierApiVersion['Level3']=="":
        for uni in dictUnis:
            for vlan in uni['ceVlansInUse']:
                vlansLevel3.append(vlan)
    else:
        for uni in dictUnis:
            for vlan in uni['ceVlansUsed']:
                vlansLevel3.append(vlan)
                
    """Begin to print the local connection information (Maryland)"""     
    for uni in dictUnis:
        print ("\nMaryland Carrier: Level3: "+uni['uniServiceId'])
        print ("*"*60)
        #add bandwidth into global list for later use. #TODO: Add other date needed globally
        bandwidthAvailable[str(uni['uniServiceId'])]=str(uni['bandwidthAvailable'])
        usgConnections[str(uni['uniServiceId'])]=str(uni['locationId'])
        _printLevel3UnisByAccount(uni)
    
    """Level 3 connections from Maryland"""
    getL3ActiveConnections()
    
    """Build technical and development CLI. CGI uses next statement and hooks to
    eliminate further input."""
    
    strEnterOptions="\n" + \
    "Enter 1 to Add AWS Connection, 2 to Delete Vlan, 3 print AWS Wan Planning Details,\n"+ \
    "4 Delete Connection to AWS, 5 show AS neighbors, 6 delete AS neighbor,\n"+ \
    "7 ping AS neighbor by Vlan, 8 get Level3 Digest Creds\n"
    if (cgiProv): # if cgi interface option 1 to provision
        raw=str(1)
    else: 
        raw = raw_input(strEnterOptions) # otherwise get a CLI entry    

    ############################################################################
    """Provisions a Connection to AWS through Level3"""
    if (raw==str(1)): 
        print ("Add AWS Connection\n"+"*"*60+"\n")
        print ("Querying endpoints\n")
        # Obtain and Print to console AWS Endpoints
        dictUnis=queryUnisByAccount(currentCarrierAccountNumbers['Level3-aws-endpoints'],"")
        for uni in dictUnis:
            print ("\nLevel 3 AWS Data Center: "+uni['uniServiceId'])
            #add bandwidth into global list for later use.
            bandwidthAvailable[uni['uniServiceId']]=uni['bandwidthAvailable']
            _printLevel3UnisByAccount(uni)
        
        # get AWS destination connection details
        destinationNid=""
        bandwidthDesired=0
        demarcVlanDesired=0
        print ("\n"+"*"*60+"\nThis API connection to Level3 through "+usgConnections[currentUsgConnection]+": "+currentUsgConnection)
        raw=""
        first=""
        
        #another hook for cgi
        if (cgiProv): raw=uni2
        
        while True:
            if raw not in bandwidthAvailable.keys(): 
                raw = raw_input(first+"Enter AWS destination [Default is "+currentDcDefaultSiteUni+" :")
                if raw=="": 
                    destinationNid=currentDcDefaultSiteUni
                    break
                first="Invalid, " 
                continue
            else:
                destinationNid=raw
                break
        print ("AWS destination: "+destinationNid)
        
        #get bandwidth requirement
        print ("\n"+"*"*60+"\n"+" "*38+"From: "+usgConnections[currentUsgConnection]+"   To: "+destinationNid)
        print ("Max Available Bandwidth by Location   From: "+_intToStrBandwidth(bandwidthAvailable[currentUsgConnection])+"   To: "+_intToStrBandwidth(bandwidthAvailable[destinationNid]))
        
        while True:
            if (cgiProv): 
                bandwidthDesired = speed
                break
            if ((int(bandwidthDesired) >= 4000) and (int(bandwidthDesired) <= int(bandwidthAvailable[currentUsgConnection])) and (int(bandwidthDesired) <= int(bandwidthAvailable[destinationNid]))):
                break
            else:
                bandwidthDesired = raw_input(first+"Enter Bandwidth Requested [Min is 4000, Max is "+str(_minBandwidthAvailable(bandwidthAvailable[currentUsgConnection],bandwidthAvailable[destinationNid]))+", default is 10000000bps] :")
                if bandwidthDesired=="":
                    bandwidthDesired=10000000 #10Mbps
                    break
                continue
        print ("Bandwidth Requested: "+str(bandwidthDesired)+" \n")	
        
        # get vlan requirement
        print ("\n"+"*"*60+"\n"+"Select Sub-Interface connection to carrier device "+usgConnections[currentUsgConnection]+" via "+currentLastMileDevice+" port "+currentLastMileInterfacePort)
        print ("Current Vlans Already Allocated: "+	str(currentVlans[0]))
        autoVlan=200
        while True:
            if (cgiProv):
                demarcVlanDesired = uni1CeLan
                break
            # Calculates dynamic last mile vlan start with 200
            while autoVlan in currentVlans[0]: 
                autoVlan+=1;
            if (int(demarcVlanDesired)>0 and int(demarcVlanDesired)<1024 and int(demarcVlanDesired) not in currentVlans[0]):
                break
            else:
                demarcVlanDesired = raw_input(first+"Enter Vlan Requested [Min is 1, Max is 1023, default is "+str(autoVlan)+"] :")
                if str(demarcVlanDesired)=="":
                    demarcVlanDesired=autoVlan
                    break
                continue
        print ("Sub-Interface (Vlan) Selected is: "+str(demarcVlanDesired))
        
        # provision the local router interface vlan for new connection
        print ("\n"+"*"*60+"\nProvisioning "+currentLastMileDevice+" subinterface "+currentLastMileInterfacePort+"."+str(demarcVlanDesired))
        (success,callResponse,dictWanIpPackage)=ASR_io.addVlanToExisitingInterface(currentLastMileDevice,currentLastMileInterfacePort,demarcVlanDesired)
        if success: print ("\n Local Sub Interface (Vlan): "+str(demarcVlanDesired)+" Created Sucessfully\n")
        
        #provisioning the AWS Connection

        cidr=""
        if dictWanIpPackage['ipNetmask']=="255.255.255.254": cidr="/31"
        elif dictWanIpPackage['ipNetmask']=="255.255.255.252": cidr="/30"
        elif dictWanIpPackage['ipNetmask']=="255.255.255.0": cidr="/24"
        else: cidr="/31"
        AwsWanIpAndCidr=str(dictWanIpPackage['ipAWSDemarc'])+str(cidr)
        DisaWanIpAndCidr=str(dictWanIpPackage['ipDisaDemarc'])+str(cidr)

        #work through the AWS region association
        awsRegionId=""
        
        #customize for your aws needs, this needs to be refactored as most of
        #this is static association between UNI, VGW, and region.
        AwsVirtualGatewayId=currentDcVirtualGatewayId
        AwsAmSecurityToken=currentDcSecurityToken

        #Obtain correct region id and vgw to use. Different for different accts.
        if (str(destinationNid) in currentDcRegionVgwByUni.keys()): 
            awsRegionId = currentDcRegionVgwByUni[destinationNid]['awsRegionId']
            try:
                AwsVirtualGatewayId = currentDcRegionVgwByUni[destinationNid]['AwsVirtualGatewayId']
            except:
                # use default if not listed
                pass
        else:
            awsRegionId = "us-east-1"
            
        ##execute payload: begin connection        
        print ("\n"+"*"*60+"\nProvisioning Connection to AWS: "+str(destinationNid)+ " Aws Region: "+str(awsRegionId))
        if (currentCarrierApiVersion['Level3']=="2.0" or currentCarrierApiVersion['Level3']==""): 
            connectionPayload = generateDisaToAwsConnectionPayload(str(bandwidthDesired),str(currentUsgConnection),str(demarcVlanDesired),str(destinationNid),str(awsRegionId),str(AwsWanIpAndCidr),str(DisaWanIpAndCidr),str(AwsVirtualGatewayId),str(AwsAmSecurityToken),"")
        else:
            connectionPayload = generateDisaToAwsConnectionPayload(str(bandwidthDesired),str(currentUsgConnection),str(demarcVlanDesired),str(destinationNid),str(awsRegionId),str(AwsWanIpAndCidr),str(DisaWanIpAndCidr),str(AwsVirtualGatewayId),str(AwsAmSecurityToken),"1.0")
        print (connectionPayload)

        #send request
        (success,connectionServiceId)=createLevel3Connection(connectionPayload,currentCarrierApiVersion['Level3'])
        if success: print ("\nCarrier Processing ... Service Id: "+str(connectionServiceId)+" Assigned For Connection to AWS: "+str(destinationNid))
        
        #get the status of the request
        status="wip"
        success=True
        while (bool(success) and str(status)!="complete" and str(status)!="error"):
            (success,objStatus)=queryRequestsById(currentCarrierAccountNumbers['Level3'],connectionServiceId,"")
            status=objStatus[0]['status']
            if str(status)=="error": 
                success=False
                break
            if str(status)=="complete":
                break
            print ("Still Work in Progress ... Waiting 30s")
            time.sleep(30)
        if success: print ("\nCarrier Processing Completed Successfully... Service Id: "+str(connectionServiceId)+" Assigned For Connection to AWS: "+str(destinationNid))
        print (objStatus)
        
        #provision endpoint services
        ##provision BGP wan interface to AWS
        print ("\n"+"*"*60+"\nProvisioning BGP Configurations to AWS: "+str(destinationNid)+ " Aws Region: "+str(awsRegionId))		
        if ASR_io.manConfigBgpNeighbor(str(currentLastMileIp),str(dictWanIpPackage['ipAWSDemarc']),currentDcAsnByConnection['AWS'],currentDcBgpAuthenticationKey['AWS']):
            print ("\n BGP neighbor "+str(dictWanIpPackage['ipAWSDemarc'])+" @ AWS Configured! \n")
        else: # AS neighbor conflict
            exit()
        ##check that connection is established
        print ("\n"+"*"*60+"\nChecking if BGP Connection is Established: "+str(destinationNid)+ " Aws Region: "+str(awsRegionId))		
        timer=0
        while (str(ASR_io.getAsNeighborStatus("asrCiscoModel",str(dictWanIpPackage['ipAWSDemarc']))) != "BgpConnStateEnum.bgp_st_estab" and timer <240):
            print ("Not Connected .. checking again in 10s")
            time.sleep(10)
            timer+=10
        if (timer<400): print ("\n"+"*"*60+"\nBGP Connection is Established: "+str(dictWanIpPackage['ipAWSDemarc'])+ " Aws Region: "+str(awsRegionId))		
        else: print ("\n"+"*"*60+"\nBGP Connection Timed out")
        #Perform ping test
        print ("\n"+"*"*60+"\nPerforming Ping Test: "+str(dictWanIpPackage['ipAWSDemarc'])+ " Aws Region: "+str(awsRegionId))		
        responsePing=ASR_io.pingIpv4Destination(str(dictWanIpPackage['ipAWSDemarc']),currentLastMileIp,currentLastMileInterfacePort+"."+str(demarcVlanDesired))
        if responsePing:
            print ("Successfully pinged AS Neighbor on Vlan "+str(demarcVlanDesired)+": "+str(dictWanIpPackage['ipAWSDemarc'])+ " Aws Region: "+str(awsRegionId)+"\n")
            print ("\nAWS connection provisioned - RTFN-MIL CJON Number Completed Successfully")
        
            if (cgiProv==True): 
                sys.stdout = original
                f.close()
            return True
        else:
            print ("Failed to ping AS Neighbor on Vlan "+str(demarcVlanDesired)+": "+str(dictWanIpPackage['ipAWSDemarc'])+ " Aws Region: "+str(awsRegionId)+"\n")
            
            if (cgiProv==True): 
                sys.stdout = original
                f.close()
            return False
        exit()



    ############################################################################
    """Removes selected VLAN from local router interface to Level3 """
    if raw==str(2): 
        print ("Delete VLAN\n"+"*"*60+"\n")
        print ("Current Vlans Already Allocated: "+	str(currentVlans[0]))
        print ("Vlans attached to carrier device "+usgConnections[currentUsgConnection]+" via "+currentLastMileDevice+" port "+currentLastMileInterfacePort)
        demarcVlanDesired=0
        first=""	
        while True:
            if (int(demarcVlanDesired)>0 and int(demarcVlanDesired)<1024 and str(demarcVlanDesired) in str(currentVlans[0]) and int(demarcVlanDesired) !=989):
                break
            else:
                demarcVlanDesired = raw_input(first+"Enter Vlan To delete: [Must be listed above and cannot delete OH of 989] :")
                continue				
        success=ASR_io.deleteVlanFromExisitingInterface(currentLastMileDevice,currentLastMileInterfacePort,demarcVlanDesired)
        if success: 		
            print ("Vlan "+str(demarcVlanDesired)+" was removed from link to carrier device "+usgConnections[currentUsgConnection]+" via "+currentLastMileDevice+" port "+currentLastMileInterfacePort)
        exit()

    ############################################################################
    """Print AWS WAN /31 planning details which is based on VLAN used"""
    if raw==str(3): 
        demarcVlanDesired="0"
        first=""
        print ("\n"+"*"*60+"\n"+"AWS planning details for AWS sub-interface")
        while True:
            if (int(demarcVlanDesired)>0 and int(demarcVlanDesired)<1024):
                break
            else:
                demarcVlanDesired = raw_input(first+"Enter Vlan Requested [Min is 1, Max is 1023] :")
                continue		
        print ASR_io.getInternetAddressPairForWan(demarcVlanDesired)
        exit()

    ############################################################################
    """Delete the connection to AWS identified. Removes AWS Private Interface and Level 3
    Connection. Does not remove VLAN or ASN entries currently. """
    if raw==str(4):  
        connectionToDelete=""
        first=""
        print ("\n"+"*"*60+"\n"+"Delete Connection from: "+currentUsgConnection)
        # get current connections
        currentActiveConnections=getServiceIdsForActiveL3Connections()
        print ("You can delete these connections: "+str(currentActiveConnections)+"\n")
        print ("This does not remove local vlan..use option 2")
        while True:
            if (str(connectionToDelete)!="" and str(connectionToDelete) in currentActiveConnections):
                break				
            else:
                connectionToDelete = raw_input(first+"Enter ConnectionId to delete:")
                continue		
        success=deleteConnection(connectionToDelete,"")
        if success: print ("\nCarrier Accepted Delete Request ... Currently Processing")
        if not bool(success): print "(\nDelete of Service Id: "+str(connectionToDelete)+" Failed!)"
        exit()

    ############################################################################
    """Pull the current list of AS neighbors"""
    if raw==str(5):  
        connectionToAdd=""
        first=""
        # get current as neighbors
        currentAsNeighbors=ASR_io.getAsNeighbors("asr",currentDcAsnByConnection['Level3'],currentCarrierBgpIp['Level3'])
        print ("Current AS Neighbors Connected: "+str(currentAsNeighbors))
        while True:
            if (str(connectionToAdd)!="" and str(connectionToAdd) not in currentAsNeighbors):
                break				
            else:
                connectionToAdd = raw_input(first+"Enter Local AS to add:")
                first = "Invalid input, "
                continue				
        if ASR_io.addAsNeighbor("asr",str(connectionToAdd),str(currentDcBgpAuthenticationKey['AWS']),currentDcAsnByConnection['AWS']):
            print ("Successfully added AS Neighbor: "+str(connectionToAdd)+"\n")
        exit()

    ############################################################################
    """To delete a local AS entry on an interface"""
    if raw==str(6):  
        connectionToDelete=""
        first=""
        currentAsNeighbors=ASR_io.getAsNeighbors("asrCiscoModel",currentDcAsnByConnection['Level3'],currentCarrierBgpIp['Level3'])
        print ("\n"+"*"*60+"\n"+"Current AS Neighbors Connected: "+str(currentAsNeighbors))
        while True:
            if (str(connectionToDelete)!="" and str(connectionToDelete) in currentAsNeighbors):
                break				
            else:
                connectionToDelete = raw_input(first+"Enter Local AS to delete:")
                first = "Invalid input, "
                continue		
        if ASR_io.deleteAsNeighbor("asr",str(connectionToDelete)):
            print ("Successfully removed AS Neighbor: "+str(connectionToDelete)+"\n")
        exit()
    ############################################################################
    """Pings the distant end from local router interface based on the local VLAN
    used. You don't have to know anything but the local VLAN ;)"""
    if raw==str(7):  
        vlanSelected=""
        connectionToTest=""
        first=""
        print ("\n"+"*"*60+"\n"+currentLastMileDevice+"Ping Test to AS Neighbors Connected: "+str(currentVlans[0]))
        while True:
            if (str(vlanSelected)!="" and int(vlanSelected) in currentVlans[0]):
                break				
            else:
                vlanSelected = raw_input(first+"Enter Vlan for AS Destination to ping:")
                first = "Invalid input, "
                connectionToTest=ASR_io.getInternetAddressPairForWan(int(vlanSelected))['ipAWSDemarc']		
                continue		
        responsePing=ASR_io.pingIpv4Destination(str(connectionToTest),currentLastMileIp,currentLastMileInterfacePort+"."+str(vlanSelected))
        if responsePing:
            print ("Successfully pinged AS Neighbor on Vlan "+str(vlanSelected)+": "+str(connectionToTest)+"\n")
        else:
            print ("Failed to ping AS Neighbor on Vlan "+str(vlanSelected)+": "+str(connectionToTest)+"\n")
        exit()

    ############################################################################
    if raw==str(8): 
        digestPair=getL3Digest("1.0")
        headers ={"Accept":"application/json","Content-type":"application/json","X-Level3-Application-Key":currentCarrierApplicationKey['Level3'],"X-Level3-Digest":digestPair[0],"X-Level3-Digest-Time":digestPair[1]}
        print(headers)
        exit()
    ############################################################################
    # default end
    else: print ("No selection ... Ending")	

          
if __name__ == "__main__":		
    provisionConnection("","","","");
