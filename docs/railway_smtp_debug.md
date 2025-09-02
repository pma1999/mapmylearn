Diagnóstico de conectividad SMTP desde Railway (CLI local)
==========================================================

Sigue estos pasos desde tu máquina local usando la Railway CLI para comprobar por qué tu aplicación obtiene "TimeoutError: timed out" al conectar con el servidor SMTP.

1) Instalar Railway CLI (si no lo tienes)
----------------------------------------
Opciones (elige una):

- npm:
  npm install -g @railway/cli

- script de instalación oficial (si prefieres curl/sh):
  curl -sSL https://railway.app/install.sh | sh

2) Login y enlazar el proyecto Railway
--------------------------------------
- Inicia sesión:
  railway login

- Sitúate en el directorio del repo (donde tienes el proyecto que desplegaste).
  Opcionalmente enlaza el proyecto (si no está enlazado):
  railway link
  (Sigue las instrucciones para seleccionar tu proyecto/entorno)

3) Ejecutar las pruebas de conectividad (comandos recomendados)
----------------------------------------------------------------
Reemplaza SMTP_HOST y SMTP_PORT por los valores reales (por ejemplo smtp.example.com y 587).

A) Comprobación TCP con netcat (nc)
- Ejecuta:
  railway run -- nc -vz SMTP_HOST SMTP_PORT
- Ejemplo:
  railway run -- nc -vz smtp.example.com 587

Interpretación:
- "succeeded" / "open" → conexión TCP exitosa (no bloqueo).
- "timed out" → salida bloqueada o DNS erróneo.
- "connection refused" → puerto cerrado en el host remoto.

B) Comprobación TLS / STARTTLS con openssl
- Puerto 587 (STARTTLS):
  railway run -- openssl s_client -starttls smtp -connect SMTP_HOST:SMTP_PORT -crlf -brief
- Puerto 465 (SMTPS):
  railway run -- openssl s_client -connect SMTP_HOST:465 -crlf -brief

Interpretación:
- Si openssl muestra certificado y espera, la negociación TLS funciona. Escribe manualmente:
  EHLO localhost
  y verifica respuestas que empiezan con 250-.
- Si openssl hace timeout, hay bloqueo de red.

C) One-liner Python (si nc/openssl no están disponibles)
- Prueba TCP desde Python:
  railway run -- python -c "import socket; socket.create_connection(('SMTP_HOST', SMTP_PORT), 10); print('OK')"

Ejemplo:
  railway run -- python -c "import socket; socket.create_connection(('smtp.example.com',587), 10); print('OK')"

Interpretación:
- "OK" → conexión TCP OK.
- Excepción socket.timeout → timeout (bloqueo).
- ConnectionRefusedError → puerto cerrado.

D) DNS y trazado (si quieres comprobar resolución/ruta)
- nslookup:
  railway run -- nslookup SMTP_HOST
- traceroute (si está disponible):
  railway run -- traceroute SMTP_HOST
  (en Windows sería tracert; en Railway/containers suele ser traceroute)

Interpretación:
- nslookup falla → nombre mal resuelto (revisa la variable env).
- traceroute muestra en qué salto se corta la ruta.

4) Qué registrar y pegar aquí
------------------------------
Cuando ejecutes cualquiera de los comandos arriba, pega la salida completa aquí. Busca:
- Mensajes "timed out" o "connection refused"
- Salida de openssl (certificado o error)
- Resultado "OK" del Python one-liner

Con esa salida podré indicarte si:
- El problema es bloqueo de puerto por el proveedor (solución: usar SendGrid API o pedir desbloqueo)
- DNS mal configurado
- Credenciales / autenticación (si openssl conecta pero login falla)

5) Acciones rápidas según resultados
------------------------------------
- Si nc/openssl muestran TIMEOUT:
  - Muy probable: Railway / proveedor de hosting bloquea salida SMTP.
  - Recomendación inmediata: usar SendGrid vía API (no requiere conexión SMTP saliente).
- Si connection refused:
  - Revisa SMTP_HOST / SMTP_PORT; confirma con el proveedor SMTP.
- Si openssl conecta pero login falla:
  - Revisa credenciales y tipo de autenticación (Gmail exige app-passwords/OAuth).

6) Si quieres, puedo preparar:
- Un parche para añadir logging más detallado en backend/services/email_providers.py (host/port, timeout, excepción completa).
- Instrucciones para cambiar a SendGrid API y probar con una petición HTTP desde Railway.

Notas finales
-------------
Ejecuta los comandos desde tu Railway CLI local y pega la salida aquí. Yo la analizo y te indico la causa y la solución recomendada.
