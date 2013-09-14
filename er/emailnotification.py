from er.models import EmailNotification as mEmailNotification
from er.models import EmailPreferences as mEmailPreferences
from er.event import event
from django.core.mail import EmailMessage
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.contrib.auth.models import User
import json

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
        self.reply_to = None

        if 'event' in kwargs:
            if isinstance(kwargs['event'], event) and kwargs['event'].model_object:
                if 'user' in kwargs:
                    # create new email notification record if there are event and user args
                    if settings.EMAIL_NOTIFICATION and self.email_preferred(kwargs['user'], kwargs['event']):
                        self.model_object = self.__class__.MODEL(
                            user=kwargs['user'],
                            event=kwargs['event'].model_object,
                        )
                        self.model_object.save()
                        self.user = kwargs['user']
                        self.event = kwargs['event']
                elif 'to' in kwargs and kwargs['to']:
                    # email without creating model object
                    self.event = kwargs['event']
                    # dummy user
                    self.user = User(username='dummy', email=kwargs['to'])

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

        if 'reply_to' in kwargs:
            self.reply_to = kwargs['reply_to']

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
        if self.event.action == 'shared':
            try:
                remarks = json.loads(self.event.remarks)
                subject_user = User.objects.get(id=remarks['sharer'])
            except Exception, ex:
                logger.error(ex)
        elif self.event.etype in ['comment_annotation', 'comment_news']:
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
                atype = c.model_object.annotation.atype
                if self.event.action == 'shared':
                    subject = ' '.join([
                        'shared',
                        (atype=='openq' and 'an' or 'a'),
                        atype_to_name(atype),
                        'with you.'
                    ])
                else:
                    subject = annotation_subject.get(atype, '')
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
                elif self.event.action == 'shared':
                    subject = 'shared a comment with you.'
                else:
                    # a regular reply
                    if root.user == self.user:
                        from er.views.annotations import atype_to_name
                        subject = 'replied to your %s.' % atype_to_name(root.model_object.annotation.atype).lower()
        elif self.event.etype == 'comment_news':
            if self.event.action == 'shared':
                subject = 'shared a comment with you.'
            else:
                subject = 'replied to a thread of your interest.'
        elif self.event.etype == 'er':
            if self.event.action == 'shared':
                subject = 'shared an Evidence Review with you.'
            elif self.event.action in ['revised', 'updated']:
                subject = 'The Evidence Review is revised.'
            elif self.event.action == 'published':
                subject = "The Evidence Review is published."
        elif self.event.etype == 'user':
            subject = "joined the system."

        if subject_user:
            subject = ' '.join([subject_user.first_name, subject_user.last_name, subject])
        return subject

    @property
    def message_plain(self):
        return self.event.email_message_plain

    @property
    def message_html(self):
        return self.event.email_message_html

    @property
    def deeplink(self):
        return self.event.url

    def send(self):
        if not self.user.email:
            logger.info('user %d has no email address saved' % self.user.id)
            return
        try:
            headers = {}
            connection = None
            if self.reply_to:
                headers['Reply-To'] = self.reply_to
            if self.connection:
                connection = self.connection

            email = EmailMultiAlternatives(
                subject = self.subject,
                body = self.message_plain,
                to = [self.user.email,],
                headers = headers,
                connection = connection,
            )
            email.attach_alternative(self.message_html, "text/html")
            email.send()
            self.delete()
        except Exception, ex:
            logger.error(ex)

