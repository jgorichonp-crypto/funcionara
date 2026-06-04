# 🚀 Guía de Despliegue en Producción

## 📋 Pre-requisitos

Antes de desplegar en producción, asegúrate de tener:

- ✅ Cuenta de AWS (para Lambda/ECS) o servidor VPS
- ✅ API Keys de servicios externos:
  - OpenAI (GPT-4)
  - Stability AI (generación de imágenes)
  - Meta Business (publicidad)
  - Vercel/Netlify (deployment)
- ✅ Webhook configurado (Slack/Discord)
- ✅ Base de datos (PostgreSQL/MongoDB recomendado)

---

## 🐳 Opción 1: Docker (Recomendado)

### Paso 1: Crear Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código
COPY . .

# Variables de entorno (sobrescribir en runtime)
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Comando de inicio
CMD ["python", "main.py"]
```

### Paso 2: Crear docker-compose.yml

```yaml
version: '3.8'

services:
  dropshipping-automation:
    build: .
    container_name: dropshipping-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
    networks:
      - dropshipping-net

  # Opcional: Base de datos
  postgres:
    image: postgres:15-alpine
    container_name: dropshipping-db
    restart: unless-stopped
    environment:
      POSTGRES_DB: dropshipping
      POSTGRES_USER: admin
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - dropshipping-net

networks:
  dropshipping-net:
    driver: bridge

volumes:
  postgres_data:
```

### Paso 3: Construir y Ejecutar

```bash
# Construir imagen
docker build -t dropshipping-automation:latest .

# Ejecutar con docker-compose
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

---

## ☁️ Opción 2: AWS Lambda

### Paso 1: Crear handler para Lambda

```python
# lambda_handler.py
import asyncio
from main import main

def lambda_handler(event, context):
    """Handler para AWS Lambda"""
    try:
        # Ejecutar pipeline
        result = asyncio.run(main())
        
        return {
            'statusCode': 200,
            'body': {
                'message': 'Pipeline completado exitosamente',
                'product': result.product_name,
                'deployed_url': result.deployed_url,
                'campaign_id': result.instagram_ad_draft_id
            }
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': {
                'error': str(e)
            }
        }
```

### Paso 2: Crear requirements para Lambda

```txt
# requirements-lambda.txt
pydantic==2.9.2
pydantic-settings==2.6.1
aiohttp==3.11.10
python-dotenv==1.0.1
```

### Paso 3: Empaquetar para Lambda

```bash
# Crear directorio de deployment
mkdir lambda-package
cd lambda-package

# Instalar dependencias
pip install -r ../requirements-lambda.txt -t .

# Copiar código
cp -r ../agents .
cp ../config.py .
cp ../models.py .
cp ../main.py .
cp ../lambda_handler.py .

# Crear ZIP
zip -r ../dropshipping-lambda.zip .
```

### Paso 4: Desplegar en AWS

```bash
# Usando AWS CLI
aws lambda create-function \
  --function-name dropshipping-automation \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambda-execution-role \
  --handler lambda_handler.lambda_handler \
  --zip-file fileb://dropshipping-lambda.zip \
  --timeout 900 \
  --memory-size 512 \
  --environment Variables="{
    OPENAI_API_KEY=sk-xxx,
    META_ACCESS_TOKEN=EAAxx,
    VERCEL_TOKEN=xxx
  }"

# Configurar trigger (EventBridge para ejecución programada)
aws events put-rule \
  --name dropshipping-daily \
  --schedule-expression "cron(0 10 * * ? *)"  # Diario a las 10 AM UTC

aws events put-targets \
  --rule dropshipping-daily \
  --targets "Id"="1","Arn"="arn:aws:lambda:REGION:ACCOUNT:function:dropshipping-automation"
```

---

## 🖥️ Opción 3: VPS (DigitalOcean, Linode, etc.)

### Paso 1: Conectar al servidor

```bash
ssh root@your-server-ip
```

### Paso 2: Instalar dependencias

```bash
# Actualizar sistema
apt update && apt upgrade -y

# Instalar Python 3.11
apt install -y python3.11 python3.11-venv python3-pip git

# Instalar supervisor (para mantener proceso corriendo)
apt install -y supervisor
```

### Paso 3: Clonar proyecto

```bash
# Crear directorio
mkdir -p /opt/dropshipping
cd /opt/dropshipping

# Clonar código (o subir vía SCP)
git clone https://github.com/tu-usuario/dropshipping-automation.git .

# Crear entorno virtual
python3.11 -m venv venv
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### Paso 4: Configurar variables de entorno

```bash
# Crear archivo .env
nano .env

# Pegar configuración:
OPENAI_API_KEY=sk-xxx
META_ACCESS_TOKEN=EAAxx
VERCEL_TOKEN=xxx
# ... resto de variables
```

### Paso 5: Configurar Supervisor

```bash
# Crear configuración
nano /etc/supervisor/conf.d/dropshipping.conf
```

```ini
[program:dropshipping]
command=/opt/dropshipping/venv/bin/python /opt/dropshipping/main.py
directory=/opt/dropshipping
user=root
autostart=true
autorestart=true
stderr_logfile=/var/log/dropshipping/error.log
stdout_logfile=/var/log/dropshipping/output.log
environment=PATH="/opt/dropshipping/venv/bin"
```

```bash
# Crear directorio de logs
mkdir -p /var/log/dropshipping

# Recargar supervisor
supervisorctl reread
supervisorctl update
supervisorctl start dropshipping

# Ver status
supervisorctl status dropshipping

# Ver logs
tail -f /var/log/dropshipping/output.log
```

### Paso 6: Configurar Cron (Ejecución Programada)

```bash
# Editar crontab
crontab -e

# Agregar línea (ejecutar diario a las 10 AM)
0 10 * * * cd /opt/dropshipping && /opt/dropshipping/venv/bin/python main.py >> /var/log/dropshipping/cron.log 2>&1
```

---

## 🔐 Seguridad en Producción

### 1. Secrets Management

**AWS Secrets Manager:**
```python
# config.py (modificado)
import boto3
import json

def get_secret(secret_name):
    client = boto3.client('secretsmanager', region_name='us-east-1')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Cargar secrets
secrets = get_secret('dropshipping/production')
settings.openai_api_key = secrets['OPENAI_API_KEY']
```

**HashiCorp Vault:**
```python
import hvac

client = hvac.Client(url='http://vault:8200', token='your-token')
secrets = client.secrets.kv.v2.read_secret_version(path='dropshipping')
```

### 2. Firewall

```bash
# UFW (Ubuntu)
ufw allow 22/tcp  # SSH
ufw allow 443/tcp # HTTPS (si tienes API)
ufw enable
```

### 3. SSL/TLS

Si expones una API:
```bash
# Instalar Certbot
apt install -y certbot python3-certbot-nginx

# Obtener certificado
certbot --nginx -d api.tudominio.com
```

---

## 📊 Monitoreo

### 1. Sentry (Errores)

```python
# main.py (agregar al inicio)
import sentry_sdk

sentry_sdk.init(
    dsn="https://xxx@sentry.io/xxx",
    traces_sample_rate=1.0,
    environment="production"
)
```

### 2. Prometheus + Grafana

```python
# metrics.py
from prometheus_client import Counter, Histogram, start_http_server

pipeline_runs = Counter('pipeline_runs_total', 'Total pipeline runs')
pipeline_duration = Histogram('pipeline_duration_seconds', 'Pipeline duration')
pipeline_errors = Counter('pipeline_errors_total', 'Total pipeline errors')

# En main.py
from metrics import pipeline_runs, pipeline_duration, pipeline_errors

@pipeline_duration.time()
async def main():
    pipeline_runs.inc()
    try:
        # ... código existente
        pass
    except Exception as e:
        pipeline_errors.inc()
        raise
```

### 3. CloudWatch (AWS)

```python
import boto3

cloudwatch = boto3.client('cloudwatch')

def send_metric(metric_name, value):
    cloudwatch.put_metric_data(
        Namespace='Dropshipping',
        MetricData=[
            {
                'MetricName': metric_name,
                'Value': value,
                'Unit': 'Count'
            }
        ]
    )
```

---

## 🔄 CI/CD

### GitHub Actions

```yaml
# .github/workflows/deploy.yml
name: Deploy to Production

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run tests
        run: |
          pytest
      
      - name: Build Docker image
        run: |
          docker build -t dropshipping:${{ github.sha }} .
      
      - name: Push to registry
        run: |
          docker push dropshipping:${{ github.sha }}
      
      - name: Deploy to server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.SERVER_HOST }}
          username: ${{ secrets.SERVER_USER }}
          key: ${{ secrets.SSH_KEY }}
          script: |
            cd /opt/dropshipping
            docker pull dropshipping:${{ github.sha }}
            docker-compose up -d
```

---

## 📈 Escalabilidad

### Horizontal Scaling con Kubernetes

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dropshipping-automation
spec:
  replicas: 3
  selector:
    matchLabels:
      app: dropshipping
  template:
    metadata:
      labels:
        app: dropshipping
    spec:
      containers:
      - name: dropshipping
        image: dropshipping:latest
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: dropshipping-secrets
              key: openai-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
```

---

## 🧪 Testing en Producción

### Smoke Tests

```bash
# smoke-test.sh
#!/bin/bash

echo "Running smoke tests..."

# Test 1: Verificar que el sistema responde
python verify.py
if [ $? -ne 0 ]; then
    echo "❌ Verification failed"
    exit 1
fi

# Test 2: Ejecutar pipeline con producto de prueba
LOG_LEVEL=ERROR python main.py
if [ $? -ne 0 ]; then
    echo "❌ Pipeline failed"
    exit 1
fi

echo "✅ All smoke tests passed"
```

---

## 📞 Soporte Post-Deployment

### Comandos Útiles

```bash
# Ver logs en tiempo real
tail -f /var/log/dropshipping/output.log

# Reiniciar servicio
supervisorctl restart dropshipping

# Ver status
supervisorctl status

# Ver métricas de sistema
htop

# Ver uso de disco
df -h

# Ver procesos Python
ps aux | grep python
```

### Troubleshooting

```bash
# Si el servicio no inicia
supervisorctl tail dropshipping stderr

# Si hay problemas de permisos
chown -R root:root /opt/dropshipping

# Si hay problemas de memoria
free -h
```

---

## ✅ Checklist de Deployment

- [ ] Configurar todas las API keys en `.env`
- [ ] Configurar webhook de alertas
- [ ] Configurar base de datos (si aplica)
- [ ] Configurar monitoreo (Sentry/CloudWatch)
- [ ] Configurar backups automáticos
- [ ] Configurar SSL/TLS (si expones API)
- [ ] Configurar firewall
- [ ] Configurar logs rotation
- [ ] Configurar alertas de errores
- [ ] Documentar procedimientos de rollback
- [ ] Realizar smoke tests
- [ ] Configurar CI/CD
- [ ] Configurar auto-scaling (si aplica)

---

**¡Listo para producción! 🚀**

Para más información, consulta [README.md](README.md) y [ARCHITECTURE.md](ARCHITECTURE.md).
