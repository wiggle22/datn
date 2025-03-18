# Create your views here.
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.password_validation import CommonPasswordValidator, NumericPasswordValidator, MinimumLengthValidator
from django.shortcuts import render
from django.http import HttpResponseRedirect
from django.contrib.sites.shortcuts import get_current_site
from django import forms
from django.contrib.auth.models import User
from django.core.mail import EmailMessage
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.http import HttpResponse
from django.conf import settings
from django.template.loader import get_template

from .tokens import account_activation_token

from django.utils.translation import ngettext
from django.utils.translation import gettext_lazy as _

def custom_404(request, exception):
    return render(request, '404.html', status=404)

class MyRegForm(UserCreationForm):
    email = forms.EmailField(
        max_length=200,
        help_text='Bắt buộc',
        error_messages={
            'required': 'Trường email là bắt buộc.',
            'invalid': 'Định dạng email không hợp lệ.',
        }
    )

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].help_text = "Tên đăng nhập ({0})".format(self.fields['username'].help_text)
        self.fields['username'].error_messages = {
            'required': 'Trường tên đăng nhập là bắt buộc.',
            'unique': 'Tên đăng nhập này đã tồn tại.',
        }
        self.fields['password1'].error_messages = {
            'required': 'Trường mật khẩu là bắt buộc.',
        }
        self.fields['password2'].error_messages = {
            'required': 'Vui lòng nhập lại mật khẩu.',
            'password_mismatch': 'Hai mật khẩu không khớp nhau.',
        }

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email này đã tồn tại.', code='email_exists')
        return email

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                'Hai mật khẩu không khớp nhau.',
                code='password_mismatch',
            )
        return password2

class CustomCommonPasswordValidator(CommonPasswordValidator):    
    def validate(self, password, user=None):
        if password.lower().strip() in self.passwords:
            raise forms.ValidationError(
                _("Mật khẩu mới quá phổ biến."),
                code="password_too_common",
            )

class CustomNumericPasswordValidator(NumericPasswordValidator):
    def validate(self, password, user=None):
        if password.isdigit():
            raise forms.ValidationError(
                _("Mật khẩu mới không được chỉ chứa số."),
                code="password_entirely_numeric",
            )
        
class CustomMinimumLengthValidator(MinimumLengthValidator):
    def validate(self, password, user=None):
        if len(password) < self.min_length:
            raise forms.ValidationError(
                ngettext(
                    "Mật khẩu mới quá ngắn. Nó phải chứa ít nhất "
                    "%(min_length)d ký tự",
                    "Mật khẩu mới quá ngắn. Nó phải chứa ít nhất "
                    "%(min_length)d ký tự.",
                    self.min_length,
                ),
                code="password_too_short",
                params={"min_length": self.min_length},
            )

def render_to_mail(template_name, context):
    template = get_template(template_name)
    return template.render(context)

def signup(request):
    if request.method == 'POST':
        form = MyRegForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.is_active = False
            user.save()

            current_site = get_current_site(request)
            mail_subject = 'Đăng ký tài khoản.'
            to_email = form.cleaned_data.get('email')

            context = {
                'user': user,
                'domain': current_site.domain,
                'root_url': settings.ROOT_URL,  # current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'token': account_activation_token.make_token(user),
            }

            message = render_to_mail('acc_activate_mail.html', context)

            email = EmailMessage(
                mail_subject, message, to=[to_email], from_email=settings.EMAIL_HOST_USER
            )
            email.content_subtype = "html"  # If you want to send HTML email

            email.send()
            return HttpResponseRedirect('/accounts/signup/completed')
    else:
        form = MyRegForm()
    return render(request, 'signup.html', {'form': form})


def completed(request):
    return render(request, "completed.html", {})


def activate(request, uidb64, token):
    try:
        uid = force_bytes(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return HttpResponseRedirect('/accounts')
    else:
        return HttpResponse('Activation link is invalid!')

