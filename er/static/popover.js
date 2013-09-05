//Global container for the popover functionality.

var POPOVER = {
	'initPopover': function (options) {
		options = options || {
				'animation': false,
				'placement': 'bottom',
				'content': 'The revolutionary discovery of a striking, if temporary, effect that targeted inhibition of BRAF has on the clinical course of metastatic melanoma has spiked a new wave of research into molecular targets. In addition, it has raised a number of new questions: what are the mechanisms of both inherent and acquired resistance to BRAF inhibitors and the possible ways to overcome this resistance; how is the activating effect of BRAF inhibition on the MAPK pathway in cells with nonmutated BRAF avoided; how should melanoma tumors that have no activating mutations in BRAF, such as tumors with mutated NRAS or tumors that are wild type for both BRAF and NRAS, be targeted; which targeted or nontargeted drug combinations should be pursued as determined by the molecular profile of each and every tumor; what is the future of combination targeted therapy and immunotherapy; and many more.' //Should be replaced with actual content
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
		this.$el.addClass('js-initialize');
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
                    }
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
