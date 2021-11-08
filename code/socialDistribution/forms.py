from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django import forms
from .models import LocalPost, LocalAuthor, Category

class CreateUserForm(UserCreationForm):
    """
        Create User Form Configuration
    """
    # ref: https://stackoverflow.com/questions/48049498/django-usercreationform-custom-fields - Chirdeep Tomar
    username = forms.CharField(widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username...'}))
    display_name = forms.CharField(max_length=50, widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name...', 'required': 'True'}))
    email = forms.EmailField(widget = forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email...'}))
    password1 = forms.CharField(widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password...'}))
    password2 = forms.CharField(widget = forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Re-enter Password...'}))
    github_url = forms.URLField(max_length=50, required = False, widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Github URL...'}))
    profile_image_url = forms.URLField(max_length=50, required = False, widget = forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Profile Image URL...'}))

    class Meta: 
        model = User
        fields = ['username', 'display_name', 'email', 'password1', 'password2', 'github_url', 'profile_image_url']

# MDN Web Docs, "Django Tutorial Part 9: Working with forms",
# https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Forms, 2021-10-15, CC BY-SA 2.5
class PostForm(forms.Form):
    """
        Create Post Form Configuration
    """
    title = forms.CharField(max_length=LocalPost.TITLE_MAXLEN, required=True)
    categories = forms.CharField(required=False)
    description = forms.CharField(max_length=LocalPost.DESCRIPTION_MAXLEN, required=True)
    content_text = forms.CharField(
        max_length=LocalPost.CONTEXT_TEXT_MAXLEN, 
        required=False,
        widget=forms.Textarea
    )
    
    content_media = forms.FileField(required=False)
    unlisted = forms.BooleanField(required=False)
    visibility = forms.ChoiceField(
        choices=LocalPost.VISIBILITY_CHOICES, 
        required=True,
    )
    post_recipients = forms.ModelMultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            queryset=LocalAuthor.objects.all(),
            label="Share with:"
        )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        postId = 0
        if 'postId' in kwargs:
            postId = kwargs.pop('postId')
        post = None
        if postId > 0:
            post = LocalPost.objects.get(id=postId)
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['post_recipients'].queryset = LocalAuthor.objects.all().exclude(id=user)
        if post:
            self.fields['title'].initial = post.title
            self.fields['description'].initial = post.description
            
            previousCategories = Category.objects.filter(post=post)
            previousCategoriesNames = " ".join([cat.category for cat in previousCategories])
            self.fields['categories'].initial = previousCategoriesNames
            
            self.fields['content_text'].initial = post.content_text
            
            self.fields['content_media'].initial = post.content_media
            self.fields['unlisted'].initial = post.unlisted
            self.fields['visibility'].initial = post.visibility
        
    def clean_visibility(self):
        """
            Ensure post's visilibity is valid
        """
        data = self.cleaned_data['visibility']
        if data in [LocalPost.FRIENDS, LocalPost.PUBLIC, LocalPost.PRIVATE]:
            return data
        else:
            raise ValidationError('Invalid visibility')