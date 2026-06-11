from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from app.views import subir_cliente, ver_pdf_cliente, dashboard  # ← Importa dashboard

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', subir_cliente, name='subir'),
    path('dashboard/', dashboard, name='dashboard'),  # ← Agrega esta línea
    path('ver/<uuid:token>/', ver_pdf_cliente, name='ver_pdf_cliente'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

