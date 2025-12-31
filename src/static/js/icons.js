document.addEventListener('DOMContentLoaded', function(){
  document.querySelectorAll('.icon[data-icon]').forEach(function(el){
    if(!el.querySelector('img')){
      var src = el.getAttribute('data-icon');
      if(src){
        var img = document.createElement('img');
        img.src = src;
        img.alt = '';
        img.onload = function(){ img.style.opacity = '1'; };
        img.style.opacity = '0';
        img.style.transition = 'opacity .15s ease-in-out';
        el.innerHTML = '';
        el.appendChild(img);
      }
    }
  });
});
