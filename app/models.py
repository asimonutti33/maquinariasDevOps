import uuid

from django.db import models


class Cliente(models.Model):
    razon_social = models.CharField(max_length=200)
    email = models.EmailField()
    archivos_asociados = models.FileField(upload_to='documentos/')
    habilitar_descarga = models.BooleanField(default=False)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    # Campos para registro de visualizaciones
    contador_visualizaciones = models.IntegerField(default=0)
    ultima_visualizacion = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.razon_social
