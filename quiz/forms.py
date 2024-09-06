from django import forms

class QuizForm(forms.Form):
    prompt = forms.CharField(widget=forms.Textarea, label='Enter a prompt for quiz generation')
