from er.models import EmailNotification as mEmailNotification
from er.models import EmailPreferences as mEmailPreferences
from er.event import event
from django.core.mail import EmailMessage

import HTMLParser

import logging
logger = logging.getLogger(__name__)

class emailNotification(object):
    """Represents an email notification"""
    MODEL = mEmailNotification

    def __init__(self, *args, **kwargs):
        self.user = None
        self.event = None
        self.model_object = None
        self.connection = None

        # create new email notification record if there are event and user args
        if 'event' in kwargs and 'user' in kwargs:
            if isinstance(kwargs['event'], event) and kwargs['event'].model_object:
                if self.email_preferred(kwargs['user'], kwargs['event']):
                    self.model_object = self.__class__.MODEL(
                        user=kwargs['user'],
                        event=kwargs['event'].model_object,
                    )
                    self.model_object.save()
                    self.user = kwargs['user']
                    self.event = kwargs['event']

        if 'model_object' in kwargs:
            if isinstance(kwargs['model_object'], self.__class__.MODEL):
                self.model_object = kwargs['model_object']
                self.user = self.model_object.user
                self.event = event(model_object=self.model_object.event, event_handler=kwargs.get('event_handler', None))
            else:
                raise TypeError('model_object must be an instance of %s' % type(self.__class__.MODEL))

        # should check
        if 'connection' in kwargs:
            self.connection = kwargs['connection']

    def email_preferred(self, user, event):
        try:
            preferences = user.emailpreferences
        except:
            preferences = mEmailPreferences(user=user)
            preferences.save()
        return event.event_handler.__class__.match_email_preference(preferences, event)

    def delete(self):
        if self.model_object:
            self.model_object.delete()
            self.model_object = None

    @property
    def subject(self):
        subject_user = None
        if self.event.etype in ['comment_annotation', 'comment_news']:
            if self.event.action not in ['proprev_accepted', 'proprev_rejected']:
                subject_user = self.event.resource.user
        elif self.event.etype == 'user':
            subject_user = self.event.resource

        annotation_subject = {
            'proprev' : 'proposed a revision.',
            'rev' : 'proposed a revision.',
            'note' : 'attached a note.',
            'openq' : 'asked an open question.',
        }
        subject = ''
        if self.event.etype == 'comment_annotation':
            c = self.event.event_handler.create_comment_obj(self.event)
            subject = 'replied to a thread of your interest.'
            try:
                # an annotation
                subject = annotation_subject.get(c.model_object.annotation.atype, '')
            except:
                # a reply
                root = c.root
                if self.event.action == 'proprev_accepted':
                    if root.user == self.user:
                        subject = 'Your proposed revision is accepted.'
                    else:
                        subject = 'The propesed revision is accepted.'
                elif self.event.action == 'proprev_rejected':
                    if root.user == self.user:
                        subject = 'Your proposed revision is rejected.'
                    else:
                        subject = 'The propesed revision is rejected.'
                else:
                    # a regular reply
                    if root.user == self.user:
                        from er.views.annotations import atype_to_name
                        subject = 'replied to your %s.' % atype_to_name(root.model_object.annotation.atype).lower()
        elif self.event.etype == 'comment_news':
            subject = 'replied to a thread of your interest.'
        elif self.event.etype == 'er':
            if self.event.action in ['revised', 'updated']:
                subject = 'The Evidence Review is revised.'
            elif self.event.action == 'published':
                subject = "The Evidence Review is published."
        elif self.event.etype == 'user':
            subject = "joined the system."
        if subject_user:
            subject = ' '.join([subject_user.first_name, subject_user.last_name, subject])
        return subject

    @property
    def message(self):
        try:
            html_parser = HTMLParser.HTMLParser()
            return html_parser.unescape(self.event.email_message)
        except Exception,ex:
            logger.error(ex)
            return ''

    @property
    def deeplink(self):
        try:
            return self.event.url
        except Exception,ex:
            logger.error(ex)
            return ''

    def send(self):
        if not self.user.email:
            logger.info('user %d has no email address saved' % self.user.id)
            return
        try:
            email = EmailMessage(
                subject = self.subject,
                body = self.message + '\n\n' + self.deeplink,
                to = [self.user.email,],
            )
            if self.connection:
                email.connection = self.connection
            email.send()
            self.delete()
        except Exception, ex:
            logger.error(ex)

