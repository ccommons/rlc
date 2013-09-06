//var notification_icon_init = null;
//var notification_icon_refresh = null;

(function() {

var notification_count_url = '';

notification_icon_init = function(url){
    notification_count_url = url;
}

notification_icon_refresh = function(){
    var display = function(data, status, jqxhr) {
        count = data['count'];
        if (count > 0) {
            $('#notifications-count').html(data['count']);
        } else {
            $('#notifications-count').html('');
        }
    }
    $.get(notification_count_url, '', display, 'json');
}

})();
