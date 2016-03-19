$(function(){
    var url = 'https://storage.googleapis.com/rutracker-rss.appspot.com/category_map.json';
    var url = 'https://dl.dropboxusercontent.com/u/660127/category_map.json';    // TODO

    $.getJSON(url, {}, function(data, textStatus){

        var tree = $('#ctree').treeview({
          data: JSON.stringify(data)
        });
    });
});
