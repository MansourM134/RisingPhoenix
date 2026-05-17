from django import forms

from rising_phoenix.moderation import text_is_clean


class ProgressCommentForm(forms.Form):
    body = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'progress-textarea progress-textarea--comment',
            'placeholder': 'Leave feedback or ask a question...',
            'rows': 3,
        }),
        max_length=1000,
    )

    def clean_body(self):
        value = self.cleaned_data.get('body', '')
        if value and not text_is_clean(value):
            raise forms.ValidationError('Your comment contains inappropriate language. Please revise it.')
        return value
