from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordChangeForm
from .models import CustomUser


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone_number = forms.CharField(required=True, max_length=20)

    class Meta:
        model = CustomUser
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'profile_photo',
            'password1',
            'password2'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].label = 'Имя пользователя'
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Username'
        })

        self.fields['first_name'].label = 'Имя'
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Ерсултан'
        })

        self.fields['last_name'].label = 'Фамилия'
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Абдрахманов'
        })

        self.fields['email'].label = 'Email'
        self.fields['email'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'example@mail.com'
        })

        self.fields['phone_number'].label = 'Телефон номер'
        self.fields['phone_number'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': '+7 777 777 77 77'
        })

        self.fields['profile_photo'].label = 'Фото профиля'
        self.fields['profile_photo'].widget = forms.FileInput(attrs={
            'class': 'form-file'
        })

        self.fields['password1'].label = 'Пароль'
        self.fields['password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': '********'
        })
        self.fields['password1'].help_text = 'Кемінде 8 символ.'

        self.fields['password2'].label = 'Подтверждение пароля'
        self.fields['password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': '********'
        })
        self.fields['password2'].help_text = 'Парольді қайта енгізіңіз.'


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'first_name', 'last_name', 'email', 'phone_number', 'bio', 'profile_photo']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].label = 'Имя пользователя'
        self.fields['username'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Username'
        })

        self.fields['first_name'].label = 'Имя'
        self.fields['first_name'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Ерсултан'
        })

        self.fields['last_name'].label = 'Фамилия'
        self.fields['last_name'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'Абдрахманов'
        })

        self.fields['email'].label = 'Email'
        self.fields['email'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': 'example@mail.com'
        })

        self.fields['phone_number'].label = 'Телефон номер'
        self.fields['phone_number'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': '+7 777 777 77 77'
        })

        self.fields['bio'].label = 'О себе'
        self.fields['bio'].widget.attrs.update({
            'class': 'form-textarea',
            'placeholder': 'Қысқаша өзіңіз туралы...'
        })

        self.fields['profile_photo'].label = 'Фото профиля'
        self.fields['profile_photo'].widget.attrs.update({
            'class': 'form-file'
        })


class CustomPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['old_password'].label = 'Ескі пароль'
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': '********'
        })

        self.fields['new_password1'].label = 'Жаңа пароль'
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': '********'
        })
        self.fields['new_password1'].help_text = 'Кемінде 8 символ.'

        self.fields['new_password2'].label = 'Қайта енгізу'
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-input',
            'placeholder': '********'
        })
        self.fields['new_password2'].help_text = 'Жаңа парольді қайта жазыңыз.'