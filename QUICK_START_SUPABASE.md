# ⚡ Inicio Rápido: Supabase PostgreSQL

## ✅ Configuración Rápida

### Paso 1: Obtener Contraseña de Supabase

1. Ve a: https://supabase.com/dashboard
2. Selecciona tu proyecto
3. Ve a **Settings** > **Database**
4. Busca **Connection string** > **Connection pooling**
5. Copia la URL y reemplaza `[YOUR-PASSWORD]` con tu contraseña real

### Paso 2: Actualizar zappa_settings.json

Edita `zappa_settings.json` y actualiza la línea de `DATABASE_URL`:

```json
{
    "dev": {
        ...
        "environment_variables": {
            "DATABASE_URL": "postgresql://postgres.gnugcsaafobcjdshvipj:TU_PASSWORD_REAL@aws-1-us-east-2.pooler.supabase.com:6543/postgres",
            ...
        }
    }
}
```

**⚠️ IMPORTANTE**: 
- Reemplaza `TU_PASSWORD_REAL` con tu contraseña de Supabase
- Usa el puerto **6543** (pooler), no 5432 (directo)
- El pooler es mejor para Lambda

### Paso 3: Actualizar Despliegue

```powershell
zappa update dev
```

### Paso 4: Crear Tablas

```powershell
# Crear tablas en Supabase
zappa invoke dev --raw 'from run import app; from app.database import db; from app.models import *; app.app_context().push(); db.create_all(); print("✅ Tablas creadas")'
```

### Paso 5: Crear Administrador

```powershell
# Crear admin por defecto
zappa invoke dev 'init_admin_lambda.init_admin'
```

### Paso 6: Verificar

```powershell
# Ver logs
zappa tail dev --since 5m

# Probar conexión
zappa invoke dev --raw 'from run import app; from app.database import db; app.app_context().push(); db.session.execute(db.text("SELECT version()")); print("✅ PostgreSQL OK")'
```

## 🔍 Verificar en Supabase

1. Ve a **Table Editor** en Supabase Dashboard
2. Deberías ver las tablas creadas:
   - `usuarios`
   - `mascotas`
   - `citas`
   - `adopciones`
   - `historial_medico`

## ✅ Ventajas de Supabase vs RDS

- ✅ **No necesita VPC**: Acceso público directo
- ✅ **Connection Pooling**: Incluido (puerto 6543)
- ✅ **Dashboard Web**: Administración fácil
- ✅ **Gratis**: Plan free tier generoso
- ✅ **Más simple**: No necesitas configurar security groups, subnets, etc.

## ⚠️ Solo Cambiar

En `zappa_settings.json`, línea 37:

**De:**
```json
"DATABASE_URL": "",
```

**A:**
```json
"DATABASE_URL": "postgresql://postgres.gnugcsaafobcjdshvipj:TU_PASSWORD@aws-1-us-east-2.pooler.supabase.com:6543/postgres",
```

**Luego:**
```powershell
zappa update dev
```

¡Y listo! 🚀

