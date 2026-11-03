from django.contrib.auth.forms import UserCreationForm

from .models import User


class SellerRegisterForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = User.Role.SELLER
        if commit:
            user.save()
            self.save_m2m()
        return user


class RiderCreateForm(SellerRegisterForm):
    def save(self, commit=True):
        user = super(SellerRegisterForm, self).save(commit=False)
        user.role = User.Role.RIDER
        if commit:
            user.save()
            self.save_m2m()
        return user
