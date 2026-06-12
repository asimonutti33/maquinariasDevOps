from django.contrib import admin
from django.urls import path, include  # ← Agregar 'include'
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.db import connections
from django.db.utils import OperationalError
from app.views import subir_cliente, ver_pdf_cliente, dashboard

def health_check(request):
    # Verificar BD
    db_conn = connections['default']
    try:
        db_conn.cursor()
        db_status = "ok"
    except OperationalError:
        db_status = "error"
    
    return JsonResponse({
        "status": "healthy" if db_status == "ok" else "unhealthy",
        "database": db_status
    })

def ready_check(request):
    return JsonResponse({"status": "ready"})


urlpatterns = [
    path('admin/', admin.site.urls),
    path('', subir_cliente, name='subir'),
    path('dashboard/', dashboard, name='dashboard'),
    path('ver/<uuid:token>/', ver_pdf_cliente, name='ver_pdf_cliente'),
    path('health/', health_check, name='health'),
    path('ready/', ready_check, name='ready'),
    path('', include('django_prometheus.urls')),
    
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

