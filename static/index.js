$(function(){
    var url = 'https://storage.googleapis.com/rutracker-rss.appspot.com/category_map.json';

    $.getJSON(url, {}, function(data, textStatus){

        var tree = $('#ctree').treeview({
          data: JSON.stringify(data)
        });
    });
});
