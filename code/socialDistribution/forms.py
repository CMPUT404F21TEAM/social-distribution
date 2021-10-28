from django import forms
from django.forms import ModelForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django import forms
from .models import Post, Author, Category

class CreateUserForm(UserCreationForm):
    """
        Create User Form Configuration
    """
    class Meta: 
        model = User
        fields = ['username', 'email', 'password1', 'password2', 'first_name', 'last_name']

# MDN Web Docs, "Django Tutorial Part 9: Working with forms",
# https://developer.mozilla.org/en-US/docs/Learn/Server-side/Django/Forms, 2021-10-15, CC BY-SA 2.5
class PostForm(forms.Form):
    """
        Create Post Form Configuration
    """
    title = forms.CharField(max_length=Post.TITLE_MAXLEN, required=True)
    categories = forms.CharField(required=False)
    description = forms.CharField(max_length=Post.DESCRIPTION_MAXLEN, required=True)
    content_text = forms.CharField(
        max_length=Post.CONTEXT_TEXT_MAXLEN, 
        required=False,
        widget=forms.Textarea
    )
    
    content_media = forms.FileField(required=False)
    unlisted = forms.BooleanField(required=False)
    visibility = forms.ChoiceField(
        choices=Post.VISIBILITY_CHOICES, 
        required=True,
    )
    post_recipients = forms.ModelMultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            queryset=Author.objects.all(),
            label="Share with:"
        )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        postId = 0
        if 'postId' in kwargs:
            postId = kwargs.pop('postId')
        post = None
        if postId > 0:
            post = Post.objects.get(id=postId)
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['post_recipients'].queryset = Author.objects.all().exclude(id=user)
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
        data = self.cleaned_data['visibility']
        if data in [Post.FRIENDS, Post.PUBLIC, Post.PRIVATE]:
            return data
        else:
            raise ValidationError('Invalid visibility')