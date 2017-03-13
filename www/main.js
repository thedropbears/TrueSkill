function Donut_chart(options) {
	
	this.settings = $.extend({
		element: options.element,
		percent: 100	
	}, options);
	
	
	this.circle = this.settings.element.find('path');
	this.settings.stroke_width = parseInt(this.circle.css('stroke-width'));
	this.radius = (parseInt(this.settings.element.css('width'))/1.5-this.settings.stroke_width)/2;
	this.angle = -97.5; // Origin of the draw at the top of the circle
	this.i = Math.round(0.75*this.settings.percent);
	this.first = true;
	
	this.animate = function() {
		this.timer = setInterval(this.loop.bind(this), 10);
	};
	
	this.loop = function(data) {
		this.angle += 5;  
		this.angle %= 360;
		var radians = (this.angle/180) * Math.PI;
		var x = this.radius + this.settings.stroke_width/2 + Math.cos(radians) * this.radius;
		var y = this.radius + this.settings.stroke_width/2 + Math.sin(radians) * this.radius;
		if(this.first==true) {
			var d = this.circle.attr('d')+" M "+x+" "+y;
			this.first = false;
		}
		else {
			var d = this.circle.attr('d')+" L "+x+" "+y;
		}
		this.circle.attr('d', d);
		this.i--;
		
		if(this.i<=0) {
			clearInterval(this.timer);
		}
	}
};

function make_card(red_odds, teams, match_name, match_location, ts, type){
	var blue_team = "blue-team"
	var red_team = "red-team"

		if (type === 'match_blue'){
			blue_team = "blue-team-won"
		}
		else if (type === 'match_red'){
			red_team = "red-team-won"
		}
		
		return "<div class=\"match-card mdl-card mdl-shadow--4dp card "+ts+"\"> \
            <div class=\"mdl-card__title white-red\"> \
              <h2 class=\"mdl-card__title-text\">"+match_name+" - "+ match_location +"</h2> \
            </div>\
            <div class=\"mdl-card__supporting-text team\">\
              <div class=\'"+blue_team+" "+ts+"\'>\
                <ul>\
                  <li>"+String(100-red_odds)+"%</li>\
                  <li>"+teams[0]+"</li>\
                  <li>"+teams[1]+"</li>\
                  <li>"+teams[2]+"</li>\
                </ul>\
              </div>\
              <div class=\'"+red_team+" "+ts+"\'>\
                <ul>\
                  <li>"+String(red_odds)+"%</li>\
                  <li>"+teams[0]+"</li>\
                  <li>"+teams[1]+"</li>\
                  <li>"+teams[2]+"</li>\
                </ul>\
              </div>\
            </div>\
          </div>"
}

function change_card(win, ts){
	console.log("helo")
	if (win === 'red'){
		$('.'+ts+'.red-team').removeClass('red-team').addClass("red-team-won")
	}
	else if (win === 'blue'){
		console.log('.'+ts+'.blue-team')
		$('.'+ts+'.blue-team').removeClass('blue-team').addClass("blue-team-won")

	}}


var events = []

$(function() {
	$('.donut-chart').each(function(index) {
		$(this).append('<svg preserveAspectRatio="xMidYMid" xmlns:xlink="http://www.w3.org/1999/xlink" id="donutChartSVG'+index+'"><path d="M100,100" /></svg>');
		var p = new Donut_chart({element: $('#donutChartSVG'+index), percent: $(this).attr('data-percent')});
		p.animate();
	});

if (events != []){
for (event in events){	
	$("#event-selector").append('<option>'+events[event].short_name+'</option>');
}}

        $("#team-input").focusout(function(){
			var team = $("#team-input").val() 
        });
});