# 2FA Email Sending backend
# Supports plain SMTP transactions using the Django Email Facilities
#
import logging
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from openstack_dashboard.dashboards.identity.totp.tools import qr
from email.MIMEImage import MIMEImage

LOG = logging.getLogger(__name__)

# build and send email address with embedded TOTP token activation QRCode.
def send_activation_email(sender, recipient, subject, totp_token, request):
    html_content = render_to_string('identity/totp/email.html', request=request)
    text_content = "2Factor Authentication Activation Token: %s. KEEP IT SECRET!" % totp_token

    # create Email Message with text content...
    msg = EmailMultiAlternatives(subject, text_content, sender, [recipient])

    # embed HTML content....
    msg.attach_alternative(html_content, "text/html")
    msg.mixed_subtype = 'related'

    # append qrcode image data
    msg.attach('qrcode_image.png', qr(request=request, token_seed=totp_token, html_encode=False).getvalue(), 'image/png')

    # send email_message
    try:
        LOG.info("[2FA Activation] Sending activation email to %s" % recipient)
        msg.send()
    except Exception as e:
        raise e

