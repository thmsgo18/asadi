from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.documents, name='documents'),
    path('delete/<int:doc_id>/', views.delete_document, name='delete_document'),
    path('delete-workspace/', views.delete_workspace, name='delete_workspace'),
]