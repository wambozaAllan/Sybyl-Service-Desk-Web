/*! formstone v1.4.10 [touch.js] 2018-08-03 | GPL-3.0 License | formstone.it */
!function(e){"function"==typeof define&&define.amd?define(["jquery","./core"],e):e(jQuery,Formstone)}(function(e,t){"use strict";function a(e){e.preventManipulation&&e.preventManipulation();var t=e.data,a=e.originalEvent;if(a.type.match(/(up|end|cancel)$/i))s(e);else{if(a.pointerId){var o=!1;for(var p in t.touches)t.touches[p].id===a.pointerId&&(o=!0,t.touches[p].pageX=a.pageX,t.touches[p].pageY=a.pageY);o||t.touches.push({id:a.pointerId,pageX:a.pageX,pageY:a.pageY})}else t.touches=a.touches;a.type.match(/(down|start)$/i)?n(e):a.type.match(/move$/i)&&i(e)}}function n(n){var o=n.data,p="undefined"!==e.type(o.touches)&&o.touches.length?o.touches[0]:null;p&&o.$el.off(d.mouseDown),o.touching||(o.startE=n.originalEvent,o.startX=p?p.pageX:n.pageX,o.startY=p?p.pageY:n.pageY,o.startT=(new Date).getTime(),o.scaleD=1,o.passedAxis=!1),o.$links&&o.$links.off(d.click);var u=c(o.scale?d.scaleStart:d.panStart,n,o.startX,o.startY,o.scaleD,0,0,"","");if(o.scale&&o.touches&&o.touches.length>=2){var h=o.touches;o.pinch={startX:r(h[0].pageX,h[1].pageX),startY:r(h[0].pageY,h[1].pageY),startD:l(h[1].pageX-h[0].pageX,h[1].pageY-h[0].pageY)},u.pageX=o.startX=o.pinch.startX,u.pageY=o.startY=o.pinch.startY}o.touching||(o.touching=!0,o.pan&&!p&&X.on(d.mouseMove,o,i).on(d.mouseUp,o,s),t.support.pointer?X.on([d.pointerMove,d.pointerUp,d.pointerCancel].join(" "),o,a):X.on([d.touchMove,d.touchEnd,d.touchCancel].join(" "),o,a),o.$el.trigger(u))}function i(t){var a=t.data,n="undefined"!==e.type(a.touches)&&a.touches.length?a.touches[0]:null,i=n?n.pageX:t.pageX,o=n?n.pageY:t.pageY,p=i-a.startX,u=o-a.startY,h=p>0?"right":"left",g=u>0?"down":"up",X=Math.abs(p)>a.threshold,Y=Math.abs(u)>a.threshold;if(!a.passedAxis&&a.axis&&(a.axisX&&Y||a.axisY&&X))s(t);else{!a.passedAxis&&(!a.axis||a.axis&&a.axisX&&X||a.axisY&&Y)&&(a.passedAxis=!0),a.passedAxis&&(f.killEvent(t),f.killEvent(a.startE));var v=!0,x=c(a.scale?d.scale:d.pan,t,i,o,a.scaleD,p,u,h,g);if(a.scale)if(a.touches&&a.touches.length>=2){var m=a.touches;a.pinch.endX=r(m[0].pageX,m[1].pageX),a.pinch.endY=r(m[0].pageY,m[1].pageY),a.pinch.endD=l(m[1].pageX-m[0].pageX,m[1].pageY-m[0].pageY),a.scaleD=a.pinch.endD/a.pinch.startD,x.pageX=a.pinch.endX,x.pageY=a.pinch.endY,x.scale=a.scaleD,x.deltaX=a.pinch.endX-a.pinch.startX,x.deltaY=a.pinch.endY-a.pinch.startY}else a.pan||(v=!1);v&&a.$el.trigger(x)}}function s(t){var a=t.data,i="undefined"!==e.type(a.touches)&&a.touches.length?a.touches[0]:null,s=i?i.pageX:t.pageX,p=i?i.pageY:t.pageY,r=s-a.startX,l=p-a.startY,u=(new Date).getTime(),h=a.scale?d.scaleEnd:d.panEnd,g=r>0?"right":"left",Y=l>0?"down":"up",v=Math.abs(r)>1,x=Math.abs(l)>1;if(a.swipe&&u-a.startT<a.time&&Math.abs(r)>a.threshold&&(h=d.swipe),a.axis&&(a.axisX&&x||a.axisY&&v)||v||x){a.$links=a.$el.find("a");for(var m=0,w=a.$links.length;m<w;m++)o(a.$links.eq(m),a)}var M=c(h,t,s,p,a.scaleD,r,l,g,Y);X.off([d.touchMove,d.touchEnd,d.touchCancel,d.mouseMove,d.mouseUp,d.pointerMove,d.pointerUp,d.pointerCancel].join(" ")),a.$el.trigger(M),a.touches=[],a.scale,i&&(a.touchTimer=f.startTimer(a.touchTimer,5,function(){a.$el.on(d.mouseDown,a,n)})),a.touching=!1}function o(t,a){t.on(d.click,a,p);var n=e._data(t[0],"events").click;n.unshift(n.pop())}function p(e){f.killEvent(e,!0),e.data.$links.off(d.click)}function c(t,a,n,i,s,o,p,c,r){return e.Event(t,{originalEvent:a,bubbles:!0,pageX:n,pageY:i,scale:s,deltaX:o,deltaY:p,directionX:c,directionY:r})}function r(e,t){return(e+t)/2}function l(e,t){return Math.sqrt(e*e+t*t)}function u(e,t){e.css({"-ms-touch-action":t,"touch-action":t})}var h=!t.window.PointerEvent,g=t.Plugin("touch",{widget:!0,defaults:{axis:!1,pan:!1,scale:!1,swipe:!1,threshold:10,time:50},methods:{_construct:function(e){if(e.touches=[],e.touching=!1,this.on(d.dragStart,f.killEvent),e.swipe&&(e.pan=!0),e.scale&&(e.axis=!1),e.axisX="x"===e.axis,e.axisY="y"===e.axis,t.support.pointer){var i="";!e.axis||e.axisX&&e.axisY?i="none":(e.axisX&&(i+=" pan-y"),e.axisY&&(i+=" pan-x")),u(this,i),this.on(d.pointerDown,e,a)}else this.on(d.touchStart,e,a).on(d.mouseDown,e,n)},_destruct:function(e){this.off(d.namespace),u(this,"")}},events:{pointerDown:h?"MSPointerDown":"pointerdown",pointerUp:h?"MSPointerUp":"pointerup",pointerMove:h?"MSPointerMove":"pointermove",pointerCancel:h?"MSPointerCancel":"pointercancel"}}),d=g.events,f=g.functions,X=t.$window;d.pan="pan",d.panStart="panstart",d.panEnd="panend",d.scale="scale",d.scaleStart="scalestart",d.scaleEnd="scaleend",d.swipe="swipe"});