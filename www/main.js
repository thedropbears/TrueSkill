function Donut_chart(options) {

	this.settings = $.extend({
		element: options.element,
		percent: 100
	}, options);


	this.circle = this.settings.element.find('path');
	this.settings.stroke_width = parseInt(this.circle.css('stroke-width'));
	this.radius = (parseInt(this.settings.element.css('width')) / 1.5 - this.settings.stroke_width) / 2;
	this.angle = -97.5; // Origin of the draw at the top of the circle
	this.i = Math.round(0.75 * this.settings.percent);
	this.first = true;

	this.animate = function () {
		this.timer = setInterval(this.loop.bind(this), 10);
	};

	this.loop = function (data) {
		this.angle += 5;
		this.angle %= 360;
		var radians = (this.angle / 180) * Math.PI;
		var x = this.radius + this.settings.stroke_width / 2 + Math.cos(radians) * this.radius;
		var y = this.radius + this.settings.stroke_width / 2 + Math.sin(radians) * this.radius;
		if (this.first == true) {
			var d = this.circle.attr('d') + " M " + x + " " + y;
			this.first = false;
		} else {
			var d = this.circle.attr('d') + " L " + x + " " + y;
		}
		this.circle.attr('d', d);
		this.i--;

		if (this.i <= 0) {
			clearInterval(this.timer);
		}
	}
};

function make_card(red_odds, blue_alliance, red_alliance, blue_score, red_score, match_name, match_location, ts) {
	var blue_team = "blue-team"
	var red_team = "red-team"
	var blue_odds = String(100 - red_odds) + '%'
	red_odds = String(red_odds) + "%"

	if (red_odds === "%") {
		blue_odds = "<br>"
		red_odds = "<br>"
	}

	if (blue_score === "" || red_score === "") {
		blue_score = "<br>"
		blue_score = "<br>"
	}
	else if (blue_score > red_score){
		blue_team = "blue-team-won"
	}
	else if (red_score > blue_score){
		red_team = "red-team-won"
	}


	return "<div class=\"match-card mdl-card mdl-shadow--4dp card " + ts + "\"> \
            <div class=\"mdl-card__title white-red\"> \
              <h2 class=\"mdl-card__title-text\">" + match_name + " - " + match_location + "</h2> \
            </div>\
            <div class=\"mdl-card__supporting-text team\">\
              <div class=\'" + blue_team + " " + ts + "\'>\
                <ul>\
                  <li>" + blue_odds + "</li>\
                  <li>" + blue_alliance[0] + "</li>\
                  <li>" + blue_alliance[1] + "</li>\
                  <li>" + blue_alliance[2] + "</li>\
                </ul>\
              </div>\
              <div class=\'" + red_team + " " + ts + "\'>\
                <ul>\
                  <li>" + String(red_odds) + "</li>\
                  <li>" + red_alliance[0] + "</li>\
                  <li>" + red_alliance[1] + "</li>\
                  <li>" + red_alliance[2] + "</li>\
                </ul>\
              </div>\
            </div>\
          </div>"
}

function change_card(win, ts) {
	console.log("helo")
	if (win === 'red') {
		$('.' + ts + '.red-team').removeClass('red-team').addClass("red-team-won")
	} else if (win === 'blue') {
		console.log('.' + ts + '.blue-team')
		$('.' + ts + '.blue-team').removeClass('blue-team').addClass("blue-team-won")

	}
}


var events = []
var team_events = []
var team_events_names = {}
var event_name_event = ""
var team = ''
var trueskill_score = {}
var trueskill_prediction = {}

get_trueskill()
$.ajax({
	type: "GET",
	headers: {
		"X-TBA-App-Id": "frc-4774:TrueSkill:1.0"
	},
	url: "https://www.thebluealliance.com/api/v2/events/2017",
	dataType: "json",
	success: function (result) {
		events = result
		for (event in events) {
		if (events[event].event_type  > 5){
			continue
		}

		var start_date_data = events[event].start_date
		var end_date_data = events[event].end_date;

		var start_date = Date.UTC(2017, parseInt(start_date_data.substring(5,7)-1), parseInt(start_date_data.substring(8,10)))
		var end_date = Date.UTC(2017, parseInt(end_date_data.substring(5,7)-1), parseInt(end_date_data.substring(8,10)))
		var current_time = (new Date).getTime();

		if (current_time > start_date && current_time < end_date){
			$("#event-selector").append('<option>' + events[event].short_name + '</option>');
		}
	}


	}
})

function set_team(team) {
	$.ajax({
		type: "GET",
		headers: {
			"X-TBA-App-Id": "frc-4774:TrueSkill:1.0"
		},
		url: "https://www.thebluealliance.com/api/v2/team/frc" + team,
		dataType: "json",
		success: function (result) {
			$("#team-info").removeClass("hidden")
			$("#team-number").text(result.team_number)
			$("#team-name").text(result.nickname)
			$("#team-location").text(result.locality)


			$('.donut-chart').each(function (index) {
				$(this).append('<svg preserveAspectRatio="xMidYMid" xmlns:xlink="http://www.w3.org/1999/xlink" id="donutChartSVG' + index + '"><path d="M100,100" /></svg>');
				var p = new Donut_chart({
					element: $('#donutChartSVG' + index),
					percent: 50,
				});
				p.animate();
				$("#trueskill-info").empty().append("50 <span>85th percetile</span>")
			});

		},
		error: function () {
			alert("ERROR: Team not found");
		}
	});
}

function get_team_events(team) {
	$.ajax({
		type: "GET",
		headers: {
			"X-TBA-App-Id": "frc-4774:TrueSkill:1.0"
		},
		url: "https://www.thebluealliance.com/api/v2/team/frc" + team + "/2017/events",
		dataType: "json",
		success: function (result) {
			$("#event-list").empty();
			$("#event-list").append("<h3>Regionals</h3>")
			team_events = []
			for (event in result) {
				$("#event-list").append('<li>' + result[event].name + '</li>');
				team_events.push(result[event].key)
			}
			get_team_matches(team);
	
	},
		error: function () {
			alert("ERROR");
		}
	});
}

function get_team_matches(team){
$("#card-div").empty() //.prepend("<div id=\"p2\" class=\"mdl-progress mdl-js-progress mdl-progress__indeterminate\"></div>");
for (event in team_events){

	$.ajax({
		type: "GET",
		headers: {"X-TBA-App-Id": "frc-4774:TrueSkill:1.0"},
		url: "https://www.thebluealliance.com/api/v2/team/frc" + team + "/event/" + team_events[event] + "/matches",
		dataType: "json",
		success: function (result) {
			if (result.length === 0){
				return
			}
			result.sort(function(a,b){
				return a.time - b.time
			})
			for (match in result){
			var winner = ""
			var current_match = result[match]
			
			if (current_match.alliances.blue.score < 0){
				return
			}
			if (current_match.alliances.blue.score > current_match.alliances.red.score){
				winner = "match_blue"
			}
			else{
				winner = "match_red"
			}

			$("#card-div").prepend(make_card("", current_match.alliances.blue.teams, current_match.alliances.red.teams,
			 current_match.comp_level.toUpperCase()+String(current_match.match_number),
			 "pass", current_match.time, winner))
			}

		},
		error: function () {
			alert("ERROR");
		}

	});
}

function get_team_matches(team) {
	$("#card-team-div").empty() //.prepend("<div id=\"p2\" class=\"mdl-progress mdl-js-progress mdl-progress__indeterminate\"></div>");
	for (event in team_events) {
		$.ajax({
			type: "GET",
			headers: {
				"X-TBA-App-Id": "frc-4774:TrueSkill:1.0"
			},
			url: "https://www.thebluealliance.com/api/v2/team/frc" + team + "/event/" + team_events[event] + "/matches",
			dataType: "json",
			success: function (result) {
				if (result.length === 0) {
					return
				}
				result.sort(function (a, b) {
					return a.time - b.time
				})
				for (match in result) {
					var winner = ""
					var current_match = result[match]

					if (current_match.alliances.blue.score < 0) {
						return
					}

					$("#card-team-div").prepend(make_card("", current_match.alliances.blue.teams, current_match.alliances.red.teams,
						current_match.alliances.blue.score, current_match.alliances.red.score,
						current_match.comp_level.toUpperCase() + String(current_match.match_number),
						team_events_names[current_match.event_key], current_match.time))
				}

			},

		});
	}
}
function set_event(event_name){
	var event_key = ""
	for (event in events){
		if (events[event].short_name === event_name){
			event_key = events[event].key
			$("#event-info").removeClass("hidden")
			$("#event-name").text(events[event].short_name)
			$("#event-location").text(events[event].locality)
			$("#event-start-date").text(events[event].start_date)
			$("#event-end-date").text(events[event].end_date)
			event_name_event = events[event].short_name
			get_event_matches(event_key)
			break
	}}
}

function get_event_matches(key){
	$("#card-event-div").empty() //.prepend("<div id=\"p2\" class=\"mdl-progress mdl-js-progress mdl-progress__indeterminate\"></div>");
		$.ajax({
			type: "GET",
			headers: {
				"X-TBA-App-Id": "frc-4774:TrueSkill:1.0"
			},
			url: "https://www.thebluealliance.com/api/v2/event/"+key+"/matches",
			dataType: "json",
			success: function (result) {
				if (result.length === 0) {
					return
				}
				result.sort(function (a, b) {
					return a.time - b.time
				})
				for (match in result) {
					var winner = ""
					var current_match = result[match]

					if (current_match.alliances.blue.score < 0) {
						return
					}

					$("#card-event-div").prepend(make_card("", current_match.alliances.blue.teams, current_match.alliances.red.teams,
						current_match.alliances.blue.score, current_match.alliances.red.score,
						current_match.comp_level.toUpperCase() + String(current_match.match_number),
						event_name_event, current_match.time))
				}

			},

		});
	
}
function get_trueskill(){
	//team truskill json
	$.ajax({
			type: "GET",
			url: "",
			dataType: "json",
			success: function (result) {
			trueskill_score = result;

			},
		});
	//match prediction json
	$.ajax({
			type: "GET",
			url: "",
			dataType: "json",
			success: function (result) {
			trueskill_score = result;

			},

		});
}

$(function () {

$('select').on('change', function() {
  	 set_event(this.value);
	});

	$("#team-input").keypress(function (e) {
		if (e.which == 13) {
			team = $("#team-input").val();
			set_team(team);
			get_team_events(team);
		}
	});
	$(".refresh").click(function(){
		get_truskill()
		set_team(team)
		get_team_events(team)
		set_event(event_name_event)
	})
});