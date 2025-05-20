from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from utilisateurs.forms import EmailAdminAuthenticationForm
from .models import Utilisateur

# Formulaire de création (admin)
class UtilisateurCreationForm(forms.ModelForm):
    password1 = forms.CharField(label='Mot de passe', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmer le mot de passe', widget=forms.PasswordInput)

    class Meta:
        model = Utilisateur
        fields = ('email', 'username', 'nom', 'prenom', 'role', 'niveau')

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user

# Formulaire de modification (admin)
class UtilisateurChangeForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = '__all__'

# Configuration de l’admin
class UtilisateurAdmin(UserAdmin):
    form = UtilisateurChangeForm
    add_form = UtilisateurCreationForm
    model = Utilisateur

    list_display = ('email', 'username', 'nom', 'prenom', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'role')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informations personnelles', {'fields': ('username', 'nom', 'prenom', 'role', 'niveau')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'nom', 'prenom', 'role', 'niveau', 'password1', 'password2', 'is_staff', 'is_superuser'),
        }),
    )

    search_fields = ('email', 'username')
    ordering = ('email',)

admin.site.register(Utilisateur, UtilisateurAdmin)
admin.site.login_form = EmailAdminAuthenticationForm