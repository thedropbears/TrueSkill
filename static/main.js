/* jshint asi: true */

function DonutChart(options) {
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
		var d;
		if (this.first) {
			d = this.circle.attr('d') + " M " + x + " " + y;
			this.first = false;
		} else {
			d = this.circle.attr('d') + " L " + x + " " + y;
		}
		this.circle.attr('d', d);
		this.i--;

		if (this.i <= 0) {
			clearInterval(this.timer);
		}
	}
}

function make_card(red_odds, blue_alliance, red_alliance, blue_score, red_score, match_name, match_location, match_id) {
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
	} else if (blue_score > red_score) {
		blue_team = "blue-team-won"
	} else if (red_score > blue_score) {
		red_team = "red-team-won"
	} else if (red_score === blue_score) {
		red_team = "red-team-won"
		blue_team = "blue-team-won"
	}
	return "<div class=\"match-card mdl-card mdl-shadow--4dp card " + match_id + "\">" +
		"<div class=\"mdl-card__title white-red\">" +
		"<h2 class=\"mdl-card__title-text\">" + match_name + " - " + match_location + "</h2>" +
		"</div>" +
		"<div class=\"mdl-card__supporting-text team\">" +
		"<div class=\'" + blue_team + " " + match_id + "\'>" +
		"<ul>" +
		"<li>" + blue_odds + "</li>" +
		"<li><b>" + blue_score + "</b></li>" +
		"<li>" + blue_alliance[0].slice(3) + " - " + get_team_name(blue_alliance[0]) + "</li>" +
		"<li>" + blue_alliance[1].slice(3) + " - " + get_team_name(blue_alliance[1]) + "</li>" +
		"<li>" + blue_alliance[2].slice(3) + " - " + get_team_name(blue_alliance[2]) + "</li>" +
		"</ul>" +
		"</div>" +
		"<div class=\'" + red_team + " " + match_id + "\'>" +
		"<ul>" +
		"<li>" + red_odds + "</li>" +
		"<li>" + red_alliance[0] + "</li>" +
		"<li>" + red_alliance[1] + "</li>" +
		"<li>" + red_alliance[2] + "</li>" +
		"<li><b>" + red_score + "</b></li>" +
		"<li>" + red_alliance[0].substring(3, 10) + " - " + team_names[red_alliance[0]] + "</li>" +
		"<li>" + red_alliance[1].substring(3, 10) + " - " + team_names[red_alliance[1]] + "</li>" +
		"<li>" + red_alliance[2].substring(3, 10) + " - " + team_names[red_alliance[2]] + "</li>" +
		"</ul>" +
		"</div>" +
		"</div>" +
		"</div>"
}

function change_card(win, match_id) {
	if (win === 'red') {
		$('.' + match_id + '.red-team').removeClass('red-team').addClass("red-team-won")
	} else if (win === 'blue') {
		$('.' + match_id + '.blue-team').removeClass('blue-team').addClass("blue-team-won")

	}
}


var events = []
var team_events = []
var team_events_names = {}
var event_name_event = ""
var team = '4774'
var trueskill_prediction = {}
var team_names = {}
var rank_list = []

get_trueskill_predictions()
get_team_names(0)
$.ajax({
	type: "GET",
	headers: {
		"X-TBA-App-Id": "frc-4774:TrueSkill:1.0"
	},
	url: "https://www.thebluealliance.com/api/v2/events/2017",
	dataType: "json",
	success: function (result) {
		events = result
		for (var i = 0; i < events.length; i++) {
			if (events[i].event_type > 5) {
				continue
			}

			var start_date = new Date(events[i].start_date)
			var end_date = new Date(events[i].end_date)
			end_date.setDate(end_date.getDate() + 1)
			var current_time = $.now();

			if (current_time > start_date && current_time < end_date) {
				$("#event-selector").append('<option>' + events[i].short_name + '</option>');
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
				var svgEl = $('<svg preserveAspectRatio="xMidYMid" xmlns:xlink="http://www.w3.org/1999/xlink"><path d="M100,100" /></svg>')
				$(this).append(svgEl);
				var p = new DonutChart({
					element: svgEl,
					percent: 100,
				});
				p.animate();
				get_trueskill_team_rank(result.team_number)
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
			var evList = $("#event-list").html("<h3>Regionals</h3>");
			team_events = []
			for (var i = 0; i < result.length; i++) {
				evList.append($('<li>').text(result[i].name));
				team_events.push(result[i].key)
			}
			get_team_matches(team);

		},
		error: function () {
			alert("ERROR");
		}
	});
}

function get_team_matches(team) {
	$("#card-div").empty() //.prepend("<div id=\"p2\" class=\"mdl-progress mdl-js-progress mdl-progress__indeterminate\"></div>");
	for (var i = 0; i < team_events.length; i++) {

		$.ajax({
			type: "GET",
			headers: {
				"X-TBA-App-Id": "frc-4774:TrueSkill:1.0"
			},
			url: "https://www.thebluealliance.com/api/v2/team/frc" + team + "/event/" + team_events[i] + "/matches",
			dataType: "json",
			success: function (result) {
				if (result.length === 0) {
					return
				}
				result.sort(function (a, b) {
					return a.time - b.time
				})
				for (var i = 0; i < result.length; i++) {
					var winner = ""
					var current_match = result[i]

					if (current_match.alliances.blue.score < 0) {
						return
					}
					if (current_match.alliances.blue.score > current_match.alliances.red.score) {
						winner = "match_blue"
					} else {
						winner = "match_red"
					}

					$("#card-div").prepend(make_card("", current_match.alliances.blue.teams, current_match.alliances.red.teams,
						current_match.comp_level.toUpperCase() + String(current_match.match_number),
						"pass", current_match.time, winner))
				}

			},
			error: function () {
				alert("ERROR");
			}

		});
	}
}

function get_team_matches(team) {
	$("#card-team-div").empty() //.prepend("<div id=\"p2\" class=\"mdl-progress mdl-js-progress mdl-progress__indeterminate\"></div>");
	for (var i = 0; i < team_events.length; i++) {
		$.ajax({
			type: "GET",
			headers: {
				"X-TBA-App-Id": "frc-4774:TrueSkill:1.0"
			},
			url: "https://www.thebluealliance.com/api/v2/team/frc" + team + "/event/" + team_events[i] + "/matches",
			dataType: "json",
			success: function (result) {
				if (result.length === 0) {
					return
				}
				result.sort(function (a, b) {
					return a.time - b.time
				})
				for (var i = 0; i < result.length; i++) {
					var current_match = result[i]
					prediction = trueskill_prediction[current_match.key]

					if (current_match.alliances.blue.score < 0) {
						current_match.alliances.blue.score = current_match.alliances.red.score = ""
						if (prediction === undefined) {
							continue
						}
					}
					if (prediction === undefined) {
						prediction = ""
					}
					if (current_match.comp_level != 'qm') {
						match_name = current_match.comp_level.toUpperCase() + String(current_match.match_number) + "." + String(current_match.set_number)
					} else {
						match_name = current_match.comp_level.toUpperCase() + String(current_match.match_number)
					}

					$("#card-team-div").prepend(make_card(prediction, current_match.alliances.blue.teams, current_match.alliances.red.teams,
						current_match.alliances.blue.score, current_match.alliances.red.score,
						match_name,
						team_events_names[current_match.event_key], current_match.key))

				}

			},

		});
	}
}

function set_event(event_name) {
	var event_key = ""
	for (var i = 0; i < events; i++) {
		if (events[i].short_name === event_name) {
			event_key = events[i].key
			$("#event-info").removeClass("hidden")
			$("#event-name").text(events[i].short_name)
			$("#event-location").text(events[i].location)
			$("#event-start-date").text(events[i].start_date)
			$("#event-end-date").text(events[i].end_date)
			event_name_event = events[i].short_name

			get_trueskill_event_rankings(event_key)
			get_event_matches(event_key)
			break
		}
	}
}

function get_event_matches(key) {
	$("#card-event-div").empty() //.prepend("<div id=\"p2\" class=\"mdl-progress mdl-js-progress mdl-progress__indeterminate\"></div>");
	$.ajax({
		type: "GET",
		headers: {
			"X-TBA-App-Id": "frc-4774:TrueSkill:1.0"
		},
		url: "https://www.thebluealliance.com/api/v2/event/" + key + "/matches",
		dataType: "json",
		success: function (result) {
			if (result.length === 0) {
				return
			}
			result.sort(function (a, b) {
				return a.time - b.time
			})
			for (var i = 0; i < result.length; i++) {
				var winner = ""
				var current_match = result[i]

				prediction = trueskill_prediction[current_match.key]

				if (current_match.alliances.blue.score < 0) {
					current_match.alliances.blue.score = current_match.alliances.red.score = ""
					if (prediction === undefined) {
						continue
					}
				}
				if (prediction === undefined) {
					prediction = ""
				}
				if (current_match.comp_level != 'qm') {
					match_name = current_match.comp_level.toUpperCase() + String(current_match.match_number) + "." + String(current_match.set_number)
				} else {
					match_name = current_match.comp_level.toUpperCase() + String(current_match.match_number)
				}

				$("#card-event-div").prepend(make_card(prediction, current_match.alliances.blue.teams, current_match.alliances.red.teams,
					current_match.alliances.blue.score, current_match.alliances.red.score,
					match_name,
					event_name_event, current_match.key))
			}
		},

	});

}

function get_trueskill_event_rankings(event) {
	//team truskill json
	$.ajax({
		type: "GET",
		url: "/api/trueskills/" + event,
		dataType: "text",
		success: function (result) {
			$("#event-ranking-card-div").removeClass("hidden")
			var rankingListEl = $(".event-ranking").empty()
			for (var i = 0; i < result.length; i++) {
				var skill = result[i][0];
				var teamNum = result[i][1];
				var nickname = result[i][2];
				var li = $("<li>").text(teamNum + " - " + nickname + " - " + Math.round(skill * 100) / 100);
				rankingListEl.append(li)
			}
		},
	});
}

function get_trueskill_team_rank(team) {
	$.ajax({
		type: "GET",
		url: "/api/trueskill/" + team,
		dataType: "text",
		success: function (result) {
			$("#trueskill-info").html(Math.round(result * 100) / 100 + "<span>TrueSkill Points</span>")

		}
	})
}

function get_trueskill_predictions() {
	//match prediction json
	$.ajax({
		type: "GET",
		url: "/predictions",
		dataType: "json",
		success: function (result) {
			trueskill_prediction = result;
		},

	});
}
var loaded = false

function get_team_names(page_num) {
	loaded = false
	$.ajax({
		type: "GET",
		headers: {
			"X-TBA-App-Id": "frc-4774:TrueSkill:1.0"
		},
		url: "https://www.thebluealliance.com/api/v2/teams/" + page_num,
		dataType: "json",
		success: function (result) {
			if (result.length === 0) {
				loaded = true
				loading(false)
				refresh()
				return
			}
			for (var i = 0; i < result.length; i++) {
				team_names[result[i].key] = result[i].nickname
			}
			get_team_names(page_num + 1)
		}

	});

}

function refresh() {
	get_trueskill_predictions()
	if (team) {
		set_team(team)
		get_team_events(team)
	}
	if (event_name_event) {
		set_event(event_name_event)
	}
}
var percent = 10

function loading(loading) {
	if (loading) {
		$(".loading").addClass('is-active')
	} else {
		$(".loading").removeClass('is-active')
	}
}

$(function () {
	$('select').on('change', function () {
		if (loaded) {
			set_event(this.value);
		}
	});

	$("#team-input").keypress(function (e) {
		team = $("#team-input").val();
		if (loaded) {
			if (e.which == 13) {
				set_team(team);
				get_team_events(team);
			}
		}
	});
	$(".refresh").click(function () {
		refresh()
	})
	loading(true)
});
