/*
 * FILENAME: index.js
 * AUTHORS: Mr. Dan Burnham, Mr. David J. Stern
 * DATE: DEC 2017
 * AGENCY: Defense Information Systems Agency
 * DEPARTMENT: Defense
 * GOVERNMENT: United States
 * THIS WORK IS IN THE PUBLIC DOMAIN. See relevant license information for its intended use. 
 * This work is solely a Government work product and no contractors participated in its creation.
 * 
 * PURPOSE: Javascript file for functionality that supports HTML UI.
 */


//global variables that should be updated
	var mapServerSchemeAuthority="http://192.168.100.28"; // this will be your map server
	var webServerSchemeAuthority="http://192.168.100.27:8000"; // this is your web server
	var defaultLatLong=[11.1111,-11.1111]; //NOTE: replace with actual location value
	var defaultZoom=8;

//global variable declaration section
	
	var awstotalavailablebandwidth = 0; //this is a cheat
	var mstotalavailablebandwidth = 0; //this is also a cheat
	var flag=0;
	var latlong=[];
	var orderWindow=0; //placeholder global variable for the orderWindow.
	var popupText='ORDER'; //placeholder global variable for the "order" button text.
	var firstTime = true; //placeholder global variable for the first time through.
	var uniList = []; //placeholder global array variable for all the UNIs (User Network Interface) select list.
	var uni1List = []; //placeholder global array variable for the UNI1 select list.
	var uni2List = []; //placeholder global array variable for the UNI2 select list.
	var uni1VLANList = []; //placeholder global array variable for the UNI1 VLAN select list.
	var uni2VLANList = []; //placeholder global array variable for the UNI2 VLAN select list.
	var currentPopup = null; //global variable for current open Popup.
	var orderProcessFlag = false; //first attempt at the setup to check if first time fireing event
	var uniPlacementNumber = 1; //quick and dirty global for what UNI is being added...
	var cartEmpty = true;
	var dialogboxAnimate = true;
	var processEndPointdone = false; //quick and dirty flags for if processing has finished on the ajax call.
	var processEndPointsdone = false;
	var provisioningError = [];
	// global icons
	var awsIcon=L.icon({iconUrl:'./leaflet/images/amazon_100.png'});
	// global timers
	var anim1,anim2; //TODO: make this scalable by using a class / non global obj	

//map instantiation section - this is done differently between the online and offline versions.
	var mymap = L.map('mapid').setView(defaultLatLong,defaultZoom);
	L.tileLayer(mapServerSchemeAuthority+'/{id}/{z}/{x}/{y}.png',{
		maxZoom: 14,	
		attribution: 'Map data &copy; OpenStreetMap contributors via CC-BY-SA',
		id: 'osm'
		}).addTo(mymap);

	mymap.on("popupopen", popupOpen);

/* @function processEndpoint
 * Function that processes the capabilities of the default connectivity node 
 * @author: Mr. David J. Stern
 * @param  jQuery response: from the initial AJAX call for vendor node info.
 */
	function processEndpoint(response){
		var totalbandwidthAvailable = 0; //local variable for adding the bandwidth available. Since there is only one endpoint, this is not really used very well here, but it is here for consistancy with the processEndpoints function. Currently the value is not returned, as the return occurs after the async call completes so the orginal specified target doesnt exist correctly.
		uniList.push(response.unis[0]); 
		L.marker([response.unis[0].latitude.toString(),response.unis[0].longitude.toString()],{title:response.unis[0].locationId.toString()}).bindPopup("Port Speed: "+response.unis[0].uniPortSpeed+"<br>Available: "+displayThroughput(response.unis[0].bandwidthAvailable)+"<br><center><button class='myButton' id='orderButton' onclick='orderButton(this,"+JSON.stringify(response.unis[0])+")'>ORDER</button></center>",{closeButton:true}).addTo(mymap);
 
		latlong[latlong.length++]={lat:response.unis[0].latitude.toString(),long:response.unis[0].longitude.toString(),uni:response.unis[0].uniServiceId.toString()};
		flag++;
		if (flag==2){getConnections()}
		totalbandwidthAvailable += (response.unis[0].bandwidthAvailable/1000000000); //BW in Gbps
	}

/* @function processEndpoints
 * Function that processes the response for an endpoint when more than one reply is expected. Response to create connection?
 * @author: Mr. David J. Stern, Mr. Dan Burnham
 * Modified to push the response by element to the global uniList as well as the modification to the html button to support the ordering dialog.
 * @param jQuery response: Request from the user for a connection?
 */
	function processEndpoints(response){
		var totalbandwidthAvailable = 0; //local variable for adding the bandwidth available.
		for (i=0,len=response.unis.length;i<len;i++){
			//add Endpoint to the UNI array
			uniList.push(response.unis[i]);
			L.marker([response.unis[i].latitude.toString(),response.unis[i].longitude.toString()],{icon:awsIcon,title:response.unis[i].locationId.toString()}).bindPopup("Port Speed: "+response.unis[i].uniPortSpeed+"<br>Available: "+displayThroughput(response.unis[i].bandwidthAvailable)+"<br><center><button class='myButton' id='orderButton' onclick='orderButton(this,"+JSON.stringify(response.unis[i])+")'>ORDER</button></center>",{closeButton:true}).addTo(mymap);
			latlong[latlong.length++]={lat:response.unis[i].latitude.toString(),long:response.unis[i].longitude.toString(),uni:response.unis[i].uniServiceId.toString()}
			totalbandwidthAvailable += (response.unis[i].bandwidthAvailable/1000000000);
		}
		flag++;if (flag==2){getConnections()}
		//console.log('processEndpoints completed.'); //this is here for debugging purposes.
		//Next line is a cheat. Instead of using the return, the needed object created and an event is manually fired off to cause the display to update.
		awstotalavailablebandwidth = {name:response.receivedParams.billingAccountNumber, bandwidthAvailable:totalbandwidthAvailable};
	}

/* @function processConnections
 * Function to start to plot active connections on the map.
 * @author: Mr. David J. Stern, Mr. Dan Burham 
 * @param jQuery response: Response
 * 
 */
	function processConnections(response){
		//console.log('processConnections started.'); //this is here for debugging purposes.
		for (var k=0, len=response.length; k<len; k++) {
			if (response[k].connectionStatus=="active") {
				var lat1long1=getLatLongByUni(response[k].endPoint1.uniServiceId);
				var lat2long2=getLatLongByUni(response[k].endPoint2.uniServiceId);
				var pointA = new L.LatLng(lat1long1[0].toString(),lat1long1[1].toString());
				var pointB = new L.LatLng(lat2long2[0].toString(),lat2long2[1].toString())
				var pointList = [pointA,pointB];

				var polylineA=L.polyline(pointList,{
					color:'black',
					weight: 3,
					smoothFactor:1			
				}).addTo(mymap);
				L.popup({closeButton:true})
					.setLatLng(polylineA.getCenter())
					.setContent('<b>'+response[k].evcServiceId+'</b><br>Throughput:'+displayThroughput(response[k].bandwidth)+'<br>')
					.openOn(mymap);
							}
		}
		//console.log('processConnections completed'); //here for debugging purposes
		firstTime = false; //no longer the first time anymore...
		//This is a flag that controls if the map will zoom to where the popup was created on the line. As this is very annoying during testing, this was added to stop that behavior in a reversable way.
	}

/* @function animateLine
 * Function to animate line while provisioing a connection via a timer.
 * @author: Mr. David J. Stern 
 * @param objLine Line on map to animate
 */	
	function animateLine(objLine){
		function phase1(){
			objLine.setStyle({dashArray:'5,5',color:'green'});
		}
		function phase2(){
			objLine.setStyle({dashArray:'5,5',color:'white'});		
		}
		anim1 = window.setInterval(phase1, 60);
		anim2 = window.setInterval(phase2, 90);
	}

/* @function clearLineAnimation
 * Function to clear timers for a connection being provisioned.
 * @author: Mr. David J. Stern 
 * @param objLine Line on map to clear
 */
	function clearLineAnimation(objLine){ //TODO: remove the objLine it is not needed
		window.clearInterval(anim1);
		window.clearInterval(anim2);
	}
	
/* @function placeBlinkyLines
 * Function to implement a line for a provisioning connection, then animate it.
 * @author: Mr. David J. Stern  
 * @param uni1 Carrier's User Network Interface (UNI) for first endpoint
 * @param uni2 Carrier's User Network Interface (UNI) for second endpoint
 */
	function placeBlinkyLines(uni1,uni2){
		var lat1long1=getLatLongByUni(uni1);
		var lat2long2=getLatLongByUni(uni2);
		var pointA = new L.LatLng(lat1long1[0].toString(),lat1long1[1].toString());
		var pointB = new L.LatLng(lat2long2[0].toString(),lat2long2[1].toString());
		var pointList = [pointA,pointB];

		var polylineA=L.polyline(pointList,{
			color:'gray',
			weight: 3,
			smoothFactor:1			
		}).addTo(mymap);
		animateLine(polylineA);

		firstTime = false; //no longer the first time anymore...
		//This is a flag that controls if the map will zoom to where the popup was created on the line. As this is very annoying during testing, this was added to stop that behavior in a reversable way.
	}

/* @function runstuff
 * Function to call things in the right order at the right time. Initally needed for offline testing, but is still useful during the operation of the page.
 * @author: Mr. Dan Burnham
 * this function is called at the very end of the script file.
 */	
	function runstuff(){
		//TODO - organize what is occuring here better than it currently is.
		//console.log('function runstuff()');
		availablebandwidthDisplay.addTo(mymap); //add the control for the availablebandwidthDisplay to the map.
		
		mymap.on('endprocessEndpoints', endprocessEndpoints); //defines the function to run when 'endprocessEndpoints' event occurs.
		mymap.on('endprocessEndpoint', endprocessEndpoint); //defines the function to run when 'endprocessEndpoint' event occurs.
	}
/* * 
 * REFERENCE: @link code snippet from http://stackoverflow.com/questions/2618959/not-well-formed-warning-when-loading-client-side-json-in-firefox-via-jquery-aj
 * @author: Mr. Dan Burnham 
 * Function that allows the call to a local file for the json data using $.getJSON 
 * this is better for testing that using a 'fake' function to parse the JSON in a way that is different from
 * from how it will be used on the webserver.
 */
	$.ajaxSetup({beforeSend: function(xhr){
		if (xhr.overrideMimeType){
			xhr.overrideMimeType("application/json");
		}
	}
	});

/* @function getMdEndpoint
 * Function to get carrier and local connection information for default endpoint.
 * This function allows this same code to be called from different parts of the script without duplicating it.
 * @author: Mr. David J. Stern, Mr. Dan Burnham 
 * @param callback Function to be called upon completion
 * TODO: Rename function to make generic and any associated code changes 
 */
	function getMdEndpoint(callback){
		if (callback === undefined){ //this means first time on a full page reload
			//console.log('getMdEndpoint callback === undefined');
			callback = false;
		}
		$.getJSON(webServerSchemeAuthority+"/www/b_p_c_s_md.py", processEndpoint)
			.done(function() {
				//console.log('$.getJSON("./b_p_c_s_md.py", processEndPoint) success.');
				processEndPointdone = true;
				if (callback === true){
					//now set the ok box back to the order dialog
					customcartControl.changeContent('<button type="button" class="btn btn-default custom-cart-button">'+
					'<i class="fa fa-comment-o fa-lg" aria-hidden="true"></i>'+
					'</button>');
				}
				mymap.fire('endprocessEndpoint'); //fires event to cause redraw of the available bandwidth control
			})
			.fail(function( jqXHR, textStatus, errorThrown){
				console.log('$.getJSON("./b_p_c_s_md.py", processEndPoint) failed: ' + textStatus + ' : ' + errorThrown);
			});
	}
	
	
	getMdEndpoint(); //TODO: consolidate this with other actions to preserve ordering
	
/* @function getAWSendpoints
 * Function to get Endpoints for the particular resource 
 * @author: Mr. David J. Stern, Mr. Dan Burnham  
 * @param callback Function to be called upon completion
 */
	function getAWSendpoints(callback) { //TODO: anonymize this but AWS was the first test case.
		if (callback === undefined){ //this means first time on a full page reload
			console.log('getAWSEndpoints callback === undefined');
			callback = false;
		}
		$.getJSON(webServerSchemeAuthority+"/www/b_p_c_s_AWS_endpoints.py", processEndpoints)
			.done(function() {
				//console.log('$.getJSON("./b_p_c_s_AWS_endpoints.py", processEndPoints) success.');
				//repopulateuni1List();
				processEndPointsdone = true;
				if (callback === true){
					//now set the ok box back to the order dialog
					customcartControl.changeContent('<button type="button" class="btn btn-default custom-cart-button">'+
					'<i class="fa fa-comment-o fa-lg" aria-hidden="true"></i>'+
					'</button>');
				}
				mymap.fire('endprocessEndpoints'); //fires event to cause redraw of the available bandwidth control
			})
			.fail(function( jqXHR, textStatus, errorThrown){
				console.log('$.getJSON("./b_p_c_s_AWS_endpoints", processConnections) failed: ' + textStatus + ' : ' + errorThrown);
			});
	}
	
	getAWSendpoints(); //TODO: consolidate this with other actions to preserve ordering
	
	//This line was moved out of the runstuff function so the variable was created at the right time...
	var mstotalavailablebandwidth = {name:"Microsoft",bandwidthAvailable:"0"}; //This could be other endpoint operators as well

/* @function getConnections
 * Function obtains connection from the webserver then passes the response to the processConnections function.
 * Modified to include .done and .fail promises and logging.
 * @author: Mr. David J. Stern, Mr. Dan Burnham 
 */	
	function getConnections(){
		//console.log('getConnections started.'); //TODO: modify this to push this logic upstream into web server.
		var temp_jqxhr = $.getJSON(webServerSchemeAuthority+"/www/level3_connections.py", processConnections)
			.done(function() {
				//console.log('$.getJSON("./level3_connections.py.json", processConnections) success.');
			})
			.fail(function( jqXHR, textStatus, errorThrown){
				console.log('$.getJSON("level3_connections.py.json", processConnections) fail: ' + textStatus + ' : ' + errorThrown);
			});
		//console.log('getConnections completed.');
	}

/* @function getLatLongByUni
 * Function to get latitue and longitude of a carrier UNI
 * @author Mr. David J. Stern 
 * @param uni User Network Interface
 * @returns {int[]} The lat and longitude for a carrier UNI //TODO: handle negative condition although it should never happen
 */
	function getLatLongByUni(uni){
		for (var j=0;j<latlong.length;j++){
			if (latlong[j]['uni']==uni){
				return ([latlong[j]['lat'],latlong[j]['long']]);
			}		
		}
	}

/* @function displayThroughput
 * Function to provide human readable speed in bps, Kbps, Mbps, or Gbps
 * @author Mr. David J. Stern  
 * @param {int} spdInt This is the speed to be returned for pretty printing. 
 */
	function displayThroughput(spdInt){
		var text="";
		if (spdInt<1000){text=spdInt.toString() + " bps";}
		else if (spdInt<1000000){text=spdInt.toString() + " Kbps";}
		else if (spdInt<1000000000){text=(spdInt/1000000).toString() + " Mbps";}	
		else if (spdInt<1000000000000){text=(spdInt/1000000000).toString() + " Gbps";}			
		return text;
	}

/* 
 * First the handle is created for the new control, then the .onAdd and .update components are defined.
 * @author Mr. Dan Burnham  
 * TODO: create a .onRemove function, as Leaflet expects one to exist.
 * TODO: relook how to move this into multiple carriers to be displayed or summarized.
 */
	var availablebandwidthDisplay = L.control({position: 'bottomleft'});
	availablebandwidthDisplay.onAdd = function (mymap) {
		this._div = L.DomUtil.create('div', 'info legend');
		this._div.innerHTML = 'Commercial Carrier Global Capability<br>CenturyLink:<br>'; 
		this.update();
		return this._div;
	};

/*
 * Handle used to update the available bandwidth display. 
 * @author Mr. Dan Burnham   
 */
	availablebandwidthDisplay.update = function (props) {
		this._div.innerHTML = 'Commercial Carrier Global Capability<br>CenturyLink:<br>';
		if (props !== undefined){
			for (var i=0; i<props.length; i++){
				props[i].name = accountId2Name(props[i].name);
				this._div.innerHTML += '<i ></i>' + (props[i] ? props[i].name + ':' + props[i].bandwidthAvailable + ' Gbps<br>' :'No props available');
			}
		}
		else {
			//this._div.innerHTML += 'No props passed to function availablebandwidthDisplay';
			this._div.innerHTML += 'Waiting for information from Service Provider...';
		}	
	};

/* @function accountId2Name
 * This function just puts in code the translation of the given account number to text for the available bandwidth display. It can be easily extended by adding more if or else if statements. 
 * @author Mr. Dan Burnham 
 * @param {int} accountId Account ID
 * @return {str} The friendly name that is mapped to an account number
 * TODO: work on this for scaling of multiple endpoint service providers (not carriers)
 * TODO: change structure for passing friendly name of provider instead of 
 *       accountId of provider in orch system
 */	
	function accountId2Name(accountId){
		if (accountId === '1'){
			accountId = 'Amazon';
		}
		return accountId;
	}

/* @function endprocessEndpoints
 * Event handler that runs when the 'endprocessEndpoints' event fires. This 
 * causes an update to the availablebandwidthDisplay. 
 * @author Mr. Dan Burnham 
 * @param {Event} e Event
 */			
	function endprocessEndpoints(e){
		availablebandwidthDisplay.update([awstotalavailablebandwidth, mstotalavailablebandwidth]);
	}

/* @function popupOpen
 * Function that listens for a popup to open and then copies the popup object to 
 * a global variable so the popup can be closed. This function also changes the
 * labels of the popups so that initially they stay in Order but once a UNI1 has 
 * been selected, they say Add to Order. Also it changes them back when an order 
 * is completed or if UNI1 is deselected.
 * @author Mr. Dan Burnham  
 * @param {Event} e Event
 */	
	function popupOpen(e){
		currentPopup = e.popup;
		//console.log('popupopen event occured.');
		//console.log('orderProcessFlag value is: ' + orderProcessFlag);
		if (firstTime === true){
			//the only purpose of this code is to stop the movement of the 
			//window away from the defined display area when the connections 
			//are processed to reduce zoomout and scrolling while testing.
			currentPopup = null;
			mymap.setView(defaultLatLong,defaultZoom);
			return;
		}
		if (orderProcessFlag === false){
			//this is more of a do nothing, but that only works for the first 
			//time around. If the button text is changed after UNI1 selected but 
			//is not changed back if an order is "cancelled" or even submitted 
			//then it wont look right...
			
			var regexstr = /(Port.*'>)Add to Order(<\/button><\/center>)/; //regular expression search expression
			var n = currentPopup.getContent().search(regexstr);
			n = currentPopup.getContent().replace(regexstr, '$1Order$2');
			currentPopup.setContent(n);
			currentPopup.update();
		}
		else if (orderProcessFlag === true) {
			//change the order button text to add to order
			var regexstr = /(Port.*'>)ORDER(<\/button><\/center>)/;
			var n = currentPopup.getContent().search(regexstr);
			n = currentPopup.getContent().replace(regexstr, '$1Add to Order$2');
			currentPopup.setContent(n);
			currentPopup.update();
		}
		else {
			//catch all
			//console.log("popupopen event catch all traversed!"); //should never get here.
		}
	}

/* @function orderButton
 * Function enables the clicking of the "Order" or "Add to Order" button on the 
 * map popups and have the correct things happen with the order dialog. They 
 * also make the order dialog visible after such an occurrence. Popup is closed 
 * after the new order popup is created.
 * @author Mr. Dan Burnham  
 * @param {} thing not used //TODO: remove this parameter
 * @param jsonResponseUni ??
 */		
	function orderButton(thing, jsonResponseUni){
		//console.log('Order button clicked');
		//console.log('jsonResponse: ' + jsonResponseUni.uniServiceId);
		orderEvent(jsonResponseUni); //the function called orderEvent isn't 
		//really an event anymore, but still performs needed functions. The name
		//wasnt changed as it might be an event again some day.
		if (currentPopup !== null){ //this check closes the popup that had the button on it.
			currentPopup._source.closePopup();
			currentPopup = null;
		}
	}
	
//TODO - Need a watching function so that when getEndpoint or getEndpoints is called again or after a defined period of time has elapsed that causes the reevalution of the uniList and availablebandwidth, etc.

/* @function createDialogBox
 * Function creates the dialog box that is needed for the order entry dialog, 
 * and does the jQuery UI widget initalization for the buttons and select menus 
 * inside the dialog box.
 * @author Mr. Dan Burnham
 */	
	function createDialogBox(){
		$( "#orderBox" ).dialog({
			autoOpen: false,
			width:950,
			show: { 
			},
			hide: { 
			},
			title: "RTFN-MIL/GOV PROVISIONING",
			buttons: [
				{
					text: "Submit Order",
					click: function() {
						orderSubmitPressed();
					}	
				}
			],
			classes: {
				"ui-dialog": 'leaflet-control leaflet-control-window'
				//had to tell leaflet this was a control to make it visible
			},
			position: {
				my: "left top",
				at: "right bottom",
				of: window
			}
		});
		
		$('#clearUni1button').button();
		//this line below creates the first entry in the uni1List with a known 
		//static value to enable clearing the dialog selectmenu and setting it 
		//to a user action prompt. This value is also checked at order processing 
		//time to ensure it was changed, otherwise an error is displayed to the 
		//user.
		uni1List = "<option value=Prompt>Please select the first endpoint.</option>";
		//Here the list of all endpoints is created from the global uniList and
		//made to be options for the select menu control.
		for (var i=0; i< uniList.length; i++) {
			uni1List +="<option value="+uniList[i].uniServiceId+" >"+uniList[i].locationId+"("+uniList[i].serviceAddress+")</option>";
		}
		//This segment of code initalizes id=selectUni1 as a select menu, sets 
		//the innerHTML elements of it, defines the function to be run on any 
		//change events, refreshes the menu to it displays correctly.
		$('#selectUni1')
				.selectmenu()
				.html(uni1List)
				.selectmenu('option', 'width', 800)
				.selectmenu({ 
					change: function(event, ui){uni1changeEventFunction(event, ui) }
				})
				.selectmenu('refresh');
		//this call sets up the event listener and defines the function to run
		$('#selectUni1').on("selectmenuchange", uni1changeEventFunction());
		
		//create the selectmenu for the celan as well.
		$('#selectUni1Celan')	
				.selectmenu()
				.html('Loading...')
				.selectmenu('option', 'width', 200);
	
		//create elements for UNI2 but do not populate the list for selection at this time. The list will end up being the same list as UNI1 but with the UNI1 item removed (we are not allowing same UNI to UNI connections).
		$('#selectUni2')
				.selectmenu()
				.selectmenu('option', 'width', 850)
				.selectmenu({ //might be needed, might not
					change: function(event, ui){ uni2changeEventFunction(event, ui) }
				})
				.selectmenu('refresh');
		$('#selectUni2').on("selectmenuchange", uni2changeEventFunction());
		
		$('#selectSpeed')
				.selectmenu()
				.selectmenu('option', 'width', 150);
			
		handleErrors(''); //causes the error box at the top of the dialog to not be visible.
		//console.log('createDialogBox funtion complete');
	}
	
/* @function orderEvent
 * Function was originally meant to handle the event that would indicate that 
 * some change to an order - be that a start or addition of an endpoint was 
 * occuring. This has changed a little, but this is still used. 
 * @param {Response} jsonResponseUni jQuery response for a UNI query
 */		
	function orderEvent(jsonResponseUni){
		//console.log("orderEvent occured.");
		//The orderProcessFlag is there to say if an order is starting 
		//(i.e. UNI1 needs to be or is being selected or is an order is 
		//continuing. This is handy to allow the closing of the dialog box 
		//without losing the order entries.
		if (orderProcessFlag === false) { //order brand new
			//console.log("orderProcessFlag === false");
			orderProcessFlag = true;
			//console.log('locationId: ' + jsonResponseUni.locationId);
			//select the UNI based on the map click
			$('#selectUni1').val(jsonResponseUni.uniServiceId);
			$('#selectUni1').selectmenu('refresh'); //has to be updated or the 
			//select wont appear to have worked.
			//generate fake event to have VLANs entry populated.
			uni1changeEventFunction('fakeevent', {item:{value:jsonResponseUni.uniServiceId}});
			//open the dialog box
			$('#orderBox').dialog("open");
			//mark that UNI1 has been entered, so the next entry would be UNI2
			uniPlacementNumber = 2;
		}
		//if the order is in progress, do this instead
		else if (orderProcessFlag === true){
			//console.log("orderProcessFlag === true");
			$('#selectUni2').val(jsonResponseUni.uniServiceId); //This sets the value of the selectmenu so that either a direct mouse selection or a click on the map will work.
			$('#selectUni2').selectmenu('refresh');
			$("#orderBox").dialog("open");
			//console.log('opening exisiting orderBox dialog');
		}
		else { //catch all if Flag is not true or false
			console.log("orderProcessFlag is neither true or false!");
		}
	}

/* @function uni1changeEventFunction
 * Function is run when a change event occurs on the selectUni1 selectmenu.
 * @author: Mr. Dan Burnham, Mr. David J. Stern  
 * @param {Event} event 
 * @param ui {obj} User Interface Object
 */		
	function uni1changeEventFunction(event, ui){
		//this event is/can be fired as part of the menu creation/population process. This catches that case to prevent an browser error from coming to the user.
		if (event === undefined){
			return;
		}
		if (ui === undefined){
			return;
		}
		//console.log('uni1changeEventFunction fired');
		
		//ui.item.value contains the uniServiceId
		//display the uniServiceId passed.
		//console.log('ui.item.value: ' + ui.item.value); 
		//clear the uni1VLANList variable. This is done each time to ensure the 
		//list doesnt have duplicate entries.
		uni1VLANList ='';
		
		//iterate through the uniList to matchup with the one of interest and 
		//then use that data to create the vlan selectmenu list.
		for (var i=0; i<uniList.length; i++){
			//console.log("inside (i=0; i<unilist.length; i++)"); 
			if (ui.item.value === uniList[i].uniServiceId){ //maps the event ui 
			//object entry with the uniServiceId
				//TODO: update to use API changes for vlan avail.
				//console.log('vlans used are: '+uniList[i].ceVlansInUse);  
				var ceLans = uniList[i].ceVlansInUse.toString();
				
				var dflag = false;
				var d = 200;
				while (dflag==false){
					if (checkCELAN(d,ceLans.split(","))) { dflag=true; }
					else d = d + 1;
				}
				
				uni1VLANList="";
				for (var j=1; j<1024; j++){
					if (checkCELAN(j,ceLans.split(","))==true) {
						uni1VLANList += "<option value=" + j + ">" + j + "</option>"; }
				}
				$('#selectUni1Celan').html(uni1VLANList);
				$('#selectUni1Celan').val(d);
				$('#selectUni1Celan').selectmenu('enable');
				$('#selectUni1Celan').selectmenu('refresh');
				
				//TODO: Implement the VLAN population in a seperate function and 
				//let it return so that this loop only has to run through the 
				//list until it has found the needed vlaue rather than going 
				//through the whole thing. Can't put a return here as-is because 
				//it prevents needed code from running.
			}
		}
		
		//now create the list of entries for UNI2 excluding the one selected for UNI1.
		//clear the existing uni2List variable so we dont get repeated entries.
		uni2List='<option value="Prompt">Please select the second endpoint.</option>'; 
		for (i=0; i< uniList.length; i++){
			//console.log('i value is: ' + i); 
			if (ui.item.value === uniList[i].uniServiceId){ //catch the case when we have UNI1
				//console.log('uni1 entry caught, not put in list');
			}
			else {
				uni2List +="<option value="+uniList[i].uniServiceId+" >"+uniList[i].locationId+"("+uniList[i].serviceAddress+")</option>";
			}
		}
		//now put entries into the selectmenu for UNI2
		$('#selectUni2').html(uni2List);
		$('#selectUni2').selectmenu('enable');
		$('#selectUni2').selectmenu('refresh');
		$('#selectSpeed').selectmenu('enable');
		
		//since a UNI1 was selected, make sure the orderProcess is marked as 
		//started.
		orderProcessFlag = true;
		//set cartEmpty to false so the cart can be reopened using the icon 
		//without clearing.
		cartEmpty = false;
		//TODO - There should be one entry location for the 'empty' version and 
		//one for the 'in progress' version. Need to fix.
		customcartControl.changeContent('<button type="button" class="btn btn-default custom-cart-button">'+
					'<i class="fa fa-comment fa-lg" aria-hidden="true"></i>'+
					'</button>');
	}

/* @function checkCELAN
 * Function checks if the vlan is available, returns true if available.
 * @author Mr. David J. Stern
 * @param {int} number Number of the vlan being checked
 * @param {int[]} arrCELANS Array of vlans to check within
 * @return {boolean} returns false if number is in the arrCELANS array, true otherwise
 */		
	function checkCELAN(number,arrCELANS){
		for (var i = 0, len = arrCELANS.length; i<len; i++) {
			if (arrCELANS[i]==number){return false;}
		}
		return true;
	}

/* @function uni2changeEventFunction
 * Function called at each selectUni2 change event. 
 * @author: Mr. Dan Burnham 
 * @param {Event} event 
 * @param {obj} ui object
 */		
	function uni2changeEventFunction(event, ui){
	//console.log('uni2changeEventFunction entered.');
	}

/* @function orderSubmitPressed
 * Function called when the submit order button on the dialog box is clicked. 
 * This function first runs through some checks to make sure that there is a 
 * UNI1 selected and a UNI2 selected and if they are not to bring up the error 
 * div in the dialog box and return, thus NOT completing the order call.
 * @author: Mr. Dan Burnham, Mr. David Stern  
 * (TODO- these will need to be expanded)  
 */	
	function orderSubmitPressed(){
		//adding in some checks before processing the order
		var errorobjectlist=[];
		var erroroccured = false;
		if (document.getElementById('selectUni1').value === 'Prompt') {
			//console.log('UNI1 not selected.');
			errorobjectlist.push({error:'UNI1 not selected. Please select a UNI1.'});
			erroroccured = true;
		}
		//this means the second uni was not selected
		if (document.getElementById('selectUni2').value === 'Prompt') { 
			//console.log('UNI2 not selected.');
			errorobjectlist.push({error:'UNI2 not selected. Please select a UNI2.'});
			erroroccured = true;
		}
		if (provisioningError === true){
			console.log('Provisioning error occured.');
			errorobjectlist.push({error:'Provisioning error occured. Please try another endpoint/carrier.'});
			erroroccured = true;
			provisioningError = false; //reset the error, as this one has to be manually done
		}
		if (erroroccured === true){ //process error routine and return
			handleErrors(errorobjectlist);
			return;
		}
	
		//change the custom control to be a spinner
		customcartControl.changeContent('<button type="button" class="btn btn-primary custom-cart-button">'+
					'<i class="fa fa-spinner fa-pulse fa-fw fa-lg" aria-hidden="true"></i>'+
					'</button>');
		//Start Pending Line		
		placeBlinkyLines(document.getElementById('selectUni1').value,document.getElementById('selectUni2').value);	

		//Do the provisioning	
		fireAway();
		$( "#orderBox" ).dialog("close");
		//change the order button in the box to "Processing..." and when it is clicked it just adds a console log entry.
		$("#orderBox").dialog("option","buttons",[ { text: "Processing...", click: function(){ 
			//console.log("Processing... button clicked")
			} } ] );
		handleErrors(''); //clear any existing errors
		//console.log('orderBox cleared');
	}

/* @function fireAway
 * Function is a AJAX call to a carrier to initiate a connection 
 * author: Mr. David Stern
 * TODO: Do you want to make the local address more generic to more than just local?
 */	 	
	function fireAway(){
		var options;
		options = "uni1="+document.getElementById('selectUni1').value+
			"&celan1="+document.getElementById('selectUni1Celan').value+
			"&uni2="+document.getElementById('selectUni2').value+
			"&speed="+document.getElementById('selectSpeed').value;
		//console.log('escape(options): '+escape(options));
		$.get(webServerSchemeAuthority+"/www/b_p_c_s_provision.py",escape(options), processOrder, "text")
			.done(function() {
				console.log('$.get("./b_p_c_s_provision.py", escape(options), processOrder) success.');
			})
			.fail(function( jqXHR, textStatus, errorThrown){
				console.log('$.getJSON("./b_p_c_s_provision", escape(options), processOrder) failed: ' + textStatus + ' : ' + errorThrown);
			});
	}

//TODO: Need to add function that runs regardless of success or failure of the 
//.get that will get an updated list of the endpoints and the vlans they are 
//using to update the selections.
		
/* @function processOrder
 * Function processes the jQuery response
 * @author Mr. David Stern
 * @param {Response} response jQuery Response
 * @param status ?? //NOT USED //TODO: clean these up
 * @param xhr ??   //NOT USED
 */	
	function processOrder(response,status,xhr){
		//change color and add data from pending line  --refresh page!	
		//alert (response.match('{PROVsuccess:true}')); //Kept for Debugging
		//TODO: this was done to handle the case where we are using STDOUT TEE
		//in the CGI/Python interface that shows the entire action to the
		//browser in near real time.
		if (response.match('{PROVsuccess:true}')){ 
			//alert ("Connection Successful! Refreshing Page with New Connection Details"); 
			window.location.reload();
			
			//first change the order icon
			customcartControl.changeContent('<button type="button" class="btn btn-success custom-cart-button">'+
					'<i class="fa fa-check fa-lg" aria-hidden="true"></i>'+
					'</button>');
			window.clearInterval(anim1);
			window.clearInterval(anim2); 
			//clean up && clear the dialog box
			$('#selectSpeed').val("10000000");
			$('#selectSpeed').selectmenu('refresh');
			clearUni1();
			handleErrors(''); //clear any existing errors
			//console.log('orderBox cleared');
			//next fire off the get connections, which really means fire off
			//to get end points
			getAWSendpoints(); //TODO: generalize this function name.
			getMdEndpoint(); //TODO: generalize this function name.
			}
		else{
			//alert ("Connection Was Not Successful"); 
			//this turns the spinner dialog to a red box with a white X in it to indicate a failure.
			customcartControl.changeContent('<button type="button" class="btn btn-danger custom-cart-button">'+
					'<i class="fa fa-times fa-lg" aria-hidden="true"></i>'+
					'</button>');
			//TODO: add red line and details
			window.clearInterval(anim1); 
			window.clearInterval(anim2);
			$("#orderBox").dialog("option","buttons",[ { text: "Submit Order", click: function(){ orderSubmitPressed()} } ] );
			//TODO - an order error flag or state or something
			provisioningError = true;
			orderSubmitPressed(); //just to pass the error to the error routine 
			//in this function
		}
	}

/* @function OrderListBy
 * Function is a sort helper function used for the putting the endpoints in 
 * alphabetical order.
 * @author Mr. Dan Burnham
 * @param {str} prop first string to sort by
 * @param {str} prop2 second string to sort by 
 */		
	function OrderListBy(prop,prop2){
		return function (a,b){
			if (a[prop] > b[prop]) {
				return 1;
			}
			else if (a[prop] < b[prop]) {
				return -1;
			}
			else if ((a[prop] === b[prop]) && (a[prop2] > b[prop2])){
				return 1;
			}
			else if ((a[prop] === b[prop]) && (a[prop2] < b[prop2])){
				return -1;
			}
			//console.log('OrderListBy returning 0'); //Kept for Debugging
			return 0;
		};		
	}

/* @function endprocessEndpoints
 * Function is an event handler function that initially updated the total 
 * available bandwidth display but now also sorts the list of UNIs. Also now 
 * recreates the uni1List from the newly alphabetical list.
 * @author Mr. Dan Burnham 
 * @param {Event} e Event
 */	 
	function endprocessEndpoints(e){
		if (processEndPointdone === true){
			//console.log('processEndPoints and processEndPoint done');
			availablebandwidthDisplay.update([awstotalavailablebandwidth, mstotalavailablebandwidth]);
			uniList.sort(OrderListBy('locationId','uniServiceId'));
			repopulateuni1List();
			processEndPointdone = false;
			processEndPointsdone = false;
		}
		else {
			//console.log('processEndPoints done but processEndPoint not yet done');
		}
	}

/*@function endprocessEndpoint
 * Function is an event handler function that is a clone of 
 * endprocessEndpoints because needed to handle the case where one could finish 
 * before the other. Still a bit hacky. 
 * @author Mr. Dan Burnham 
 * //TODO: Consolidate with endprocessEndpoints this was first
 * @param {Event} e Event
 */	
	function endprocessEndpoint(e){
		if (processEndPointsdone === true){
			console.log('processEndPoint and processEndPoints done');
			availablebandwidthDisplay.update([awstotalavailablebandwidth, mstotalavailablebandwidth]);
			uniList.sort(OrderListBy('locationId','uniServiceId'));
			repopulateuni1List();
			processEndPointdone = false;
			processEndPointsdone = false;
		}
		else {
			console.log('procesEndPoint done but processEndPoints not yet done');
		}
	}
	
/* @function handleErrors
 * Function used to deal with the errors and display them. 
 * @reference the book jQuery UI in action
 * @author Mr. Dan Burnham 
 * @param {Object[]}errorList List of error objects
 */
	function handleErrors(errorlist) {
		var container = $( ".ui-state-error" ).hide(),
			list = container.find( "ul" ).empty();
		if (errorlist.length === 0) {
			return;
		}
		
		$.each( errorlist, function ( index, erroritem){
			list.append( "<li>" + erroritem.error + "</li>" );
		});
		container.show ("shake", {times: 2}, 100 );
	}		
	
/* @function clearUni1
 * Function is the cleanup function.
 * 1) cartEmpty is set to true, to indicate no order in progress
 * 2) selectUni1 is set to the Prompt value and refreshed
 * 3) selectUni2 is set to a Prompt value, set to disabled, and refreshed. If no
 *    uni1 is selected then no UNI2 should be selectable.
 * 4) selectUni1Celan is emptied of its contents, set to disabled, and refreshed.
 * 5) selectSpeed is set to disabled.
 * 6) the orderProcessFlag is set to show no order in progress
 * 7) the customcartControl is updated to show no current order in progress
 * @author Mr. Dan Burnham 
 */
	function clearUni1(){
		//simple function to clear the selection of UNI1 so a new one can be selected.
		cartEmpty = true;
		$('#selectUni1').val("Prompt");
		$('#selectUni1').selectmenu('refresh');
		$('#selectUni2').html('<option value="Prompt" selected>Please select a first endpoint before selecting a second endpoint.</option>');
		$('#selectUni2').selectmenu('disable');
		$('#selectUni2').selectmenu('refresh');
		$('#selectUni1Celan').empty();
		$('#selectUni1Celan').selectmenu("disable");
		$('#selectUni1Celan').selectmenu('refresh');
		$('#selectSpeed').selectmenu('disable');
		orderProcessFlag = false;
		customcartControl.changeContent('<button type="button" class="btn btn-default custom-cart-button">'+
					'<i class="fa fa-comment-o fa-lg" aria-hidden="true"></i>'+
					'</button>');
		//console.log('clearUni1 function exit');
	}

/* customcartControl
 * Handle creates the custom control for the item to being up the dialog box / shopping cart.
 * @author Mr. Dan Burnham 
 */	
	var customcartControl = L.control.custom({
		forceSeparateButton: false,
		position: 'topright',
		content: '<button type="button" class="btn btn-default custom-cart-button">'+
					'<i class="fa fa-comment-o fa-lg" aria-hidden="true"></i>'+
					'</button>', 
					//the btn and btn-default classes are bootstrap css classes. The custom-cart-button is mine but not used.
					//the fa fa-comment-o is refering to the awesome font that is a small dialog box.
		classes: 'btn-group-vertical btn-group-sm',
		style   :
                {
                    margin: '10px',
                    padding: '0px 0 0 0',
                    cursor: 'pointer'
                },
                datas   :
                {
                    'foo': 'bar',
                },
                events:
                {
                    click: function(data)
                    {
                        console.log('wrapper div element clicked');
                        console.log(data);
						if(cartEmpty === true){ 
							clearUni1(); //if cart is empty, make sure of it.
							$("#orderBox").dialog("open");
						}
						else{
							$("#orderBox").dialog("open");
						}
						
                    },
                    dblclick: function(data) //not used but kept
                    {
                        //console.log('wrapper div element dblclicked');
                        //console.log(data);
                    },
                    contextmenu: function(data) //not used but kept.
                    {
                        //console.log('wrapper div element contextmenu');
                        //console.log(data);
                    },
                }
    });
			
    customcartControl.addTo(mymap);	//adds control to the map.

/* @function repopulateuni1List
 * Function repopulates the User Network Interfaces List.
 * @author Mr. Dan Burnham  
 */	
	function repopulateuni1List(){
		uni1List = "<option value=Prompt>Please select the first endpoint.</option>";
		//Here the list of all endpoints is created from the global uniList and made to be options for the select menu control.
		for (var i=0; i< uniList.length; i++) {
			uni1List +="<option value="+uniList[i].uniServiceId+" >"+uniList[i].locationId+"("+uniList[i].serviceAddress+")</option>";
		}
		$('#selectUni1').html(uni1List);
		$('#selectUni1').selectmenu("refresh");
	}
	
	//this waits for the document to be ready before calling the 
	//createDialogBox, which is important otherwise it will not be created 
	//correctly.
	$( document ).ready( createDialogBox );
	runstuff(); //end of script call to run a few things after the other calls complete
