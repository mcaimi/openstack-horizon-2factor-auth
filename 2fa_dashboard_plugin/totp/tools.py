#
# QRCode gen tools
#
import qrcode
from rfc6238 import totp
from StringIO import StringIO
from openstack_dashboard import settings
from django.http import HttpResponse
from horizon import exceptions

# generate html response with QR code to allow the user to sync mobile token generators
def qr(request, token_seed=None, html_encode=True):
    """
    Return a QR code for the secret key associated with the userid
    The QR code is returned as file with MIME type image/png.
    """
    if not token_seed:
        raise exceptions.HorizonException

    # compute token...
    token = totp.TOTP(token_seed)
    provisioning_prefix = getattr(settings, 'OPENSTACK_TWO_FACTOR_PROVISIONING', '')
    provisioning_uri = totp.build_uri(secret=token_seed, name=request.user.username)
    qrCodeImage = qrcode.make(provisioning_uri)
    img = StringIO()
    qrCodeImage.save(img)
    img.seek(0)

    # return QRCode
    if html_encode:
        return HttpResponse(img, content_type="image/png")

    # return bare image data
    return img

