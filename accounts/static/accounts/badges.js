$(document).ready(function() {
	var badgeSvg;

	function badgeLoad() {
		badgeSvg = document.getElementById("badge").contentDocument;

	 	if(ticketRate == "corporate") {
	 		$('#id_badge_company')[0].disabled = true;
	 	}

		if(isOrganiser) {
			badgeSvg.getElementById("background").className.baseVal = "red";
		} else if(isContributor) {
			badgeSvg.getElementById("background").className.baseVal = "blue";
		}

		updateBadge();
	}

	$(window).bind("load", function() {
	 	setTimeout(badgeLoad, 250);
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

	$(".snake-body").on('click', function(e) {
		snake = e.target.dataset.id;
		$('#id_badge_snake_colour')[0].value = snake;
		updateBadge();
	})

	$(".snake-extras").on('click', function(e) {
		extras = e.target.dataset.id;
		$('#id_badge_snake_extras')[0].value = extras;
		updateBadge();
	})

	function updateBadge() {

		var extraText = "";

		if(pronoun && (pronoun != "None" && pronoun != "")) {
			extraText = pronoun;
		}

		if(pronoun && (pronoun != "None" && pronoun != "") && twitter && (twitter != "None" && twitter != "")) {
			extraText = extraText + ' - '
		}

		if(twitter && (twitter != "None" && twitter != "")) {
			extraText = extraText + '@' + twitter;
		}

		badgeSvg.getElementById("name").innerHTML = name;
		badgeSvg.getElementById("company").innerHTML = company;
		badgeSvg.getElementById("extratext").innerHTML = extraText;

		// Check length of name
		badgeSvg.getElementById("name").setAttribute('class',  'large-name')
		var name_length = badgeSvg.getElementById("name").getComputedTextLength()
		if(name_length > 95) {
			badgeSvg.getElementById("name").setAttribute('class',  'small-name')
			var name_length = badgeSvg.getElementById("name").getComputedTextLength()
			if(name_length > 95) {
				badgeSvg.getElementById("name").setAttribute('class',  'name-extras')
			}
		}

		badgeSvg.getElementById("snake-body").setAttribute('xlink:href', '#solid-snake-body')
		badgeSvg.getElementById("snake-body").setAttribute('class',  snake + '-snake snake-body')

		$('.snake-body.selected').removeClass('selected');
		$(".snake-body[data-id='" + snake + "']").addClass('selected');

		badgeSvg.getElementById("snake-back").setAttribute('xlink:href', '#' + extras + '-back')
		badgeSvg.getElementById("snake-front").setAttribute('xlink:href', '#' + extras + '-front')

		$('.snake-extras.selected').removeClass('selected');
		$(".snake-extras[data-id='" + extras + "']").addClass('selected');
	}
});
