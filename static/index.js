$(function(){
    var url = 'https://storage.googleapis.com/rutracker-rss.appspot.com/category_map.json';
    var url = 'https://ttupdater-choom.c9users.io/static/category_map.json';    // TODO

    $.getJSON(url, {}, function(data, textStatus){

        var tree = $('#ctree').treeview({
          data: JSON.stringify(data)
        });
    });
});
