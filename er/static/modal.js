/* modal window interface for RLC */

function Modal() {
    $.extend(this, {
        'content_element' : null,
        'content_set' : function(content_html, id) {
            $('body').append(content_html);
            var content_id = "#" + id;
            this.content_element = $(content_id);
        },
        'content_delete' : function() {
            if (this.content_element !== null) {
                this.content_element.remove();
                this.content_element = null;
            }
        },
        'close' : function() {
            this.content_element.modal('hide');
        },
        'render' : function() {
            this.content_element.modal();
            this.content_element.on('hidden', this.content_delete.bind(this));
        }
    });
}

function AnnotationModal() {
    var $super = new Modal();
    $.extend(this, $super, {
        'render' : function() {
            $super.render.bind(this)();
            $('#annotation-compose').click(function(event) {
                this.close();
                var url = $(event.currentTarget).attr('url');
                annotation_compose_init(url);
            }.bind(this));
            $('a.annotation-reply').click(function(event) {
                // TODO: replace generic compose with inline editor
                this.close();
                var url = $(event.currentTarget).attr('reply_url');
                annotation_compose_init(url);
            }.bind(this));
            $('a.annotation-page').click(function(event) {
                var source = $(event.currentTarget);
                var el = $('#' + source.attr("target_el"));
                var increment = parseInt(source.attr("incr"));
                var num_annotations = parseInt(el.attr("num_annotations"));
                var current_pos = parseInt(el.attr("current_pos"));
                var new_pos = current_pos + increment;
                if (new_pos == 0) {
                    /* do nothing */
                } else if (new_pos > num_annotations) {
                    /* do nothing */
                } else {
                    var new_pos_str = new_pos.toString();
                    el.text(new_pos_str);
                    el.attr("current_pos", new_pos_str);
                    var tab_id = "#annotation-activate-" + new_pos_str;
                    $(tab_id).tab('show');
                }
                /* TODO: show/hide links */
            }.bind(this));
            $('.annotation-context a').click(function(event) {
                // TODO: replace generic compose with inline editor
                var block_id = $(event.currentTarget).attr('block_id');
                this.close();
                var els = $('#' + block_id).get();
                if (els.length > 0) {
                    els[0].scrollIntoView(true);
                    // TODO: move this to a new function that also adjusts
                    // the location versus the header
                }
            }.bind(this));
        }
    });
}

function AnnotationComposeModal() {
    var $super = new Modal();

    var submit_response_handler = function(data, texttype) {
        this.close();
        annotation_init(data["url"]);
    }.bind(this);

    $.extend(this, $super, {
        'render' : function() {
            $super.render.bind(this)();
            $('#annotation-submit').click(function(event) {
                // can we get this from the event?
                var action = $('#annotation-submit').attr('action');
                var postdata = $('#annotation-compose-form').serialize();
                $.post(action, postdata, submit_response_handler, 'json');
            }.bind(this));
        }
    });
}

function modal_init(url, modaltype) {
    if (typeof(modaltype) === 'undefined') {
        var modaltype = Modal;
    }
    var display = function(data, status, jqxhr) {
        // TODO: add protocol error checking
        var modal = new modaltype();
        modal.content_set(data["body_html"], data["modal_id"]);
        modal.render();
    }
    $.get(url, '', display, 'json');
}

function annotation_init(url) {
    modal_init(url, AnnotationModal);
}

function annotation_compose_init(url) {
    modal_init(url, AnnotationComposeModal);
}
