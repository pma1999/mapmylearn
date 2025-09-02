# Railway CLI: comandos rápidos para probar conectividad SMTP desde tu proyecto Railway
# Guarda este archivo localmente y reemplaza SMTP_HOST y SMTP_PORT por tus valores reales.
#
# Uso:
# 1) Instala railway CLI y haz login (ver docs/railway_smtp_debug.md)
# 2) Desde la raíz del repo enlazado al proyecto, ejecuta estos comandos.

# 1) Prueba TCP con netcat (si está disponible en el entorno)
railway run -- nc -vz SMTP_HOST SMTP_PORT

# Ejemplo:
# railway run -- nc -vz smtp.example.com 587

# 2) Prueba TLS / STARTTLS con openssl (para 587 usar -starttls smtp; para 465 conectar directo)
# STARTTLS (587):
railway run -- openssl s_client -starttls smtp -connect SMTP_HOST:SMTP_PORT -crlf -brief

# SMTPS (465):
railway run -- openssl s_client -connect SMTP_HOST:465 -crlf -brief

# 3) One-liner Python para comprobar conexión TCP (útil si nc/openssl no existen)
railway run -- python -c "import socket,sys; \
  \
  host='SMTP_HOST'; port=int('SMTP_PORT'); \
  socket.create_connection((host,port),10); print('OK')"

# Ejemplo (sustituye valores):
# railway run -- python -c "import socket; socket.create_connection(('smtp.example.com',587),10); print('OK')"

# 4) Comprobar resolución DNS
railway run -- nslookup SMTP_HOST

# 5) (Opcional) traceroute para ver dónde se corta la ruta
railway run -- traceroute SMTP_HOST

# Notas de interpretación rápidas (resumen):
# - "OK" o "succeeded/open" -> TCP hacia el host:puerto funciona → problema no es bloqueo de red.
# - "timed out" -> salida bloqueada / puerto filtrado / DNS erróneo → muy común en PaaS (proveedor bloquea SMTP).
# - "connection refused" -> puerto cerrado en host remoto.
# - openssl conecta y muestra certificado -> la negociación TLS funciona; prueba enviar EHLO localhost y revisa respuestas 250-.
#
# Si obtienes TIMEOUT desde Railway, la recomendación inmediata es usar la API de SendGrid (o similar)
# ya que evita la salida SMTP en puertos tradicionales y suele ser permitida por PaaS.
#
# Pega la salida completa de cualquiera de los comandos aquí y la analizo.
