/* annotation placement infrastructure */

/* public API */
var annotation_preview_init = null;
var annotation_preview_refresh = null;

(function () {

var preview_url = '';

annotation_preview_init = function(url) {
    preview_url = url;
};

annotation_preview_refresh = function() {
    var display = function(data, status, jqxhr) {
        /* TODO: check status */
        /* remove any pre-existing previews */
        $('.annotation-preview').remove();
        /* show new previews */
        var previews = data["previews"];
        for (var i = 0; i < previews.length; i++) {
            var preview_info = previews[i];
            var $el = $('#' + preview_info["block_id"]);
            if ($el !== []) {
                $el.addClass('allow-annotation relative').append(preview_info["html"]);
            }
        }

        /* add click-to-activate-modal handlers */
        $('.annotation-modal-activate').click(function(event) {
            var url = $(event.currentTarget).attr('url');
            annotation_init(url);
        });
        $('.add-annotation').click(function(event) {
            var url = $(event.currentTarget).attr('url');
            annotation_compose_init(url);
        });

        /* update summary */
        $('#annotation-summary-container').replaceWith(data["summary_html"]);
    }
    $.get(preview_url, '', display, 'json');
}
})();

