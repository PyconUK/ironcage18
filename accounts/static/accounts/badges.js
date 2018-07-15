$(document).ready(function() {
	var badgeSvg, name, company, twitter, pronoun;
	$("#badge").on('load', function() {
	 	badgeSvg = document.getElementById("badge").contentDocument;


		if (ticketCompany != "") {
			$('#id_badge_company')[0].value = ticketCompany;
			$('#id_badge_company')[0].disabled = true;
		}

		name = $('#id_name')[0].value;
		company = $('#id_badge_company')[0].value;
		pronoun = $('#id_badge_pronoun')[0].value;
		twitter = $('#id_badge_twitter')[0].value;

		if(isOrganiser) {
			badgeSvg.getElementById("background").className.baseVal = "red";
		} else if(isContributor) {
			badgeSvg.getElementById("background").className.baseVal = "blue";
		}

		updateBadge();

		// badgeSvg.getElementById("snake-snake").setAttributeNS('http://www.w3.org/1999/xlink', 'xlink:href', "/static/accounts/snakes/bluesnakewithhat.svg");
	});

	$("#id_name").on('change', function(e) {
		name = e.target.value;
		updateBadge();
	});

	$("#id_badge_company").on('change', function(e) {
		company = e.target.value;
		updateBadge();
	});

	$("#id_badge_pronoun").on('change', function(e) {
		pronoun = e.target.value;
		updateBadge();
	});

	$("#id_badge_twitter").on('change', function(e) {
		twitter = e.target.value;
		updateBadge();
	});

	function updateBadge() {

		var extraText = "";

		if(pronoun && pronoun != "") {
			extraText = pronoun;
		}

		if(pronoun && pronoun != "" && twitter && twitter != "") {
			extraText = extraText + ' - '
		}

		if(twitter && twitter != "") {
			extraText = extraText + '@' + twitter;
		}

		badgeSvg.getElementById("name").innerHTML = name;
		badgeSvg.getElementById("company").innerHTML = company;
		badgeSvg.getElementById("extratext").innerHTML = extraText;
	}
});
