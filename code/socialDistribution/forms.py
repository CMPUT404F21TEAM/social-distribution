from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django import forms
from .models import Post

class CreateUserForm(UserCreationForm):
    """
        Create User Form Configuration
    """
    class Meta: 
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']


class PostForm(forms.Form):
    """
        Create Post Form Configuration
    """
    title = forms.CharField(max_length=Post.TITLE_MAXLEN, required=True)
    categories = forms.CharField(required=False)
    description = forms.CharField(max_length=Post.DESCRIPTION_MAXLEN, required=True)
    content_text = forms.CharField(max_length=Post.CONTEXT_TEXT_MAXLEN, required=False)
    content_media = forms.FileField(required=False)
    unlisted = forms.BooleanField(required=False)
    visibility = forms.ChoiceField(
        choices=Post.VISIBILITY_CHOICES, 
        required=True,
    )

    def clean_visibility(self):
        data = self.cleaned_data['visibility']
        if data in [Post.FRIENDS, Post.PUBLIC]:
            return data
        else:
            raise ValidationError('Invalid visibility')