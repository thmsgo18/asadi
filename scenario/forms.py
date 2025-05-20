from django import forms
from .models import Scenario, QuestionReponse

class ScenarioForm(forms.ModelForm):
    contexte_utilisateur = forms.CharField(widget=forms.Textarea(attrs={
        'class': 'input-rounded',
        'placeholder': 'Décrivez brièvement le contexte du scénario...',
        'rows': 3
    }))
    
    class Meta:
        model = Scenario
        fields = []  # Nous n'utilisons aucun champ du modèle directement

class QuestionReponseForm(forms.ModelForm):
    class Meta:
        model = QuestionReponse
        fields = ['question', 'reponse']
        widgets = {
            'question': forms.Textarea(attrs={
                'class': 'input-rounded',
                'placeholder': 'Question',
                'rows': 2
            }),
            'reponse': forms.Textarea(attrs={
                'class': 'input-rounded',
                'placeholder': 'Réponse',
                'rows': 2
            }),
        }
