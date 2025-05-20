from django import template
from workspace.models import Workspace

register = template.Library()

@register.filter
def get_workspace_name(workspaces, ws_id):
    ws = workspaces.filter(id=ws_id).first()
    return ws.name if ws else "Inconnu"