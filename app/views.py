from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404
from django.contrib import messages
from django.utils import timezone
from django.db.models import Sum, Avg  # ← Nueva importación
from .models import Cliente
from .marca_agua import aplicar_marca_agua
from django.core.files.base import ContentFile

def subir_cliente(request):
    if request.method == 'POST':
        razon_social = request.POST.get('razon_social')
        email = request.POST.get('email')
        archivo = request.FILES.get('archivo')

        if archivo and archivo.name.endswith('.pdf'):
            pdf_original = archivo.read()

            texto_marca = f"DELBA S.R.L."
            pdf_con_marca = aplicar_marca_agua(pdf_original, texto_marca)

            cliente = Cliente(
                razon_social=razon_social,
                email=email,
            )
            cliente.archivos_asociados.save(
                archivo.name,
                ContentFile(pdf_con_marca),
                save=True
            )

            link_completo = request.build_absolute_uri(f'/ver/{cliente.token}/')

            return render(request, 'ver_link.html', {
                'cliente': cliente,
                'link_completo': link_completo
            })
        else:
            messages.error(request, 'Solo se permiten archivos PDF')

    return render(request, 'subir_cliente.html')

def ver_pdf_cliente(request, token):
    """Vista que muestra el PDF sin permitir descarga fácil"""
    cliente = get_object_or_404(Cliente, token=token)

    # REGISTRO DE VISUALIZACIÓN
    if not request.GET.get('raw'):
        cliente.contador_visualizaciones += 1
        cliente.ultima_visualizacion = timezone.now()
        cliente.save()

        print(f"[{timezone.now()}] Cliente: {cliente.razon_social} - Visualizaciones: {cliente.contador_visualizaciones}")

    # Si es una petición para el PDF raw (para el visor)
    if request.GET.get('raw') == 'true':
        if not cliente.archivos_asociados:
            raise Http404("No hay archivo asociado")

        try:
            with cliente.archivos_asociados.open('rb') as pdf_file:
                pdf_content = pdf_file.read()
        except Exception as e:
            raise Http404("Error al leer el archivo")

        response = HttpResponse(pdf_content, content_type='application/pdf')

        if cliente.habilitar_descarga:
            response['Content-Disposition'] = f'attachment; filename="{cliente.razon_social}.pdf"'
        else:
            response['Content-Disposition'] = 'inline'
            response['Cache-Control'] = 'no-store, private, no-cache, must-revalidate'
            response['Pragma'] = 'no-cache'

        return response

    # Si no, mostrar el visor HTML
    return render(request, 'visor_pdf.html', {'cliente': cliente})

# ============================================
# NUEVA FUNCIÓN DASHBOARD
# ============================================
def dashboard(request):
    clientes = Cliente.objects.all().order_by('-fecha_creacion')

    # Calcular estadísticas
    total_clientes = Cliente.objects.count()
    total_visualizaciones = Cliente.objects.aggregate(Sum('contador_visualizaciones'))['contador_visualizaciones__sum'] or 0
    vistos_hoy = Cliente.objects.filter(ultima_visualizacion__date=timezone.now().date()).count()
    promedio_visitas = Cliente.objects.aggregate(Avg('contador_visualizaciones'))['contador_visualizaciones__avg'] or 0

    return render(request, 'dashboard.html', {
        'clientes': clientes,
        'total_clientes': total_clientes,
        'total_visualizaciones': total_visualizaciones,
        'vistos_hoy': vistos_hoy,
        'promedio_visitas': promedio_visitas,
        'ahora': timezone.now(),
    })
