from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import signing
from django.shortcuts import redirect


@login_required
def authorize(request):
    user = request.user

    if user.get_ticket() is None:
        messages.warning(request, "Sorry, only ticket holders can take part in the Botany tournament")
        return redirect('index')

    data = {"name": user.name, "email_addr": user.email_addr}
    signed_data = signing.dumps(data, key=settings.BOTANY_SECRET_KEY)

    url = settings.BOTANY_LOGIN_URL.format(signed_data)

    if "next" in request.GET:
        url += f"?next={request.GET['next']}"

    return redirect(url)
