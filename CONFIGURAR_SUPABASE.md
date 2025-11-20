# 🗄️ Configurar Supabase PostgreSQL en Lambda

Guía para usar Supabase PostgreSQL con AWS Lambda.

## ✅ Ventajas de Supabase

- ✅ **Persistencia real**: Base de datos PostgreSQL en la nube
- ✅ **Acceso público**: No necesitas VPC (más simple)
- ✅ **Connection Pooler**: Mejor para Lambda con muchas invocaciones
- ✅ **Gratis**: Plan free tier generoso
- ✅ **Dashboard**: Interfaz web para administrar la BD

## 🔧 Configuración

### Paso 1: Obtener URL de Supabase

1. Ve a tu proyecto en Supabase: https://supabase.com/dashboard
2. Ve a **Settings** > **Database**
3. Copia la **Connection string** (URI) de **Connection pooling**
4. Reemplaza `[YOUR-PASSWORD]` con tu contraseña real

**Formato:**
```
postgresql://postgres.gnugcsaafobcjdshvipj:TU_PASSWORD_REAL@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

**Nota**: Usa el **pooler** (puerto 6543) para Lambda, no la conexión directa.

### Paso 2: Crear Base de Datos

En Supabase SQL Editor, ejecuta:

```sql
CREATE DATABASE mascotas_elect;

-- O si ya existe, simplemente usa el schema 'public'
-- Las tablas se crearán automáticamente en el schema 'public'
```

O conecta directamente y crea las tablas cuando ejecutes la app por primera vez.

### Paso 3: Actualizar zappa_settings.json

**IMPORTANTE**: Reemplaza `[YOUR-PASSWORD]` con tu contraseña real de Supabase.

```json
{
    "dev": {
        ...
        "environment_variables": {
            "DATABASE_URL": "postgresql://postgres.gnugcsaafobcjdshvipj:TU_PASSWORD_REAL@aws-1-us-east-2.pooler.supabase.com:6543/postgres",
            "DB_TYPE": "postgresql",
            ...
        }
    }
}
```

**⚠️ IMPORTANTE**: 
- No necesitas `vpc_config` para Supabase (acceso público)
- Usa el **pooler** (puerto 6543), no la conexión directa (5432)
- El pooler es mejor para Lambda porque maneja conexiones eficientemente

### Paso 4: Actualizar Despliegue

```powershell
zappa update dev
```

### Paso 5: Crear Tablas e Inicializar

```powershell
# Crear tablas (se ejecuta automáticamente en el primer request)
# Pero puedes forzarlo con:
zappa invoke dev --raw 'from run import app; from app.database import db; from app.models import *; app.app_context().push(); db.create_all(); print("Tablas creadas")'

# Crear admin
zappa invoke dev 'init_admin_lambda.init_admin'
```

## 🔍 Verificar Conexión

```powershell
# Verificar que se conecta correctamente
zappa invoke dev --raw 'from run import app; from app.database import db; app.app_context().push(); db.session.execute(db.text("SELECT version()")); print("✅ Conexión OK")'

# Ver logs
zappa tail dev --since 5m
```

## 📋 Crear Base de Datos en Supabase

1. Ve a **SQL Editor** en Supabase Dashboard
2. Ejecuta:

```sql
-- Crear base de datos (si no existe el schema)
CREATE SCHEMA IF NOT EXISTS public;

-- O usar la base de datos postgres y crear las tablas ahí
-- Las tablas se crearán automáticamente cuando ejecutes db.create_all()
```

**Nota**: Por defecto, Supabase usa el schema `public` de la base de datos `postgres`. Las tablas se crearán automáticamente.

## 🔐 Seguridad

### Usar Variable de Entorno para Password

En lugar de poner la password en `zappa_settings.json`, usa:

1. **AWS Secrets Manager** (recomendado):

```json
{
    "dev": {
        ...
        "environment_variables": {
            "DATABASE_URL_SECRET_ARN": "arn:aws:secretsmanager:us-east-2:ACCOUNT:secret:supabase/db/url"
        }
    }
}
```

Y actualiza `app/config.py` para leer del secret.

2. **O simplemente reemplaza en zappa_settings.json**:

```json
"DATABASE_URL": "postgresql://postgres.gnugcsaafobcjdshvipj:TU_PASSWORD_AQUI@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
```

## 🎯 URLs de Supabase

### Connection Pooling (Recomendado para Lambda)
```
postgresql://postgres.gnugcsaafobcjdshvipj:PASSWORD@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

### Direct Connection (No recomendado para Lambda)
```
postgresql://postgres.gnugcsaafobcjdshvipj:PASSWORD@aws-1-us-east-2.pooler.supabase.com:5432/postgres
```

**Usa el pooler (6543)** porque:
- Mejor para muchas conexiones concurrentes
- Maneja reconexiones automáticamente
- Optimizado para serverless

## 🧪 Probar Localmente

Para probar localmente, crea `config.env`:

```env
DATABASE_URL=postgresql://postgres.gnugcsaafobcjdshvipj:TU_PASSWORD@aws-1-us-east-2.pooler.supabase.com:6543/postgres
```

O usa variables individuales:

```env
DB_TYPE=postgresql
DB_HOST=aws-1-us-east-2.pooler.supabase.com
DB_PORT=6543
DB_USER=postgres.gnugcsaafobcjdshvipj
DB_PASSWORD=TU_PASSWORD
DB_NAME=postgres
```

## ⚠️ Notas Importantes

1. **Password en URL**: Reemplaza `[YOUR-PASSWORD]` con tu contraseña real
2. **Connection Pooling**: Usa puerto **6543** (pooler), no 5432 (directo)
3. **Sin VPC**: No necesitas configurar `vpc_config` en `zappa_settings.json`
4. **SSL**: Supabase requiere SSL por defecto. SQLAlchemy lo maneja automáticamente

## 🔄 Migración de MySQL a PostgreSQL

Si tenías datos en MySQL local, necesitarás migrarlos:

1. Exportar datos de MySQL:
```bash
mysqldump -u maxi -p1234 mascotas_elect > backup.sql
```

2. Convertir formato SQL (puede requerir ajustes manuales)

3. Importar a Supabase usando el SQL Editor

O simplemente recrea los datos desde cero usando la aplicación.

## 📊 Verificar en Supabase

1. Ve a **Table Editor** en Supabase Dashboard
2. Deberías ver las tablas creadas:
   - `usuarios`
   - `mascotas`
   - `citas`
   - `adopciones`
   - `historial_medico`

## Troubleshooting

### Error: "password authentication failed"

**Solución**: Verifica que la password en `DATABASE_URL` sea correcta

### Error: "connection timeout"

**Solución**: 
- Verifica que uses el pooler (puerto 6543)
- Verifica que no haya firewall bloqueando
- Supabase debería ser accesible públicamente

### Error: "relation does not exist"

**Solución**: Las tablas no existen. Ejecuta:
```powershell
zappa invoke dev --raw 'from run import app; from app.database import db; from app.models import *; app.app_context().push(); db.create_all(); print("OK")'
```

### Error: "too many connections"

**Solución**: 
- Usa connection pooling (puerto 6543)
- Considera usar `SQLALCHEMY_ENGINE_OPTIONS` para pooling

## 🔒 Mejorar Seguridad

Para producción, no pongas la password directamente en `zappa_settings.json`. En su lugar:

1. **Usa AWS Secrets Manager**
2. **O usa variables de entorno por separado** y construye la URL en el código
3. **O encripta el archivo** antes de subirlo

## ✅ Checklist

- [ ] Reemplazaste `[YOUR-PASSWORD]` en `DATABASE_URL`
- [ ] Actualizaste `zappa_settings.json`
- [ ] Ejecutaste `zappa update dev`
- [ ] Creaste las tablas con `db.create_all()`
- [ ] Verificaste conexión con `zappa invoke`
- [ ] Creaste el admin con `init_admin_lambda.init_admin`
- [ ] Probaste el endpoint `/mascotas`

