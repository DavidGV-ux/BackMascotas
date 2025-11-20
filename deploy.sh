#!/bin/bash
# Script de despliegue para Linux/Mac
# Uso: ./deploy.sh [dev|production]

STAGE=${1:-dev}

echo "🚀 Iniciando despliegue en AWS Lambda (Zappa) - Stage: $STAGE"

# Verificar que estamos en el directorio correcto
if [ ! -f "zappa_settings.json" ]; then
    echo "❌ Error: zappa_settings.json no encontrado. Ejecuta este script desde la raíz del proyecto."
    exit 1
fi

# Verificar que el entorno virtual existe
if [ ! -f "venv/bin/activate" ]; then
    echo "⚠️  Advertencia: Entorno virtual no encontrado. Creando..."
    python3 -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
else
    echo "✅ Activando entorno virtual..."
    source venv/bin/activate
fi

# Verificar que Zappa está instalado
if ! pip show zappa > /dev/null 2>&1; then
    echo "📦 Instalando Zappa..."
    pip install zappa
fi

# Verificar credenciales de AWS
echo "🔐 Verificando credenciales de AWS..."
if ! aws configure list > /dev/null 2>&1; then
    echo "⚠️  Advertencia: AWS CLI no configurado. Ejecuta 'aws configure' primero."
    echo "   O configura las variables de entorno AWS_ACCESS_KEY_ID y AWS_SECRET_ACCESS_KEY"
fi

# Confirmación para producción
if [ "$STAGE" = "production" ]; then
    echo "⚠️  ATENCIÓN: Estás desplegando a PRODUCCIÓN"
    read -p "¿Continuar? (s/N): " confirm
    if [ "$confirm" != "s" ] && [ "$confirm" != "S" ]; then
        echo "❌ Despliegue cancelado"
        exit 0
    fi
fi

# Desplegar
echo ""
echo "🚀 Desplegando a AWS Lambda..."
echo "   Stage: $STAGE"
echo "   Esto puede tardar varios minutos..."
echo ""

# Intentar actualizar primero (si ya existe)
echo "🔄 Intentando actualizar despliegue existente..."
if zappa update $STAGE 2>&1; then
    echo ""
    echo "✅ Actualización completada exitosamente!"
else
    # Si falla, intentar deploy nuevo
    echo ""
    echo "📦 Despliegue no existe, creando nuevo..."
    if zappa deploy $STAGE 2>&1; then
        echo ""
        echo "✅ Despliegue completado exitosamente!"
    else
        echo ""
        echo "❌ Error en el despliegue"
        exit 1
    fi
fi

# Mostrar estado
echo ""
echo "📊 Estado del despliegue:"
zappa status $STAGE

echo ""
echo "✨ ¡Despliegue completado!"
echo ""
echo "📝 Comandos útiles:"
echo "   Ver logs: zappa tail $STAGE --tail"
echo "   Ver estado: zappa status $STAGE"
echo "   Rollback: zappa rollback $STAGE"

