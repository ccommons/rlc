//Global container for the popover functionality.

var POPOVER = {
	'initPopover': function (options) {
		options = options || {
				'animation': false,
				'placement': 'bottom',
				'content': 'The revolutionary discovery of a striking, if temporary, effect that targeted inhibition of BRAF has on the clinical course of metastatic melanoma has spiked a new wave of research into molecular targets. In addition, it has raised a number of new questions: what are the mechanisms of both inherent and acquired resistance to BRAF inhibitors and the possible ways to overcome this resistance; how is the activating effect of BRAF inhibition on the MAPK pathway in cells with nonmutated BRAF avoided; how should melanoma tumors that have no activating mutations in BRAF, such as tumors with mutated NRAS or tumors that are wild type for both BRAF and NRAS, be targeted; which targeted or nontargeted drug combinations should be pursued as determined by the molecular profile of each and every tumor; what is the future of combination targeted therapy and immunotherapy; and many more.' //Should be replaced with actual content
			};
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
			//we may proseed with closing the opened popovers.
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
		!this.isInitialized() && this.initPopover();
		if (this.hasPopover()) {
			this.hide();
		} else {
			this.show();
		}
	},
	'toggleProfileMenu': function (myProfileUrl, allMembersUrl) {
		this.$el = $('#lnk-profile-menu');
		var template = [
				'<ul class="unstyled">',
				'<li><a href="javascript:myprofile_init(\'',
				myProfileUrl,
				'\')">My Profile</a></li>',
				'<li class="horizontal-separator"></li>',
				'<li><a href="javascript:members_init(\'',
				allMembersUrl,
				'\')">All Members</a></li>',
				'<li class="horizontal-separator"></li>',
				'<li><a href="#">Sign out</a></li>',
				'</ul>'
			],
			options = {
				'animation': false,
				'placement': 'bottom',
				'html': 'text',
				'content':  template.join('')
			};
		!this.isInitialized() && this.initPopover(options);
		if (this.hasPopover()) {
			this.hide();
		} else {
			this.show();
		}
	}
}