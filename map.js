/*
 * Turns this data into GeoJSON.
 *
 * Get dependencies:
 *
 * npm install csv turf
 * wget -O coast.geojson https://raw.githubusercontent.com/glynnbird/countriesgeojson/master/united%20states%20of%20america.geojson
 *
 */

var fs = require('fs');
var csv = require('csv');
var turf = require('turf');

function main() {
	// Read from the CSV file.
	var file = fs.createReadStream("hardiness_zones.csv");

	// Stream the file into a CSV parser that will create
	// a turf FeatureCollection.
	var parser = csv.parse();
	setup_parser(parser, processor);
	file.on('data', function(data) {
		parser.write(data);
	});
	file.on('end', function(data) {
		parser.end();
	});
}

function setup_parser(parser, callback) {
	// Set up the CSV parser using the streaming API and
	// create turf points from the rows.
	var headers = null;
	var points = [];
	parser.on('readable', function() {
	  while(record = parser.read()) {
	  	// If this is the first row, it's the header row.
	  	if (!headers) {
	  		headers = record;
	  		continue;
	  	}

	  	// Turn the array into an Object by matching up
	  	// cells with the header row.
	  	var rec = { };
	  	for (var i = 0; i < headers.length; i++)
	  		rec[headers[i]] = record[i];

	  	// Skip non-continental-US states because they confuse the
	  	// isolines/isobands algorithm.
	  	if (['AK', 'HI', 'PR'].indexOf(rec.state) >= 0)
	  		continue;

	  	// Create a turf.js Point.
	  	var p = turf.point([parseFloat(rec['longitude']), parseFloat(rec['latitude'])], rec);
	   	points.push(p);
	  }
	});
	parser.on('error', function(err) {
	  console.log(err.message);
	});
	parser.on('finish', function(err) {
	  var fc = turf.featurecollection(points);
	  callback(fc);
	});
}

function processor(fc) {
	// Takes a feature collection and generates isobands.

	// The 'zones' are strings like 12a. We need to assign them
	// some logical order. Zones always end with a letter.
	var zones = { };
	fc.features.forEach(function(item) {
		zones[item.properties.zone] = true;
	});
	zones = Object.keys(zones);
	zones.sort(function(a, b) {
		var a1 = parseInt(a.substring(0, a.length-1));
		var a2 = a.substring(a.length-1);
		var b1 = parseInt(b.substring(0, b.length-1));
		var b2 = b.substring(b.length-1);
		if (a1 < b1)
			return -1;
		else if (a1 > b1)
			return 1;
		else
			return a2.localeCompare(b2);
	});

	// Add z values into the points based on the zone order.
	fc.features.forEach(function(item) {
		item.properties.z = zones.indexOf(item.properties.zone);
	});

	// Simplify the map because it will be just a bit too slow to display
	// in real time if we use all source data.
	fc = turf.sample(fc, 7500);

	// Create contour plot.
	var map = turf.tin(fc, 'z');

	// Bound by the coast -- this part is slow.
	var coast = JSON.parse(fs.readFileSync('coast.geojson'));
	map.features = map.features.map(function(item) {
		var fnew = turf.intersect(item, coast);
		if (fnew) // may be null if no intersection
			fnew.properties = item.properties; // restore
		return fnew;
	});
	map.features = map.features.filter(function(item) { return item != null });

	// Write out.
	fs.writeFileSync('map.geojson', JSON.stringify(map, null, '  '));
}

main();
