#!/usr/bin/env python
'''
 * FILENAME: secondAsrConfig.py
 * PURPOSE: Manage api calls to a Cisco ASR9000, this likely will change with scale.
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
'''
GLOBAL TODOS:
* Move to openconfig based models for scale and usability. Use vendor models
   only when there are features required that are not supported. Vendor models
   are largely too SLOW.
* Revisit Cisco support of OC models in latest version as well as resolution of
   commit bugs in the device agent.
* Creds need to be offloaded or placed in a higher level orchestrator.
* Consider using bgp AS from calling applications.
* Improve inbound/outbound BGP policies .. these are default all currently.
   
'''
from __future__ import print_function
from __future__ import absolute_import
from ydk.types import Empty, DELETE, Decimal64
from ydk.services import CRUDService
from ydk.providers import NetconfServiceProvider
from session_mgr import establish_session, init_logging

#from ydk.models.openconfig.openconfig_vlan import Vlans
#from ydk.models.openconfig.openconfig_interfaces import Interfaces
from ydk.models.cisco_ios_xr.Cisco_IOS_XR_l2_eth_infra_oper import Vlan as l2_io
from ydk.models.cisco_ios_xr import Cisco_IOS_XR_ifmgr_cfg \
    as xr_ifmgr_cfg
from ydk.models.cisco_ios_xr.Cisco_IOS_XR_l2_eth_infra_datatypes import VlanEnum

#bgp
from ydk.models.openconfig.openconfig_bgp import Bgp as bgp_io
from ydk.models.cisco_ios_xr.Cisco_IOS_XR_ipv4_bgp_cfg import Bgp as bgp_cfg_cisco
from ydk.models.cisco_ios_xr.Cisco_IOS_XR_ipv4_bgp_oper import Bgp as bgp_io_cisco
from ydk.models.cisco_ios_xr.Cisco_IOS_XR_ipv4_bgp_oper import BgpConnStateEnum

#latency and ping
import paramiko
import socket

from ydk.errors import YPYError
import logging, json
import time

currentEdgeDeviceInfo={};
currentEdgeDeviceInfo['IPv4']="{redacted}"; #i.e 10.0.0.0
currentEdgeDeviceInfo['username']="{redacted}"; #i.e. admin
currentEdgeDeviceInfo['password']="{redacted}"; # i.e. password123
currentEdgeDeviceInfo['NETCONFport']=000; #i.e. 830
currentEdgeDeviceInfo['AS']=00000; #i.e. 1234 local AS
#NOTE:  default security policies for WAN are used as this is dev. For 
#       production use locked down policies tailored to use.

def print_Neighbor(neighbor):
    """
    Prints state of neighbor to console.
    
    TODO: This model has some issues so code has been left in but commented out.
          Check back to see if issues have been resolved with OC ASR model
          compliance.
    
    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    neighbor: (YDK neighbor): neighbor object
    
    Returns:
    (None)
    """
    print("Config for Neighbor: " , neighbor.neighbor_address)
    show config options
    #print("   ","Password: ",str(neighbor.password))
    #print("   ","Description: ",str(neighbor.config.description))
    #print("   ","Local AS: ",str(neighbor.config.local_as))	
    #print("   ","Neighbor Address: ",str(neighbor.config.neighbor_address))	
    print("   " , "Peer AS: " , str(neighbor.remote_as))	

    # show state options
    print("State for Neighbor: ",neighbor.neighbor_address)   
    print("   " , "Current State: " , BgpConnStateEnum(neighbor.connection_state))       

def print_vlanNode(node):
    """
    Prints Vlans used on an interface.
    
    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    node: (YDK node): YDK node object
    
    Returns:
    (None)
    """
    print('*' * 28)
    print('Node_id: %s'%node.node_id)
    intVlans=0
    for i in node.trunks.trunk:
        intVlans=i.layer3_sub_interfaces.dot1q_count
        print('Number of Vlans: %s'%intVlans)
    print ('Tags Used: ')
    for i in node.tag_allocations.tag_allocation:
        print('    '+str(i.first_tag)+'    '+i.interface)
        if i.interface==strInterfaceToAct:
            if i.first_tag != None: listVlans.append(i.first_tag)

def getVlansByInterface(node,strInterfaceToAct):
    """
    Returns Vlans used on an interface.
    
    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    node: (YDK node): YDK node object
    strInterfaceToAct: (String): vendor interface name
    
    Returns:
    tagsInUse: (Array): cast to str if needed, will be an int[]
    """   
    tagsInUse=[]
    for i in node.trunks.trunk:
        intVlans=i.layer3_sub_interfaces.dot1q_count
    for i in node.tag_allocations.tag_allocation:
        if str(i.interface)==strInterfaceToAct:
            if tagsInUse.count==0: tagsInUse[0]=i.first_tag
            else: tagsInUse.append(i.first_tag)
    return tagsInUse
    

def getNeighborByASN(neighbor,ASN):
    """
    Returns Neighbors used for an ASN.
    
    TODO: THIS APPEARS TO BE USELESS
    
    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    neighbor: (YDK neighbor): YDK neighbor object
    ASN: (int): UNUSED: Autonomous System Number 
    
    Returns:
    tagsInUse: (Array): cast to str if needed, will be an int[]
    """      
    neighborData=[]
    print (neighbor[0].config.local_as)
    return neighborData

def printVlans(vlans):
    """
    Prints vlans from array to console.
    
    TODO: Fix extra None in implementation. APPEARS TO BE USELESS
    
    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    vlans: (int[]): Array of Virtual Local Area Network (VLAN) numbers

    Returns:
    (none)
    """         
    print ('Vlans in use')
    for i in vlans: 
    if len(i) != 0: 
        #TODO: fix extra None
        print (i)

def getVlansInUse(device,interface):
    """
    Get an array of vlans for a device and interface.
    
    TODO: 
    Expand into mult-endpoint support and incorporate different devices.
    Clean up error conditions.
    Change asr device argument key to me asrCiscoModel like others.
    
    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    device: (str): device type identifier being used.
        device = "asr" to use Vendor model
    interface: (str): vendor name for interface/sub interface. 

    Returns:
    vlans: (int[]): Array of Virtual Local Area Network (VLAN) numbers
    
    Error: 
    (YPYError): Prints error to console. May return [] or partial [] on error.
    """     
    vlans=[]
    if device=="asr":
        provider = NetconfServiceProvider(address=currentEdgeDeviceInfo['IPv4'],port=,username=currentEdgeDeviceInfo['username'],password=currentEdgeDeviceInfo['password'],protocol="ssh")
    crud = CRUDService()
    interfaces_filter = l2_io.Nodes()
    try:
        respNodes = crud.read(provider, interfaces_filter)
        for node in respNodes.node:
            vlans.append(getVlansByInterface(node,interface))
    except YPYError:
        print('An error occurred reading interfaces.')	
    return vlans

# Method: deleteAsNeighbors
# Parameters: device (str), AsNeighbor(str)           
# Description: deletes AS neighbor via openconfig
# Returns: Bool for success
def deleteAsNeighbor(device,AsNeighbor):
    """
    Deletes AS neighbor device config via OpenConfig NETCONF/YANG model
    
    TODO:
    Add more granularlity for CRUD delete responses.

    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    device: (str): device type identifier being used.
        device = "asr" to use OpenConfig model
    asNeighbor: (int): AS number

    Returns:
    (boolean): True if successful, False otherwise
    
    On Error: 
    (YPYError): Prints to console. Returns False.
    """     
    if device=="asr":
        provider = NetconfServiceProvider(address=currentEdgeDeviceInfo['IPv4'],port=,username=currentEdgeDeviceInfo['username'],password=currentEdgeDeviceInfo['password'],protocol="ssh")
        crud = CRUDService()
        interfaces_filter = bgp_io.Neighbors().Neighbor()
        interfaces_filter.neighbor_address = str(AsNeighbor)
    try:
        respNodes = crud.delete(provider, interfaces_filter)
    except YPYError:
        print('An error occurred delete AS: '+str(AsNeighbor))	
        return False
    return True
    
def addAsNeighbor(device,AsNeighbor,AsPassword,peerAs):
    """
    Adds AS neighbor device config via OpenConfig or Vendor NETCONF/YANG model
    
    TODO:
    Finish or adapt vendor model. Combination of both models worked/didn't work.
    Rework with newer releases of OS and YDK model support.
    Move away from the vendor model for performance considerations.
    Fix the vendor model, this may not work.
    Update interface description in vendor model.

    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    device: (str): device type identifier being used.
        device = "asr" to use OpenConfig model
        device = "asrCiscoModel" to use vendor model.
    AsNeighbor: (str): AS number of this device
    AsPassword: (str): AS password to use for BGP secret key
    peerAs: (str): AS number of the peer device

    Returns:
    (boolean): True if successful, False otherwise
    
    On Error: 
    (YPYError): Prints message to console. Returns False.
    """         
    if device=="asr":
        provider = NetconfServiceProvider(address=currentEdgeDeviceInfo['IPv4'],port=,username=currentEdgeDeviceInfo['username'],password=currentEdgeDeviceInfo['password'],protocol="ssh")
        crud = CRUDService()
        interfaces_filter = bgp_io.Neighbors().Neighbor()
        interfaces_filter.neighbor_address = str(AsNeighbor)
        config_interface = interfaces_filter.Config()
        config_interface.auth_password=AsPassword
        config_interface.peer_as=peerAs
        interfaces_filter.config=config_interface
    if device=="asrCiscoModel":
        provider = NetconfServiceProvider(address=currentEdgeDeviceInfo['IPv4'],port=,username=currentEdgeDeviceInfo['username'],password=currentEdgeDeviceInfo['password'],protocol="ssh")
        crud = CRUDService()
        #READ: instances.instance.instance_active.default_vrf.neighbors
        #write with cfg: 
        #bgp_cfg_cisco.Bgp.Instance.InstanceAs.FourByteAs.Vrfs.Vrf.VrfNeighbors.VrfNeighbor
        baseObj=bgp_cfg_cisco.Bgp().Instance()
        baseObj.instance_name="default"
        baseIas = bgp_cfg_cisco.Bgp.InstanceAs().FourByteAs()
        baseIas.default_vrf=bgp_cfg_cisco.Bgp.Instance.InstanceAs.FourByteAS.DefaultVrf()
        baseNeighbor=baseIas.BgpEntity().Neighbors().Neighbor()
        baseNeighbor.neighbor_address = str(AsNeighbor)
        baseNeighbor.description = "TODO: UPDATED"
        baseNeighbor.password = str(AsPassword)
        baseNeighbor.remote_as = "" #TODO:P obj   #RESTART HERE BGP_CFG.PY
        interfaces_filter =""
    try:
        respNodes = crud.create(provider, interfaces_filter)
    except YPYError:
        print('An error occurred add AS: '+str(AsNeighbor))	
        return False
    return True

      
def getAsNeighborStatus(model,neighborIp):
    """
    Provides AS neighbor connection status via specified model.
    
    TODO:
    Add multi device and multi vendor support
    Sync with the rest of the file, use either model or device or both
    Consider adding IPv6 support in the future
    Restore OC model when funcional with YDK and device

    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    model: (str): device type identifier being used.
        model = "asrCiscoModel" to use vendor model.
    neighborIp: (str): IPv4 address for neighbor

    Returns:
    (YDK Connection_state str): AS connection state
    
    On Error: 
    (YPYError): Returns "" on error
    """    
    if model=="asrCiscoModel":
        provider = NetconfServiceProvider(address=currentEdgeDeviceInfo['IPv4'],port=,username=currentEdgeDeviceInfo['username'],password=currentEdgeDeviceInfo['password'],protocol="ssh")
        crud = CRUDService()
        bgpInstances = bgp_io_cisco.Instances().Instance()
        bgpInstances.instance_name = "default"
        neighborInst=bgpInstances.instance_active.default_vrf.neighbors.Neighbor()
        neighborInst.neighbor_address=str(neighborIp)
        bgpInstances.instance_active.default_vrf.neighbors.neighbor.append(neighborInst)
        interfaces_filter = neighborInst
        
    if model=="asr": 
        pass
        #provider = NetconfServiceProvider(address=currentEdgeDeviceInfo['IPv4'],port=,username=currentEdgeDeviceInfo['username'],password=currentEdgeDeviceInfo['password'],protocol="ssh")		
        #crud = CRUDService()
        #interfaces_filter = bgp_io.Neighbors()
    try:
        respNeighbor = crud.read(provider, interfaces_filter)
        if model=="asrCiscoModel":
            return respNeighbor.connection_state
    except YPYError:
        print('An error occurred reading interfaces.')	
    return ""

def getAsNeighbors(device,ASN,excludeThese):
    """
    Provides AS neighbor connection status via specified model.
    
    TODO:
    Add multi device and multi vendor support
    Consider adding IPv6 support in the future

    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    device: (str): device type identifier being used.
        device = "asr" to use OpenConfig model
        device = "asrCiscoModel" to use vendor model.
    ASN: (str): AS Number to query.
    excludeThese: (str[]): List of neighbor IPs to exclude

    Returns:
    (str []): Array of neighbor IP addresses 
    
    On Error: 
    (YPYError): Returns [] on error and prints message to console.
    """       
    neighbors=[]
    if device=="asrCiscoModel":
        provider = NetconfServiceProvider(address=currentEdgeDeviceInfo['IPv4'],port=,username=currentEdgeDeviceInfo['username'],password=currentEdgeDeviceInfo['password'],protocol="ssh")
        crud = CRUDService()
        bgpInstances = bgp_io_cisco.Instances().Instance()
        bgpInstances.instance_name = "default"
        interfaces_filter = bgpInstances
    
    if device=="asr":
        provider = NetconfServiceProvider(address=currentEdgeDeviceInfo['IPv4'],port=,username=currentEdgeDeviceInfo['username'],password=currentEdgeDeviceInfo['password'],protocol="ssh")
        crud = CRUDService()
        interfaces_filter = bgp_io.Neighbors()
    try:
        respNodes = crud.read(provider, interfaces_filter)
        if device=="asrCiscoModel":
            respNodes = respNodes.instance_active.default_vrf.neighbors
        for neighbor in respNodes.neighbor:
            if excludeThese in neighbor.neighbor_address:
                next
            else: 
                print (print_Neighbor(neighbor))
                neighbors.append(neighbor.neighbor_address)
    except YPYError:
        print('An error occurred reading interfaces.')	
    return neighbors

def addVlanToExisitingInterface(device,interface,vlan):
    """
    Adds a subinterface to a Cisco ASR. Automatically assigns ip addressing
    based on the VLAN used.
    
    TODO:
    Add multi device and multi vendor support
    Consider adding IPv6 support in the future
    Consider impact of autoassignment on multiple interfaces on a single 
        device and potential collisions.
    Integrate to Defense Digital Storefront to obtain order information to 
        place on interface.
    When vendor has the OC model working implement it.

    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    device: (str): device type [UNUSED for future use]
    interface: (str): Vendor identifier of interface/subinterface
    vlan: (int): vlan number to use [will be casted to int if you send str]

    Returns:
    (boolean,YDK crud response, dictWanIp Object):
    (boolean): Success of the creation
    (YDK crud response): YDK response object
    (dictWanIp Object): Dict of IP addressing used.
    
    On Error: 
    (Any Exception to call): Returns False,{},{}.
    """    
    interface_configurations = xr_ifmgr_cfg.InterfaceConfigurations() 
    # configure IPv4 address
    interface_configuration = interface_configurations.InterfaceConfiguration()
    interface_configuration.active = "act"
    interface_configuration.interface_name = str(interface)+"."+str(vlan)
    interface_configuration.interface_mode_non_physical = xr_ifmgr_cfg.InterfaceModeEnumEnum.default
    interface_configuration.description = "Connect to AWS CJON No. XXXXXX"
    primary = interface_configuration.ipv4_network.addresses.Primary()
    #get ipv4 addressing for wan
    dictWanIp=getInternetAddressPairForWan(int(vlan))
    primary.address = dictWanIp['ipDisaDemarc'] 
    primary.netmask = dictWanIp['ipNetmask'] 
    interface_configuration.ipv4_network.addresses.primary = primary
    subinterface = interface_configuration.VlanSubConfiguration().VlanIdentifier()
    subinterface.first_tag=int(vlan)
    subinterface.vlan_type=VlanEnum(2)
    interface_configuration.vlan_sub_configuration.vlan_identifier = subinterface
    interface_configurations.interface_configuration.append(interface_configuration)
    # create NETCONF provider
    provider = NetconfServiceProvider(address=currentEdgeDeviceInfo['IPv4'],port=,username=currentEdgeDeviceInfo['username'],password=currentEdgeDeviceInfo['password'],protocol="ssh")
    # create CRUD service
    crud = CRUDService()
    try:
        response=crud.create(provider, interface_configurations)
    except:
        provider.close()
        return (False,{},{})
    provider.close()
    return (True,response,dictWanIp)

def deleteVlanFromExisitingInterface(device,interface,vlan):
    """
    Deletes subinterface on a Cisco ASR9XXX. 
    
    TODO:
    Add multi device and multi vendor support
    Consider adding IPv6 support in the future
    When vendor has the OC model working implement it.

    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    device: (str): device type [UNUSED for future use]
    interface: (str): Vendor identifier of interface/subinterface
    vlan: (int): vlan number to use [will be casted to int if you send str]

    Returns:
    (boolean): True for success of the deletion.

    On Error: 
    (Any Exception to call): Returns False
    """     
    interface_configurations2 = xr_ifmgr_cfg.InterfaceConfigurations().InterfaceConfiguration()
    interface_configurations2.interface_name = str(interface)+"."+str(vlan) 
    interface_configurations2.interface_mode_non_physical = xr_ifmgr_cfg.InterfaceModeEnumEnum.default   
    interface_configurations2.active = "act" 
    provider = NetconfServiceProvider(address=currentEdgeDeviceInfo['IPv4'],port=,username=currentEdgeDeviceInfo['username'],password=currentEdgeDeviceInfo['password'],protocol="ssh")
    crud = CRUDService()
    try:
        crud.delete(provider, interface_configurations2)
    except:
        provider.close()
        return (False)
    provider.close()
    return(True)

# Returns:all str dict with {ipDisaDemarc:v4 address for disa wan, ipAWSDemarc:v4 address for AWS wan, ipNetmask:v4 netmask }	
def getInternetAddressPairForWan(vlan):
    """
    Returns the AS WAN IP /31 address pair based on a specific vlan. Supports 
    1024 VLANs currently. Pinned to 10.0.[220-227].X space currently. IPv4 only.
    For vlans < 256 the last octet of the local IP will match the Vlan.
    
    TODO:
    Consider removing use of vlan 1 as it may be default on some vendor gear. 
        Explore whether this will be solved by checking vlans in use.
    Determine if this will scale or implement in another system managing IP
        address assignments.
    Determine how this could be used with multiple interfaces to the same 
        datacenter or different datacenters.
    Update netmask to a datastructure/class to handle various /CIDR values

    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    vlan: (int): Vlan number to use [will be casted to int if you send str].
                 Value should be between 1 and 1023. Consider not using 1.

    Returns:
    (dict): {}
        ipDisaDemarc:v4 address for local WAN Interface, 
        ipAWSDemarc:v4 address for remote WAN Interface,
        ipNetmask:v4 netmask (i.e. 255.255.255.254)

    On Error: 
    (Any Exception to call): Returns False
    """         
    ipDisaDemarc=""
    ipAWSDemarc=""
    ipNetmask="255.255.255.254" 
    vlan = int(vlan)
    if (divmod(vlan,2)[1]) == 1: #handle odd vlans
        #using 10.0.221/223/225/227.0-254/31
        #vlan 1 is lowest, highest is 1023
        if (vlan>=1 and vlan<=255): 
            ipDisaDemarc="10.0.221."+str(vlan)
            ipAWSDemarc="10.0.221."+str(vlan-1)
        elif (vlan>=256 and vlan<=511): 
            ipDisaDemarc="10.0.223."+str(vlan-256)
            ipAWSDemarc="10.0.223."+str(vlan-257)
        elif (vlan>=512 and vlan<=767): 
            ipDisaDemarc="10.0.225."+str(vlan-512)
            ipAWSDemarc="10.0.225."+str(vlan-513)
        elif (vlan>=768 and vlan<=1023):
            ipDisaDemarc="10.0.227."+str(vlan-768)
            ipAWSDemarc="10.0.227."+str(vlan-769)
    else: #handle even vlans
        #using 10.0.220/222/224/226.0-254/31
        #vlan 2 is lowest, highest is 1024
        
        if (vlan>=1 and vlan<=255): 
            ipDisaDemarc="10.0.220."+str(vlan)
            ipAWSDemarc="10.0.220."+str(vlan+1)
        elif (vlan>=256 and vlan<=511): 
            ipDisaDemarc="10.0.222."+str(vlan-256)
            ipAWSDemarc="10.0.222."+str(vlan-255)
        elif (vlan>=512 and vlan<=767): 
            ipDisaDemarc="10.0.224."+str(vlan-512)
            ipAWSDemarc="10.0.224."+str(vlan-511)
        elif (vlan>=768 and vlan<=1023):
            ipDisaDemarc="10.0.226."+str(vlan-768)
            ipAWSDemarc="10.0.226."+str(vlan-767)
    wanIpPackage={}
    wanIpPackage['ipDisaDemarc']=ipDisaDemarc
    wanIpPackage['ipAWSDemarc']=ipAWSDemarc
    wanIpPackage['ipNetmask']=ipNetmask
    return wanIpPackage


def pingIpv4Destination(destip,ip,port):
    """
    Connects via SSH to a ASR 9000 device and pings a distant WAN link via
    CLI commands that ping out the actual subinterface. Processes the response
    from the device and prints RTT latency and success result to console.
    
    TODO:
    Push for incorporation in vendor and OpenConfig models. Both latency and
        success are important.
    Expand to return status and latency.
    Consider IP based methods to measure rather than use ICMP (if possible.)
    Consider changing return logic to prevent infinite loops when there is an
        issue with getting the ping, not simply that the ping failed.

    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters: 
    destip: (str): remote WAN link interface/subinterface IP
    ip: (str): local WAN link IP of the subinterface
    port: (str): vendor interface description to ping from including the 
                 subinterface
    Returns:
    (Boolean) True if successful. False if unsuccessful or error.

    On Error: 
    (Various Exceptions): Prints console message regarding type of error
    """         
	latency=-1
	dssh = paramiko.SSHClient()
	dssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	try:
		dssh.connect(ip,username=currentEdgeDeviceInfo['username'],password=currentEdgeDeviceInfo['password'], timeout=4)
		stdin, stdout, stderr = dssh.exec_command('ping ipv4 '+str(destip)+' count 4 source '+str(port))
		output=[]
		output=stdout.read().split("\n")
		print (str(output[4]))
		print (str(output[6]))
		percentSuccess = int(output[6].split(" ")[3])
		if percentSuccess==100: print ("Link Ping Test Successful")
		else: 
			print ("Link Ping Test Failed")
			return False
		estimateLatencyMax = int(output[6].split(",")[1].split(" ")[4].split("/")[2])
		estimateLatencyMin = int(output[6].split(",")[1].split(" ")[4].split("/")[0])
		estimateLatencyAvg = int(output[6].split(",")[1].split(" ")[4].split("/")[1])
		print ("Max Round-Trip Latency is: "+str(estimateLatencyMax)+" ms")
		
	except paramiko.AuthenticationException:
		print (ip + '=== Bad Credentials')
		return False
	except paramiko.SSHException:
		print (ip + '=== Issues with ssh service')
		return False
	except socket.error:
		print (ip + '=== Device unreachable')
		return False
	except: 
		print (ip + '=== unspecified SSH error')
		dssh.close()
		return False
	dssh.close()
	return True

def manConfigBgpNeighbor(ip,neighborIp,remoteAs,wanPword):  
    """
    Connects via SSH to an ASR 9000 device and provisions to BGP neighbor on an
    exiting subinterface that has already been created.
    
    TODO:
    Check back with vendor to see if between YDK and the ASR they can properly
        support their model and OC's model then implement.

    Author:
    David J. Stern

    Date:
    DEC 2017
    
    Parameters:
    ip: (str): local WAN link IP of the subinterface
    neighborIp: (str): remote WAN link interface/subinterface IP
    remoteAs: (int): remote AS to connect to [this will be casted to str]
    wanPword: (str): password to use for the BGP secret
    Returns:
    (Boolean) True if successful. False if unsuccessful or error.

    On Error: 
    (Various Exceptions): Prints console message regarding type of error
    """     
    dssh = paramiko.SSHClient()
    dssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    stderr=[]
    try:
        dssh.connect(ip,username=currentEdgeDeviceInfo['username'],password=password=currentEdgeDeviceInfo['password'],look_for_keys=False,allow_agent=False)
        commands=['config\n','router bgp '+str(currentEdgeDeviceInfo['AS'])+'\n','neighbor '+str(neighborIp)+'\n','remote-as '+str(remoteAs)+'\n','password '+str(wanPword)+'\n','address-family ipv4 unicast\n','route-policy ALLOW-ALL in\n','route-policy ALLOW-ALL out\n','soft-reconfiguration inbound always\n','commit\n','end\n']
        channel = dssh.invoke_shell()
        print ("Manually Configuring device via CLI\n ")
        for i in commands:
            print (i)
            channel.sendall(i)
            time.sleep(1) #TODO: replace this will a more elegant check from paramiko.
    except paramiko.AuthenticationException:
        print (ip + '=== Bad Credentials')
        dssh.close()
        return False
    except paramiko.SSHException:
        print (ip + '=== Issues with ssh service')
        dssh.close()
        return False
    except socket.error:
        print (ip + '=== Device unreachable')
        dssh.close()
        return False
    except:
        print("Unspecifed BGP Error")
        dssh.close()
        return False
    dssh.close()
    return True