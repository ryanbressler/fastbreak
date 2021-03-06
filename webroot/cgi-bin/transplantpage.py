#!/usr/bin/python
import os, glob
import cgi
import cgitb
cgitb.enable()
from config import *


vars={'checkboxes':"",'transplantws':transplantws,'survivaldatasource':survivaldatasource,'genedatasource':genedatasource,"jsdir":jsdir,"loadergif":loadergif}
files=[]
#for infile in glob.glob(os.path.join(os.getcwd(),'../data/*out')):
for infile in glob.glob(datapath+'*out.pickle'):
	basename = os.path.basename(infile);	
	files.append(basename)

vars["files"]="['"+"','".join(files)+"']"

print "Content-type: text/html"
print
print """<?xml version="1.0" ?>

<html xmlns="http://www.w3.org/1999/xhtml" 

                 xmlns:svg="http://www.w3.org/2000/svg"

     xmlns:xlink="http://www.w3.org/1999/xlink"

     lang="en-US">
<head>
<meta http-equiv='Content-Type' content='text/html; charset=utf-8' />

<title>Transplant</title>

<style>
body { 
font: 8pt helvetica neue;
color: #666;
}
td { 
font: 8pt helvetica neue;
color: #666;
}
input {
font: 8pt helvetica neue;


}
.outlined {
	color: #666;
	border-color: #F5F5F5;
	border-width: 2px 2px 2px 2px;
	border-style: solid;
	border-spacing: 0px;
	
	}

</style>
	
<script type='text/javascript' src='http://www.google.com/jsapi'></script>
<script type='text/javascript'>
  google.load('visualization', '1', {packages:["table"]});
  //google.load('prototype', '1.6');
</script>
<script type='text/javascript' src='%(jsdir)stransplant.js'></script>

<script type='text/javascript' >


filenames = %(files)s;
transplantws = "%(transplantws)s";
survivaldatasource = "%(survivaldatasource)s";
genedatasource = "%(genedatasource)s";
loadingpatientinfo = true;
patients = {};
sampletypes = {};
progstyle ={"Poor":"border-color: #F5B9B9;","Good":"border-color: #B9F5B9;","Medium":"border-color: #F5F5B9;"};
samplelabels = {"10":"Blood","11":"Adjacent","01":"Tumor"};
ajloader = "%(loadergif)s"

patientrequested = {} 
patientcount = 0;
patientloadedcount =0;

function onpageload()
{
	genelocready = false;
	filenamesready = false;
	
	
	
	//Get gene location
	var gene_symbol = getQueryVariable("genes")[0].split("/").pop();
	var querystring = "select gene_symbol, chromosome, start, end where gene_symbol = '"+gene_symbol+"'";
	this.log("loading: " + querystring +" from " + genedatasource);
	var query = new google.visualization.Query(genedatasource);
	query.setQuery(querystring);	
	query.send(savegeneloc);
	
	var utlpats = getQueryVariable("patients");
	
	patientrequested = {}
	for (var i in utlpats)
	{
		var pat = utlpats[i].split("/").pop()
		log("pat " + pat + " from " + utlpats[i]);
		patientrequested[pat]=true;
	}
	
	//getfilenames
	/*filenames = [];
	
	var utlpats = getQueryVariable("patients");
	patientcount = utlpats.length;
	patientloadedcount =0;
	
	for (var i in utlpats)
	{
		var req = new XMLHttpRequest();
		var patientindex = fileindex+utlpats[i]+"/Pickle";
		req.open("GET", patientindex, true);
		req.onreadystatechange = function (){
			if (req.readyState == 4 ) {
				var files = eval('(' + req.responseText + ')').references;
				for (var j in files)
				{
					log("adding file name"+files[j].local);
					filenames.push(files[j].local);
				}
				patientloadedcount++;
				grow();
			}
		};
		req.send(null);
	}*/
}

function savegeneloc(response)
{
	log("gene location data recieved");
	if (response.isError()) {
    	log('Error in query: ' + response.getMessage() + ' ' + response.getDetailedMessage());
    	return;
  	}
  	var data = response.getDataTable();
  	var radius = parseInt(document.getElementById('radius').value);
	document.getElementById('chr').value = data.getValue(0,1);
	document.getElementById('start').value = data.getValue(0,2)-radius;
	document.getElementById('end').value = data.getValue(0,3)+radius;
	genelocready = true;
	grow();
}



function grow()
{
	//if(!(genelocready && filenamesready) && ( patientcount == patientloadedcount ))
	//	return;
		
	loadingpatientinfo = true;
	document.getElementById('visdiv').innerHTML="<center><img src='"+ajloader+"'/><br/>Loading Patient Data...<\/center>";
	loadthese=[];
	drawthese=[];

	patients = {}
	sampletypes = {"10":true,"11":true,"01":true};
	
	
	
	for (var i in filenames)
	{
		var filename = filenames[i].split("/").pop();
		var patientid = filename.substring(0,12)
		if(patientrequested[patientid])
		{
			
			loadthese.push(filename);
			
			var sampletype = filename.substring(13,15)
			log("patient '" + patientid + "' sampletype '" + sampletype + "'")
			
			if(!patients.hasOwnProperty(patientid))
			{
				patients[patientid] = {samples:{}}
			}
			if(!patients[patientid].samples.hasOwnProperty(sampletype))
			{
				patients[patientid].samples[sampletype]=[];
			}
			patients[patientid].samples[sampletype].push(filename);
			
			
			sampletypes[sampletype] = true
		}
	}
	
	if(loadthese.length == 0)
	{
		document.getElementById('visdiv').innerHTML="<center>No Data to Load.<\/center>";
		return;
	}
	loadAll();
	
	log("building survival query");
	var orarray = []
	for (var patient in patients)
	{
		orarray.push("(patient_id = '"+patient+"')");
	}
	
	var patientquery = "select * where " + orarray.join(" or ") + "order by `label` desc, time_years asc";
	
	var query = new google.visualization.Query(survivaldatasource);
	query.setQuery(patientquery);
	
	log("sending query " + patientquery + " to " + survivaldatasource);
	query.send(handleSurvivalResponse);
	
	
	
			
}





google.setOnLoadCallback(onpageload);


</script>
<script type='text/javascript' src='%(jsdir)stransplantpage.js' ></script>
<style>
body { margin: 30px; text-align: left; white-space: nowrap;}

</style>

</head>

<body>
<div id="visdiv" style="white-space: nowrap;"><center><img src='../ajax-loader.gif'/><br/>Loading gene and file data...</center></div>
<br/>
<div>
<form>
<!--Data Files:<br/>
<input type="checkbox" id="checkallb" onchange = "script:checkallf();" /> Check All
<div style="width:95%%;height:300;overflow:auto;border:2px grey solid;">
%(checkboxes)s
</div>-->
<center>
<table>
<tr>
<td>
Root Location:<br/><br/>
Chromosome:<input type='text' id="chr" />&nbsp;&nbsp;
Start:<input type='text' id="start" />&nbsp;&nbsp;
End:<input type='text' id="end" />
</td>
<td>
&nbsp;&nbsp;&nbsp;&nbsp;
</td>
<td>
Tree Parameters:<br/><br/>
Maximum Branch Depth:<input type='text' id="depth" value="2"/>&nbsp;&nbsp;
Search Radius:<input type='text' id="radius" value="400000"/>
</td>
</tr>
</table>
<br/><br/>
<input type="button" value="Regrow Transplants" onclick="script:grow();"/>
</center>
</form>
</div>


</body>
</html>"""%vars