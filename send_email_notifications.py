import rlc.settings
from django.core.management import setup_environ
setup_environ(rlc.settings)
from er.models import EmailNotification as mEmailNotification
from er.emailnotification import emailNotification

import logging
logger = logging.getLogger(__name__)

emails = mEmailNotification.objects.all()
for email in emails:
    try:
        emailNotification(model_object=email).send()
    except Exception, ex:
        logger.error(ex)
