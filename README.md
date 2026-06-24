# Maquinarias DevOps

Sistema desarrollado en Django que permite a creadores de contenido subir documentos PDF, aplicarles automáticamente una **marca de agua** (texto + logo), y compartirlos con clientes mediante enlaces únicos protegidos por token UUID.

**El objetivo principal es proteger la propiedad intelectual del creador**, evitando que los documentos sean descargados, copiados o reproducidos sin autorización. El sistema garantiza que el cliente solo pueda **visualizar** el contenido, no poseerlo.

### 🎯 Funcionalidades clave

- **Subida de PDFs** con marca de agua automática (texto y logo)
- **Enlace único por token UUID** para cada cliente
- **Visor protegido** que bloquea descarga, impresión.
- **Panel de administración** con interfaz moderna (Unfold)
- **Dashboard de uso** con estadísticas de visualizaciones
- **Observabilidad** con Prometheus + Grafana (4 Golden Signals)

Proyecto Final — Bootcamp DevOps · Código Facilito (Opción 3, Proyecto Libre).

---

## Índice

- [Arquitectura](#arquitectura)
- [Stack tecnológico](#stack-tecnológico)
- [Cómo correrlo en local](#cómo-correrlo-en-local)
- [Cómo correrlo en Kubernetes (Minikube)](#cómo-correrlo-en-kubernetes-minikube)
- [CI/CD](#cicd)
- [Observabilidad](#observabilidad)
- [Seguridad](#seguridad)
- [Decisiones técnicas](#decisiones-técnicas)
- [Estructura del repositorio](#estructura-del-repositorio)

---

## Arquitectura

```
                         ┌─────────────────┐
                         │     Cliente      │
                         │   (navegador)    │
                         └────────┬─────────┘
                                  │
                                  ▼
                    ┌─────────────────────────┐
                    │   Django + Gunicorn      │
                    │   (whitenoise + static)  │
                    └────────────┬─────────────┘
                                 │
                  ┌──────────────┼──────────────┐
                  ▼              ▼              ▼
          ┌───────────┐  ┌─────────────┐  ┌──────────────┐
          │ PostgreSQL │  │  /metrics    │  │  Media (PVC) │
          │   (datos)  │  │ (prometheus) │  │ (PDFs subidos)│
          └───────────┘  └──────┬───────┘  └──────────────┘
                                 │
                                 ▼
                          ┌─────────────┐
                          │  Prometheus  │
                          └──────┬───────┘
                                 │
                                 ▼
                          ┌─────────────┐
                          │   Grafana    │
                          │ (dashboards) │
                          └─────────────┘
```

La app expone dos endpoints de salud (`/health/` y `/ready/`) que se reutilizan como `livenessProbe` y `readinessProbe` en Kubernetes, y un endpoint `/metrics` (vía `django-prometheus`) que Prometheus scrapea cada 15 segundos.

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Backend | Python 3.12 + Django 6.0 |
| Servidor WSGI | Gunicorn |
| Base de datos | PostgreSQL 16 |
| Archivos estáticos | WhiteNoise |
| Panel de administración | django-unfold |
| Generación/edición de PDF | ReportLab + pypdf |
| Contenedores | Docker (build multi-stage) |
| Orquestación | Kubernetes (probado en Minikube) |
| CI/CD | GitHub Actions |
| Registry | Docker Hub |
| Observabilidad | django-prometheus + Prometheus + Grafana |
| Escaneo de seguridad | Trivy + pip-audit |

---

## Cómo correrlo en local

### Requisitos
- Docker y Docker Compose instalados

### Pasos

```bash
git clone https://github.com/asimonutti33/maquinariasDevOps.git
cd maquinariasDevOps

cp .env.example .env
# Editar .env con tus propios valores (SECRET_KEY, passwords, etc.)

docker compose up --build
```

Al iniciar, el contenedor de Django ejecuta automáticamente (vía `entrypoint.sh`):
1. Espera a que PostgreSQL esté disponible
2. `makemigrations` + `migrate`
3. Crea un superusuario si no existe (usando las variables `DJANGO_SUPERUSER_*` del `.env`)
4. Levanta Gunicorn

### Accesos

| Servicio | URL |
|---|---|
| Aplicación | http://localhost:8000 |
| Panel de administración | http://localhost:8000/admin/ |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3000 (usuario/clave definidos en `.env`) |

El dashboard **"Maquinarias DevOps - Golden Signals"** se provisiona automáticamente en Grafana al arrancar — no requiere configuración manual.

### Detener

```bash
docker compose down          # conserva los datos
docker compose down -v       # borra también los volúmenes (DB, media, métricas)
```

---

## Cómo correrlo en Kubernetes (Minikube)

### Requisitos
- Minikube instalado y corriendo
- kubectl configurado

### Pasos

```bash
minikube start --cpus=4 --memory=4096 --driver=docker

# Construir la imagen DENTRO del Docker de Minikube
eval $(minikube docker-env)
docker build -t maquinarias-web:latest .

# Namespace
kubectl apply -f k8s/namespace.yaml

# Secret (generar con valores propios, NO usar el template tal cual)
kubectl create secret generic django-secret \
  --namespace=maquinarias \
  --from-literal=SECRET_KEY="$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')" \
  --from-literal=DB_USER='postgres' \
  --from-literal=DB_PASSWORD='tu-password-segura' \
  --from-literal=DJANGO_SUPERUSER_PASSWORD='tu-password-admin' \
  --from-literal=GRAFANA_USER='admin' \
  --from-literal=GRAFANA_PASSWORD='tu-password-grafana'

# Resto de los manifiestos
kubectl apply -f k8s/

# URLs de acceso
minikube service django-service -n maquinarias --url
minikube service grafana-service -n maquinarias --url
```

### Verificación

```bash
kubectl get pods -n maquinarias
kubectl get pvc -n maquinarias
kubectl logs -n maquinarias deployment/django-deployment
```

### Componentes desplegados

| Recurso | Tipo | Notas |
|---|---|---|
| `django-deployment` | Deployment | 1 réplica, con `initContainer` que espera a Postgres |
| `postgres-deployment` | Deployment | `strategy: Recreate` (PVC ReadWriteOnce) |
| `prometheus-deployment` | Deployment | Config vía ConfigMap, PVC propio |
| `grafana-deployment` | Deployment | Datasource y dashboard provisionados vía ConfigMaps |
| `django-service` | Service NodePort | Puerto 30080 |
| `grafana-service` | Service NodePort | Puerto 30030 |
| `postgres-service` | Service ClusterIP | Solo accesible dentro del clúster |
| `media-pvc`, `postgres-pvc`, `prometheus-pvc`, `grafana-pvc` | PersistentVolumeClaim | Persistencia de datos, métricas y dashboards |

---

## CI/CD

Pipeline en GitHub Actions (`.github/workflows/ci-cd.yml`), con 4 jobs encadenados:

```
build  →  test  →  scan  →  deploy
            │        │
            └────┬───┘
            (en paralelo, ambos dependen de build)
```

| Job | Qué hace |
|---|---|
| **build** | Construye la imagen Docker una sola vez y la pasa como artifact a los siguientes jobs |
| **test** | `flake8` (estilo) + `manage.py check` + `manage.py makemigrations --check` |
| **scan** | Escaneo de la imagen con **Trivy** + auditoría de dependencias con **pip-audit** |
| **deploy** | Publica en Docker Hub con tags `latest`, `sha-<hash>` y `v1.0.<run_number>` — **solo en push a `main`** |

Imagen publicada: [`ales33/maquinarias-devops`](https://hub.docker.com/r/ales33/maquinarias-devops)

```bash
docker pull ales33/maquinarias-devops:latest
```

Se dispara automáticamente con cada push o Pull Request a `main`/`develop`. Ver configuración de secrets necesarios en `.github/workflows/SECRETS_SETUP.md`.

> **Nota:** el proyecto todavía no cuenta con tests unitarios (pytest/unittest); el job `test` corre las validaciones nativas de Django mientras tanto. Queda como mejora pendiente.

---

## Observabilidad

Dashboard con los 4 Golden Signals, provisionado automáticamente en Grafana (sin configuración manual) tanto en Docker Compose como en Kubernetes:

| Señal | Métrica |
|---|---|
| Latencia (p95) | `django_http_requests_latency_seconds_by_view_method` |
| Tráfico (req/s) | `django_http_requests_total_by_view_transport_method` |
| Errores (tasa 4xx/5xx) | `django_http_responses_total_by_status_view_method` |
| Saturación (CPU/memoria) | `process_cpu_seconds_total`, `process_resident_memory_bytes` |

Archivos de configuración en `monitoring/` (Compose) y como ConfigMaps en `k8s/` (Kubernetes), ambos usando el mismo `golden-signals.json` como fuente única.

---

## Seguridad

Prácticas de DevSecOps aplicadas:

- **Escaneo de imágenes:** Trivy corre en cada ejecución del pipeline, reportando vulnerabilidades `CRITICAL`/`HIGH` de la imagen final.
- **Secrets fuera del repo:** ninguna credencial (passwords, `SECRET_KEY`, tokens) está hardcodeada ni commiteada. En local viven en `.env` (no versionado, ver `.env.example`); en Kubernetes se generan vía `kubectl create secret`; en CI/CD viven como GitHub Secrets.
- **Dependencias actualizadas:** `pip-audit` corre sobre `requirements.txt` en cada ejecución del pipeline.
- El contenedor de la app corre con un usuario no-root (`appuser`).

---

## Decisiones técnicas

- **Docker multi-stage:** el build se compila en una etapa (`builder`, con `gcc`/`libpq-dev` para psycopg2 y Pillow) y se ejecuta en otra limpia (`runtime`), evitando exponer herramientas de compilación en la imagen final.
- **`entrypoint.sh` en vez de `RUN` en el Dockerfile:** las migraciones y la creación del superusuario necesitan una base de datos disponible, que no existe en tiempo de build. Se resolvió con un script de entrypoint que corre en tiempo de arranque del contenedor.
- **PVC `ReadWriteOnce` + `strategy: Recreate`** en los Deployments con estado (Postgres, Prometheus, Grafana): evita que dos pods escriban simultáneamente al mismo volumen durante un rolling update.
- **Reutilización de `/health/` y `/ready/`** como probes de Kubernetes, en vez de crear endpoints nuevos solo para eso.
- **Provisioning de Grafana como código:** datasource y dashboard se definen en archivos versionados (YAML/JSON), no se configuran a mano desde la UI — así cualquiera que levante el proyecto obtiene el mismo resultado.
- **Pipeline de CI/CD sin tests unitarios reales (todavía):** en vez de simular un paso vacío, el job `test` corre las validaciones nativas que Django sí provee (`check`, `makemigrations --check`), documentado como limitación conocida.

---

## Estructura del repositorio

```
maquinariasDevOps/
├── app/                          # App principal de Django
├── delba/                        # Configuración del proyecto (settings, urls, wsgi)
├── monitoring/                   # Config de Prometheus + Grafana (Compose)
│   └── grafana/provisioning/
├── k8s/                          # Manifiestos de Kubernetes
├── .github/workflows/            # Pipeline de CI/CD
├── Dockerfile
├── docker-compose.yml
├── entrypoint.sh
├── requirements.txt
├── .env.example
└── README.md
```

---

## Autor

Proyecto desarrollado por [asimonutti33](https://github.com/asimonutti33) como Proyecto Final del Bootcamp DevOps de Código Facilito, edición 2026.
