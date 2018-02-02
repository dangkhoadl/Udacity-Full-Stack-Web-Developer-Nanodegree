

/*-------------------------------------- Global variables ----------------------------------*/
var map;
var markers = [];
var largeInfowindow;

/*-------------------------------------- Functions ----------------------------------*/
// Initialize Map
function initMap() {
	// Constructor creates a new map - only center and zoom are required.
	map = new google.maps.Map(document.getElementById('googleMap'), {
		center: {lat: 10.800744, lng: 106.665262},
		zoom: 14,
		styles: styles,
		mapTypeControl: false,
		disableDefaultUI: true
	});

	// Create an info window
	largeInfowindow = new google.maps.InfoWindow();

	// Style the markers a bit. This will be our listing marker icon
	var defaultIcon = makeMarkerIcon('0091ff');
	function setDefaultIcon() {
		this.setIcon(defaultIcon);
	}

	// Create a "highlighted location" maker color for when the user mose over the marker
	var highlightedIcon = makeMarkerIcon('ffff24');
	function setHighlightedIcon() {
		this.setIcon(highlightedIcon);
	}

	// maker click handler
	function passClickToKnockOut() {
		window.vm.goToMarker(this);
	}

	// The following group uses the location array to create an array of markers on initialize.
	for (var i = 0; i < locations.length; ++i) {
		// Get the position from the location array.
		var position = locations[i].location;
		var title = locations[i].title;
		var id = locations[i].id;

		// Create a marker per location, and put into markers array.
		var marker = new google.maps.Marker({
			title: title,
			map: map,
			position: position,
			icon: defaultIcon,
			animation: google.maps.Animation.DROP,
			id: id
		});

		// Push the marker to our array of markers.
		markers.push(marker);
		/*----------------------------------------------- Event Listeners ----------------------------------------------------------- */

		// Create an onclick event to open an infowindow at each marker.
		marker.addListener('click', passClickToKnockOut);

		// Event: mouseover
		marker.addListener('mouseover', setHighlightedIcon);

		// Event mouseout
		marker.addListener('mouseout', setDefaultIcon);
	}
}


/* ----------------------------- Marker API -------------------------------------------*/
// Set/Clear markers
function clearMarker(location) {
	if(location.isSet === true) {
		markers[location.id].setMap(null);
		location.isSet = false;
	}
}

function setMarker(location) {
	if(location.isSet === false) {
		markers[location.id].setMap(map);
		location.isSet = true;
	}
}

/// This function takes in a COLOR, and then creates a new marker
// icon of that color. The icon will be 21 px wide by 34 high, have an origin
// of 0, 0 and be anchored at 10, 34).
function makeMarkerIcon(markerColor) {
	var markerImage = new google.maps.MarkerImage(
		'http://chart.googleapis.com/chart?chst=d_map_spin&chld=1.15|0|'+ markerColor +
		'|40|_|%E2%80%A2',
		new google.maps.Size(21, 34),
		new google.maps.Point(0, 0),
		new google.maps.Point(10, 34),
		new google.maps.Size(21,34));
	return markerImage;
}

// This function populates the infowindow when the marker is clicked. We'll only allow
// one infowindow which will open at the marker that is clicked, and populate based
// on that markers position.
function populateInfoWindow(marker, infowindow) {
	// Check to make sure the infowindow is not already opened on this marker.
	if (infowindow.marker != marker) {
		// Clear the infowindow content to give the streetview time to load.
		infowindow.setContent('');
		infowindow.marker = marker;

		// Make sure the marker property is cleared if the infowindow is closed.
		infowindow.addListener('closeclick', function() {
			infowindow.marker = null;

			// Update view model
			vm.goToPlace(null);

			// Remove marker animation
			markers.forEach(function(marker) {
				marker.setAnimation(null);
			});
		});

		// Get Google street view Images
		var streetViewURL = 'http://maps.googleapis.com/maps/api/streetview?size=200x200&location=';
		var streetViewLocation = marker.getPosition().lat() + ',' + marker.getPosition().lng();
		var streetViewImgConfig = '&fov=90&heading=235&pitch=10';

		// Update display info
		infowindow.setContent(
			// Title
			'<div><strong>' + locations[marker.id].title + '</strong></div>' +

			// streetAddress
			'<div>' + locations[marker.id].streetAddress + '</div>' +

			// cityAddress
			'<div>' + locations[marker.id].cityAddress + '</div>' +

			// website URL
			'<div><a href="http://' + locations[marker.id].websiteURL + '">' + locations[marker.id].websiteURL + '</a></div>' +

			// Google street view Image
			'<img src="' +
			streetViewURL + streetViewLocation + streetViewImgConfig +
			'">'
		);

		// Open the infowindow on the correct marker.
		map.panTo(marker.position);
		infowindow.open(map, marker);

		// Bouncing animation
		markers.forEach(function(marker) {
			marker.setAnimation(null);
		});
		marker.setAnimation(google.maps.Animation.BOUNCE);
	}
}

/* ----------------------------- Map Error Handler -------------------------------------------*/
function mapError() {
	alert('The image could not be loaded.');
}

/* ----------------------------- List-filter -------------------------------------------*/
function ViewModel() {
	var self = this;

	self.places = ko.observableArray(locations);

	self.wikiHeader = ko.observable('');
	self.showWikiArticles = ko.observable(false);
	self.wikiArticles = ko.observableArray([]);

	self.filter = ko.observable('');
	self.showFilterList = ko.observable(false);

	// filter-list handler
	self.filteredList = ko.computed(function() {
		var query = self.filter().toLowerCase();
		return ko.utils.arrayFilter(self.places(), function(location) {
			if(location.title.toLowerCase().indexOf(query) >= 0) {
				setMarker(location);
			}
			else {
				clearMarker(location);
			}
			return location.title.toLowerCase().indexOf(query) >= 0;
		});
	});

	// Wikipedia handler
	self.selectedPlace = ko.observable(null);
	self.selectedPlace.subscribe(function(place) {
		// hide location list
		self.showFilterList(false);
		self.showWikiArticles(false);

		if (place === null) return;

		var marker = markers[place.id];

		populateInfoWindow(marker, largeInfowindow);

		// Update wikipedia API
		getWikiArticles(marker.title, function(header, result) {
			self.showWikiArticles(true);
			self.wikiHeader(header);
			self.wikiArticles(result);
		});
	});

	self.goToPlace = function(place) {
		self.selectedPlace(place);
	};

	self.goToMarker = function(marker) {
		var place = locations.find(function(x) {
			return x.id == marker.id;
		});
		self.selectedPlace(place);
	};
}

window.vm = new ViewModel();
ko.applyBindings(window.vm);


/* ----------------------------- Wikipedia - API -------------------------------------------*/
function getWikiArticles(title, callback) {
	title = encodeURIComponent(title);

	$.ajax({
		url: 'http://en.wikipedia.org/w/api.php?action=opensearch&search=' + title + '&format=json',
		dataType: 'jsonp',
		success: function(response) {
			var terms = response[1];
			var header = "";
			if(terms.length === 0) {
				header = "No Relevant articles were found";
			}
			else {
				header = "Relevant Wikipedia Articles";
			}
			var articleList = terms.map(function(term) {
				return {
					url: 'http://en.wikipedia.org/wiki/' + encodeURIComponent(term),
					title: term
				};
			});
			callback(header, articleList);
		},
		error: function(e) {
			alert("Failed to get Wikipedia articles");
			var header = "Failed to get Wikipedia articles";
			var articleList = [];
			callback(header, articleList);
		}
	});
}
