from django import forms
from .models import ReviewRating

class ReviewForm(forms.ModelForm):
    class Meta:
        model = ReviewRating
        fields = ['subject', 'rating', 'review']

    def __init__(self, *args, **kwargs):
        super(ReviewForm, self).__init__(*args, **kwargs)
        self.fields['subject'].widget.attrs['class'] = 'form-control'
        self.fields['subject'].widget.attrs['placeholder'] = 'Review Subject'
        self.fields['review'].widget.attrs['class'] = 'form-control'
        self.fields['review'].widget.attrs['placeholder'] = 'Write your review'
        self.fields['rating'].widget.attrs['class'] = 'form-control'