from django import forms
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError

class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].error_messages['invalid'] = 'Mật khẩu cũ không đúng.'
        self.fields['new_password1'].error_messages['password_mismatch'] = 'Mật khẩu mới không khớp.'
        self.fields['new_password2'].error_messages['password_mismatch'] = 'Mật khẩu mới không khớp.'

    def clean_new_password1(self):
        new_password1 = self.cleaned_data.get('new_password1')
        if self.user.check_password(new_password1):
            raise ValidationError("Mật khẩu mới không được giống với mật khẩu hiện tại.")
        return new_password1

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise forms.ValidationError(
                self.fields['old_password'].error_messages['invalid'],
                code='invalid',
            )
        return old_password
