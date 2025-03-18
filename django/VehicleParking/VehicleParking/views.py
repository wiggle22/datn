from django.http import HttpResponseRedirect
from django.shortcuts import render

def index_view(request):
    return HttpResponseRedirect('/accounts/home')
    
# views.py
from django.contrib.auth.views import PasswordResetView
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.forms import PasswordResetForm
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes

User = get_user_model()

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    form_class = PasswordResetForm
    email_template_name = 'registration/password_reset_email.html'

    def form_valid(self, form):
        """
        If the form is valid, send the email and keep the user on the same page.
        """
        email = form.cleaned_data['email']
        users = User.objects.filter(email=email)
        for user in users:
            opts = {
                'use_https': self.request.is_secure(),
                'token_generator': default_token_generator,
                'from_email': None,
                'email_template_name': self.email_template_name,
                'subject_template_name': 'registration/password_reset_subject.txt',
                'request': self.request,
                'html_email_template_name': 'registration/password_reset_email.html',
                'extra_email_context': {
                    'ROOT_URL': settings.ROOT_URL,
                    'user': user,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                    'token': default_token_generator.make_token(user),
                },
            }
            form.save(**opts)
        return self.render_to_response(self.get_context_data(email_sent=True))

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth import update_session_auth_hash
from .forms import CustomPasswordChangeForm

@login_required
def change_password(request):
    password_changed = False
    if request.method == 'POST':
        form = CustomPasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            user = form.save()
            update_session_auth_hash(request, user)  # Quan trọng để giữ người dùng đăng nhập sau khi đổi mật khẩu
            password_changed = True
    else:
        form = CustomPasswordChangeForm(request.user)
    return render(request, 'registration/password_change_form.html', {'form': form, 'password_changed': password_changed})