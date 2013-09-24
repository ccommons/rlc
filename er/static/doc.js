var __CKEDITOR_CONFIGS = {
    default : {
    },
    doceditor : {
        allowedContent: true,
        height: '500px'
    },
    annotation_compose : {
        toolbar: [
            [ 
                'Bold', 'Italic', '-',
                'RemoveFormat'
            ], [
                'SpecialChar'
            ], [
                'BulletedList', 'NumberedList', '-', 'Table'
            ], [
                'Link', 'Unlink'
            ], [
                'Image'
            ]
        ]
    }
}

function verify_json_response(data) {
    if (data.hasOwnProperty("error")) {
        if (data["error"] === 'logged_out') {
            if (data.hasOwnProperty("login_url")) {
                window.location.replace(data["login_url"]);
            } else {
                // this case is usually preferable; the mandatory login
                // redirector will help return to previous context
                location.reload();
            }
        }
    }
}

function references_init() {
    $('.rlc-reference').click(function(event) {
        $ref_element = $(event.currentTarget);
        /* initialize the tooltip if necessary */
        if ($ref_element.attr("data-toggle") === undefined) {
            $ref_element.attr("data-toggle", "tooltip");
            $ref_element.attr("data-trigger", "click");
            $ref_element.attr("data-placement", "right");
            var content = "<div class=\"ref-info\">";
            content += $ref_element.attr('data-ref-info') 
            if ($ref_element.attr('url') !== undefined) {
                content += '<br />';
                content += "<a class=\"ref-url\" target=\"_blank\" href=\"" + $ref_element.attr('url') + "\">";
                content += "View at PubMed";
                content += "</a>";
            }
            content += "</div>";

            $ref_element.attr("data-title", content);
            $ref_element.tooltip({
                "html" : true
            });
            $ref_element.tooltip('show');
        } else {
            // $ref_element.tooltip('toggle');
        }
        return false;
    });
}

