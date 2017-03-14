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

$(function() {
	$('.donut-chart').each(function(index) {
		$(this).append('<svg preserveAspectRatio="xMidYMid" xmlns:xlink="http://www.w3.org/1999/xlink" id="donutChartSVG'+index+'"><path d="M100,100" /></svg>');
		var p = new Donut_chart({element: $('#donutChartSVG'+index), percent: $(this).attr('data-percent')});
		p.animate();
	});
});