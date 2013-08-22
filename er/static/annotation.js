/* annotation placement infrastructure */

var preview_url = '/er/3/annotation/previews/json';

function annotation_previews(preview_url) {
    var display = function(data, status, jqxhr) {
        /* remove any pre-existing previews */
        $('.annotation-preview').remove();
        /* show new previews */
        for (var i = 0; i < data.length; i++) {
            var preview_info = data[i];
            $el = $('#' + preview_info["block_id"]);
            if ($el !== []) {
                $el.after(preview_info["html"]);
            }
        }
    }
    $.get(preview_url, '', display, 'json');
}

