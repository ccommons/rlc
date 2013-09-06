//Global container for the popover functionality.

var POPOVER = {
	'initPopover': function (options) {
		options = options || {
			'animation': false,
			'placement': 'bottom',
			'content': 'Sample content here.' //Should be replaced with actual content
		};
        // attempt to get content from an attached data element
        if (this.$el.attr("data-element") !== undefined) {
            // TODO: check to see if that data element actually
            // exists and there is actually something in it
            options["html"] = true;
            var $content_element = $('#'+this.$el.attr("data-element"));
            options["content"] = $content_element.html();
        }
		this.$el.popover(options);
		this.$el.addClass('js-initialized');
	},
	'show': function () {
		this.closeAllPopovers();
		this.$el.popover('show');
		this.$el.addClass('has-popover');

		this.calculatePosition();
		
		$('body').on('click', function (evt) {
			var target = $(evt.target), //We use target to identify where exactly the event occurred.
				popover = target.parents('.popover');

			if (target.hasClass('has-popover') || target.parents('.has-popover').length) {
				return;
			}
			//If there are no popovers identified as parents
			//to the target element, it means the event
			//occurred elsewhere on the page, therefore,
			//we may proceed with closing the opened popovers.
			if (!popover.length) {
				this.closeAllPopovers();
			}
		}.bind(this));
	},
	'hide': function () {
		this.$el.popover('hide');
		this.$el.removeClass('has-popover');
		$('body').off();
	},
	'isInitialized': function () {
		var f = false;
		if (this.$el.hasClass('js-initialized')) {
			f = true;
		}
		return f;
	},
	'hasPopover': function () {
		var f = false;
		if (this.$el.hasClass('has-popover')) {
			f = true;
		}
		return f;
	},
	'closeAllPopovers': function () {
		var owners = $('.has-popover');

		owners.each(function (index, owner) {
			owner = $(owner);
			if (owner) {
				owner.popover('destroy');
				owner.removeClass('has-popover js-initialized');
			}
		});
		$('body').off();
	},
	'calculatePosition': function () {
		var elPosition = null,
			popover = null,
			position = null,
			left = 0,
			top = 0;

		popover = this.$el.siblings('.popover');
		elPosition = this.$el.offset();
		position = popover.offset();
		left = position.left - (elPosition.left - position.left);
		top = position.top;
		popover.offset({'left': left, 'top': top});
	},
	'toggleNotifications': function () {
		this.$el = $('#lnk-notifications');
        
        if (!this.isInitialized()) {
            var options = {
	                'animation': false,
	                'html' : true,
	                'placement': 'bottom'
	            };
            this.initPopover(options);
        }

        if (this.hasPopover()) {
            this.hide();
        } else {
            this.show();
            var url = this.$el.attr('data-url');
            if (url !== undefined) {
                $.get(url, '', function(data, status, jqxhr) {
                    var $popover_content = this.$el.siblings('.popover').children(".popover-content");
                    $popover_content.html(data["body_html"]);
                    notification_icon_refresh();
                }.bind(this));
            } else {
                // TODO: fill in this error
                // (no URL defined)
            }
        }
	},
	'toggleProfileMenu': function () {
		this.$el = $('#lnk-profile-menu');
                var options = {
                    'animation': false,
                    'placement': 'bottom'
                    // 'html': 'text',
                    // 'content':  template.join('')
                };
		if (!this.isInitialized()) {
            this.initPopover(options);
        }
		if (this.hasPopover()) {
			this.hide();
		} else {
			this.show();
		}
	}
}
