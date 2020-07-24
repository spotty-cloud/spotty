window.onload = function() {
    var links = document.querySelectorAll('a.external');

    for(var i = 0; i < links.length; i++) {
       links[i].target = '_blank';
    }
}
