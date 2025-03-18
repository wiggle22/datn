from django import forms
from .models import Customer
from .models import Reservation
from datetime import datetime

class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['full_name', 'vehicle_number', 'contact_number']



class ReservationForm(forms.ModelForm):
    class Meta:
        model = Reservation
        fields = ['reserved_from', 'reserved_to', 'spot']
        widgets = {
            'reserved_from': forms.TimeInput(attrs={'type': 'time'}),
            'reserved_to': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def __init__(self, *args, **kwargs):
        lot = kwargs.pop('lot', None)
        super().__init__(*args, **kwargs)
        if lot:
            self.fields['spot'].queryset = lot.spots.filter(is_reserved=False)
        self.fields['spot'].widget = forms.HiddenInput()  # Ẩn trường spot

    def clean_spot(self):
        spot = self.cleaned_data.get('spot')
        if not spot:
            raise forms.ValidationError("Vui lòng chọn một vị trí đỗ xe.")
        return spot