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
        'set_data' : function(data) {
            this.attached_data = data;
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
        this.editors_finalize();
        this.close();
        annotation_init(data["url"]);
        annotation_preview_refresh();
    }.bind(this);

    $.extend(this, $super, {
        'render' : function() {
            $super.render.bind(this)();
            $('#annotation-submit').click(function(event) {
                this.editors_sync();
                // can we get this from the event?
                var action = $('#annotation-submit').attr('action');
                var postdata = $('#annotation-compose-form').serialize();
                $.post(action, postdata, submit_response_handler, 'json');
            }.bind(this));

            this.editors_init();
        },
        /* editor-in-modal window support methods */
        'editors_init' : function() {
            if (this.attached_data["use_ckeditor"] === true) {
                /* look for textareas and replace with ckeditor */
                this.editors = [];
                var textareas = this.content_element.find('textarea');
                $.each(textareas, function(i, value) {
                    var textarea_id = textareas.attr('id');
                    var ckconfig = {};
                    /* set default */
                    if ('default' in __CKEDITOR_CONFIGS) {
                        ckconfig = __CKEDITOR_CONFIGS['default'];
                    }
                    if ('ckeditor_config' in this.attached_data) {
                        var ckconfig_name = this.attached_data["ckeditor_config"];
                        if (ckconfig_name in __CKEDITOR_CONFIGS) {
                            ckconfig = __CKEDITOR_CONFIGS[ckconfig_name];
                        }
                    }
                    var instance = CKEDITOR.replace(textarea_id, ckconfig);
                    this.editors.push(instance);
                }.bind(this));
            }
        },
        'editors_sync' : function() {
            /* synchronize ckeditors if present */
            if (this.attached_data["use_ckeditor"] === true) {
                $.each(this.editors, function(i, ckinstance) {
                    ckinstance.updateElement();
                });
            }
        },
        'editors_finalize' : function() {
            /* tear down ckeditors if present */
            if (this.attached_data["use_ckeditor"] === true) {
                $.each(this.editors, function(i, ckinstance) {
                    ckinstance.destroy();
                });
            }
        }
    });
}

function MyProfileModal() {
    var $super = new Modal();

    var submit_response_handler = function(data, texttype) {
        this.close();
        this.content_delete();
        this.content_set(data["body_html"], data["modal_id"]);
        this.render();
    }.bind(this);

    $.extend(this, $super, {
        'render' : function() {
            $super.render.bind(this)();
            $('#profile-conversations a').click(function(event) {
                this.close();
            }.bind(this));
            $('#profile-update-submit').click(function(event) {
                // can we get this from the event?
                var action = $('#profile-update-submit').attr('action');
                var postdata = $('#profile-update-form').serialize();
                $.post(action, postdata, submit_response_handler, 'json');
            }.bind(this));
        }
    });
}

function MembersModal() {
    var $super = new Modal();

    var submit_response_handler = function(data, texttype) {
        this.close();
        this.content_delete();
        this.content_set(data["body_html"], data["modal_id"]);
        this.render();
    }.bind(this);

    $.extend(this, $super, {
        'render' : function() {
            $super.render.bind(this)();
            $('#member-name a').click(function(event) {
                this.close();
            }.bind(this));
            $('#members-sort-form input:radio').change(function(event) {
                // can we get this from the event?
                var action = $('#members-sort-form').attr('action');
                var postdata = $('#members-sort-form').serialize();
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
        modal.set_data(data);
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

function myprofile_init(url) {
    modal_init(url, MyProfileModal);
}

function members_init(url) {
    modal_init(url, MembersModal);
}
