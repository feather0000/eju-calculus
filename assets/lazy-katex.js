/* Lazy KaTeX: render formulas only near the viewport / when a <details> opens,
   plus small idle-time slices, so no multi-second long task blocks the page. */
(function(){
  var orig=window.renderMathInElement; if(!orig||orig.__lazy) return;
  var RE=/\$|\\\(|\\\[|\\begin\{/;
  var SKIP=/^(SCRIPT|STYLE|TEXTAREA|PRE|CODE|OPTION|NOSCRIPT)$/;
  function lazy(root,opts){
    var todo=[],seen=new Set();
    var w=document.createTreeWalker(root,NodeFilter.SHOW_TEXT,{acceptNode:function(n){
      if(!RE.test(n.nodeValue))return 2;
      for(var p=n.parentNode;p&&p!==root;p=p.parentNode){if(SKIP.test(p.nodeName)||(p.classList&&p.classList.contains('katex')))return 2;}
      return 1;}});
    var n;while((n=w.nextNode())){var el=n.parentNode;
      // render at the nearest block so delimiters split across inline tags still match
      while(el!==root&&el.parentNode&&/^(SPAN|B|STRONG|EM|I|SUB|SUP|A|SMALL|MARK|U|LABEL)$/.test(el.nodeName))el=el.parentNode;
      if(!seen.has(el)){seen.add(el);todo.push(el);}}
    // drop elements contained in another queued element
    todo=todo.filter(function(e){for(var p=e.parentNode;p;p=p.parentNode)if(seen.has(p))return false;return true;});
    var done=new WeakSet();
    function go(el){if(done.has(el))return;done.add(el);io&&io.unobserve(el);try{orig(el,opts);}catch(e){}}
    var io='IntersectionObserver' in window?new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting)go(e.target);});},{rootMargin:'1200px 0px'}):null;
    if(!io){todo.forEach(go);return;}
    todo.forEach(function(e){io.observe(e);});
    document.addEventListener('toggle',function(ev){var d=ev.target;if(d.open)todo.forEach(function(e){if(d.contains(e))go(e);});},true);
    // render whatever is still pending in small idle slices (keeps find-in-page/print correct)
    var i=0,ric=window.requestIdleCallback||function(f){return setTimeout(function(){f({timeRemaining:function(){return 8}})},50)};
    function idle(dl){while(i<todo.length&&dl.timeRemaining()>4){go(todo[i++]);}if(i<todo.length)ric(idle,{timeout:2000});}
    setTimeout(function(){ric(idle,{timeout:2000});},1500);
    window.addEventListener('beforeprint',function(){todo.forEach(go);});
  }
  var wrap=function(el,opts){ if(el===document.body||el===document.documentElement) return lazy(el,opts); return orig(el,opts); };
  wrap.__lazy=true; window.renderMathInElement=wrap;
})();
