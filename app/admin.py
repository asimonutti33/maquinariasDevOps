from django.contrib import admin
from .models import Cliente
from unfold.admin import ModelAdmin

@admin.register(Cliente)
class ClienteAdmin(ModelAdmin):
    list_display = ['razon_social', 'email', 'habilitar_descarga', 'contador_visualizaciones', 'ultima_visualizacion', 'fecha_creacion']
    list_editable = ['habilitar_descarga']
    readonly_fields = ['token', 'contador_visualizaciones', 'ultima_visualizacion', 'fecha_creacion']
    search_fields = ['razon_social', 'email']
    

    
    # Ordenar por más reciente primero
    ordering = ['-fecha_creacion']
