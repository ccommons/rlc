/* modal window interface for RLC */

function Modal() {
    $.extend(this, {
        'content_element' : null,
        'container_html' : '<div class="modal hide fade" tabindex="-1" role="dialog"></div>',
        'content_set' : function(content_html) {
            if (this.content_element === null) {
                this.content_element = $(this.container_html).appendTo('body');
            }
            this.content_element.html(content_html);
            // $('body').append(content_html);
            // var content_id = "#" + id;
            // this.content_element = $(content_id);
        },

        'load' : function (url) {
            var display = function(data, status, jqxhr) {
                // TODO: add protocol error checking
                this.content_set(data["body_html"]);
                this.set_data(data);
                this.render();
            };
            $.get(url, '', display.bind(this), 'json');
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
        'rendered' : false,
        'render' : function() {
            if (this.rendered === false) {
                this.content_element.modal();
                this.content_element.on('hidden', this.content_delete.bind(this));
            }
            this.rendered = true;
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
                // start inline editor, attach modal
                var event_element = $(event.currentTarget);
                var reply = new InlineReply(event_element);
                reply.$calling_modal = this;
            }.bind(this));
            $('a.newsitem-reply').click(function(event) {
                // start inline editor
                var event_element = $(event.currentTarget);
                var reply = new InlineReply(event_element);
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

                var ckconfig_name = "";
                if ('ckeditor_config' in this.attached_data) {
                    ckconfig_name = this.attached_data["ckeditor_config"];
                }
                this.ckeditor = new CKEditorsInModal(this.content_element, ckconfig_name);
            }
        },
        'editors_sync' : function() {
            /* synchronize ckeditors if present */
            if (this.attached_data["use_ckeditor"] === true) {
                this.ckeditor.sync();
            }
        },
        'editors_finalize' : function() {
            /* tear down ckeditors if present */
            if (this.attached_data["use_ckeditor"] === true) {
                this.ckeditor.finalize();
            }
        }
    });
}

function MyProfileModal() {
    var $super = new Modal();

    var submit_response_handler = function(data, texttype) {
        // this.close();
        // this.content_delete();
        /* TODO: make this into some better sort of handler */
        this.content_set(data["body_html"]);
        this.set_data(data);
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
        this.content_set(data["body_html"]);
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

function NewsModal() {
    var $super = new Modal();

    $.extend(this, $super, {
        'render' : function() {
            $super.render.bind(this)();

            $('a.news-comments-link').click(function(event) {
                this.close();
                var url = $(event.currentTarget).attr('url');
                news_comment_init(url);
            }.bind(this));

            $('.tag-filter').click(function(event) {
                var url = $(event.currentTarget).attr('url');
                this.close();
                news_index_init(url);
            }.bind(this));
        }
    });
}

/* inline reply object, for use in comment replies */
function InlineReply(initiating_element) {
    this.$parent = $('#' + initiating_element.attr('parent_id'));

    this.ckeditor = undefined;
    this.use_ckeditor = false;

    this.$new = undefined;

    this.$calling_modal = undefined;

    $.extend(this, {
        'show_reply_form' : function(data, status, jqxhr) {
            this.$new = $("<div/>").html(data["body_html"]);
            this.$parent.after(this.$new);
            if (data["use_ckeditor"] === true) {
                this.use_ckeditor = true;
                var ckconfig_name = "";
                if ('ckeditor_config' in data) {
                    ckconfig_name = data["ckeditor_config"];
                }
                this.ckeditor = new CKEditorsInModal(this.$new, ckconfig_name);
            }

            $('#reply-submit').click(function(event) {
                this.submit_reply_form(event);
            }.bind(this));
            $('.reply-close').click(function(event) {
                this.cancel_form(event);
            }.bind(this));

            // TODO: this seems to also scroll the base window
            var els = this.$new.get();
            if (els.length > 0) {
                els[0].scrollIntoView();
            }
        },

        'cancel_form' : function(event) {
            this.ckeditor.finalize();
            this.$new.remove();
        },

        'submit_reply_form' : function(event) {
            if (this.use_ckeditor === true) {
                this.ckeditor.sync();
            }
            var action = $(event.currentTarget).attr('action');
            // TODO: get this from the event
            var postdata = $('#reply-compose-form').serialize();
            // alert(postdata);
            $.post(action, postdata, this.reply_form_response.bind(this), 'json');
        },

        'reply_form_response' : function(data, status, jqxhr) {
            /* close inline commenter and replace with new comment */
            if (this.use_ckeditor === true) {
                this.ckeditor.finalize();
            }
            this.$new.html(data["html"]);

            // TODO: this seems to also scroll the base window
            var els = this.$new.get();
            if (els.length > 0) {
                els[0].scrollIntoView();
            }

            // switch the calling modal to new URL if present
            // (for example, if a proposed revision is approved)
            if (data.hasOwnProperty("change_modal") &&
                data.hasOwnProperty("url") &&
                this.$calling_modal !== undefined) {
                if (data["change_modal"] === true) {
                    this.$calling_modal.close();
                    annotation_preview_refresh();
                    annotation_init(data["url"]);
                }
            }

        }
    });

    var url = initiating_element.attr('reply_url');
    $.get(url, '', this.show_reply_form.bind(this), 'json');
}

function modal_init(url, modaltype) {
    if (typeof(modaltype) === 'undefined') {
        var modaltype = Modal;
    }
    var modal = new modaltype();
    modal.load(url);
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

function news_index_init(url) {
    modal_init(url, NewsModal);
}

function news_comment_init(url) {
    /* very similar to the annotation modal */
    modal_init(url, AnnotationModal);
}

/* dynamic ckeditor setup/sync/teardown */
function CKEditorsInModal(element, config_name) {
    this.element = element;
    this.editors = [];

    /* init: look for textareas and replace with ckeditor */
    var textareas = this.element.find('textarea');
    $.each(textareas, function(i, value) {
        var textarea_id = textareas.attr('id');
        var ckconfig = {};
        /* set default */
        if ('default' in __CKEDITOR_CONFIGS) {
            ckconfig = __CKEDITOR_CONFIGS['default'];
        }
        if (config_name in __CKEDITOR_CONFIGS) {
            ckconfig = __CKEDITOR_CONFIGS[config_name];
        }
        var instance = CKEDITOR.replace(textarea_id, ckconfig);
        this.editors.push(instance);
    }.bind(this));

    $.extend(this, {
        'sync' : function() {
            /* synchronize ckeditors if present */
            $.each(this.editors, function(i, ckinstance) {
                ckinstance.updateElement();
            });
        },
        'finalize' : function() {
            /* tear down ckeditors if present */
            $.each(this.editors, function(i, ckinstance) {
                ckinstance.destroy();
            });
        }
    });
}
