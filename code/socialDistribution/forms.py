from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django import forms
from .models import LocalPost, LocalAuthor, Image
import base64

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

    TEXT = 'TEXT'
    IMAGE = 'IMAGE'
    forms_post_types = (
        (TEXT, 'Text or Markdown'),
        (IMAGE, 'Upload an Image')
    )

    post_type = forms.ChoiceField(
        choices=forms_post_types,
        required=True,
    )

    content_text = forms.CharField(
        max_length=LocalPost.CONTENT_MAXLEN, 
        required=False,
        widget=forms.Textarea
    )
    
    image = forms.FileField(required=False)
    unlisted = forms.BooleanField(required=False)
    visibility = forms.ChoiceField(
        choices=LocalPost.Visibility.choices, 
        required=True,
    )
    post_recipients = forms.ModelMultipleChoiceField(
            required=False,
            widget=forms.CheckboxSelectMultiple,
            queryset=LocalAuthor.objects.all(),
            label="Share with:"
        )

    def __init__(self, *args, **kwargs):
        user_id = kwargs.pop('user_id')
        post_id = 0
        if 'post_id' in kwargs:
            post_id = kwargs.pop('post_id')
        post = None
        if post_id > 0:
            post = LocalPost.objects.get(id=post_id)
        super(PostForm, self).__init__(*args, **kwargs)
        self.fields['post_recipients'].queryset = LocalAuthor.objects.all().exclude(id=user_id)
        if post:
            self.fields['title'].initial = post.title
            self.fields['description'].initial = post.description
            
            previousCategories = post.categories.all()
            previousCategoriesNames = " ".join([cat.category for cat in previousCategories])
            self.fields['categories'].initial = previousCategoriesNames
            
            if post.is_image_post():
                self.fields['post_type'].initial = self.IMAGE

            else:
                self.fields['post_type'].initial = self.TEXT
                self.fields['content_text'].initial = post.decoded_content
            
            self.fields['unlisted'].initial = post.unlisted
            self.fields['visibility'].initial = post.visibility
        
    # "Django - Get uploaded file type / mimetype", Last accessed on November 19, 2021
    # Authors: Hanpan, moskrc, Nathan Osman
    # https://stackoverflow.com/questions/4853581/django-get-uploaded-file-type-mimetype, CC BY-SA 2021
    def clean_image(self):
        """ Validates the file input """
        image = self.cleaned_data.get('image')
        content_type = None
        image_binary = b''

        if image:
            mime_type, subtype = image.content_type.split('/')
            if mime_type not in ['image', 'application']:
                raise forms.ValidationError('File type is not supported')
            
            subtype = subtype.upper()
            PNG = LocalPost.ContentType.PNG
            JPEG = LocalPost.ContentType.JPEG
            if subtype not in [PNG, JPEG]:
                raise forms.ValidationError('File format is not supported')

            content_type = subtype
            image_binary = image.read()

        return image, image_binary, content_type

    def clean_content_text(self):
        """ Validates the content text input and returns the value in binary """
        content_text = self.cleaned_data.get('content_text')
        if content_text:
            return content_text.encode('utf-8')
        else:
            return b''

    def clean_visibility(self):
        """
            Ensure post's visilibity is valid
        """
        data = self.cleaned_data['visibility']
        if data in [visibility[0] for visibility in LocalPost.Visibility.choices]:
            return data
        else:
            raise ValidationError('Invalid visibility')

    def get_content_and_type(self):
        """
            Gets the content type and the content of the submitted data
        """
        post_type = self.cleaned_data.get('post_type')
        image, image_binary, content_type = self.cleaned_data.get('image')
        
        # Upload image to media folder and base64-
        # encode the data to store in database
        if post_type == PostForm.IMAGE and image:
            Image.objects.create(
                caption=self.cleaned_data.get('description'),
                image=image
            )

            content = base64.b64encode(image_binary)

        else:
            content_type = LocalPost.ContentType.PLAIN
            content = base64.b64encode(self.cleaned_data.get('content_text'))

        return content, content_type