$(function(){
    $.getJSON('https://storage.googleapis.com/rutracker-rss.appspot.com/category_map.json', {}, function(data, textStatus){

        var tree = $('#ctree').treeview({
          data: data
        });
    });
});
