//Global container for the popover functionality.

var POPOVER = {
	'initPopover': function (options) {
		options = options || {
				'animation': false,
				'placement': 'bottom',
				'content': 'Sample content' //Should be replaced with actual content
			};
		this.$el.popover(options);
		this.$el.addClass('js-initialize');
	},
	'show': function () {
		this.closeAllPopovers();
		this.$el.popover('show');
		this.$el.addClass('has-popover');
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
				'<li><a href="javascript:members_init(\'',
				allMembersUrl,
				'\')">All Members</a></li>',
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