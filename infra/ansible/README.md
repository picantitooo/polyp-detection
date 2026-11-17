# Fases 7B/7C: despliegue de polyp mediante Ansible y TURN seguro

Administra tres EC2 **existentes** con Amazon Linux 2023 mediante
`amazon.aws.aws_ssm`. El inventario descubre instancias running de polyp/staging
y genera `role_backend`, `role_frontend` y `role_proxy` con `ec2_tags.Role`.
Se requiere exactamente una instancia distinta por grupo. No se usa SSH ni se
crean instancias, redes, buckets, roles o reglas de security groups.

Las variables se cargan automáticamente desde `inventory/group_vars/all.yml`.
No crear otro `group_vars/all.yml` en la raíz ni añadir `vars_files` a los
playbooks. El callback es `ansible.builtin.default`, con formato YAML.

## Preparación

Ejecutar desde `infra/ansible/`. En un entorno Python 3.10 o posterior:

```sh
python3 -m venv /tmp/polyp-ansible-venv
. /tmp/polyp-ansible-venv/bin/activate
python -m pip install 'ansible-core>=2.17' 'boto3>=1.35.0' 'botocore>=1.35.0'
ansible-galaxy collection install -r requirements.yml
session-manager-plugin --version
```

`requirements.yml` fija amazon.aws 11.5.1. El controlador necesita credenciales
AWS vigentes configuradas fuera del repositorio, Session Manager Plugin y
permisos de descubrimiento EC2, sesiones SSM y transferencia S3. El bucket de
transferencia **ya debe existir** y ser distinto del bucket de modelos. El plugin
SSM utiliza ese bucket para módulos y archivos temporales que pueden contener
datos sensibles. Debe conservar bloqueo público, cifrado, denegación de HTTP,
versionado suspendido y limpieza previamente configurados. El plugin elimina
transferencias al terminar; la expiración existente actúa como respaldo.
Consultar los [requisitos de SSM](https://docs.ansible.com/projects/ansible/latest/collections/amazon/aws/aws_ssm_connection.html).

Cada EC2 requiere Python 3, curl, sudo, SSM Agent activo y acceso a SSM, S3, ECR y
repositorios de paquetes. El proxy también descarga Caddy y Coturn de Docker Hub. Los
perfiles IAM existentes de backend/frontend deben permitir autenticación y pull
ECR; backend necesita ListBucket y GetObject para los dos modelos. Los comandos
AWS remotos usan el rol IAM de la instancia; no copiar credenciales a las EC2.

La conectividad existente debe permitir HTTP público al proxy y tráfico privado
desde el proxy hacia backend:8000 y frontend:3000. Ansible no modifica firewall
ni security groups. Common instala Docker mediante dnf, habilita el servicio e
instala el paquete `awscli2` si falta `aws`.

## Variables de entorno

Configurar valores reales exclusivamente en el entorno, fuera de Git. Este
bloque usa **Bash** y solicita los valores sin escribirlos en el historial:

```sh
export AWS_REGION=us-east-2
read -r -p 'Bucket existente para transferencias SSM: ' ANSIBLE_SSM_BUCKET
read -r -p 'URI ECR backend completa con tag: ' POLYP_BACKEND_IMAGE
read -r -p 'URI ECR frontend completa con tag: ' POLYP_FRONTEND_IMAGE
read -r -p 'Bucket existente de modelos: ' POLYP_MODEL_BUCKET
read -r -p 'Origen público HTTP del proxy, sin barra final: ' POLYP_PUBLIC_ORIGIN
export ANSIBLE_SSM_BUCKET POLYP_BACKEND_IMAGE POLYP_FRONTEND_IMAGE
export POLYP_MODEL_BUCKET POLYP_PUBLIC_ORIGIN
```

Las imágenes deben ser URI ECR privadas completas de us-east-2 con tag explícito.
Para repetir una versión, usar tags inmutables y conservar las mismas versiones
de los dos objetos ONNX: sincronizar un bucket mutable puede actualizar modelos.
`POLYP_PUBLIC_ORIGIN` debe ser `http://HOST` con puerto opcional, sin ruta,
credenciales, query ni fragmento. AWS_REGION debe ser exactamente us-east-2.
No guardar archivos `.env`, inventarios renderizados, IDs de cuenta, IP públicas,
tags de imágenes de aplicación ni nombres reales de buckets en el repositorio.

Backend sincroniza solamente `detector.onnx` y `classifier.onnx` de la raíz del
bucket a `/opt/polyp/models/`, monta `/models:ro` y configura
`POLYP_MODEL_DIR=/models` y `CORS_ALLOWED_ORIGINS` con el origen público.
La aplicación acepta CORS separado por comas, elimina espacios y duplicados y
rechaza comodines. Una variable vacía no permite ningún origen; si no está
definida, conserva localhost:5173 y 127.0.0.1:5173 para desarrollo.
`/health` ya existe y no carga modelos: verifica HTTP, no la inferencia.

## Preparar las imágenes previamente

Las imágenes deben estar construidas y publicadas antes del despliegue. Ansible
solo autentica y descarga. El Dockerfile frontend recibe `PUBLIC_API_URL` como
argumento y el componente lo importa desde `$env/static/public`: la URL queda
incluida en el build. En producción debe ser `http://<proxy-public-ip>/api`.
Desde la raíz del repositorio, el build equivalente es:

```sh
docker build --build-arg PUBLIC_API_URL="${POLYP_PUBLIC_ORIGIN}/api" -t "$POLYP_FRONTEND_IMAGE" frontend/
docker build -t "$POLYP_BACKEND_IMAGE" backend/
```

Publicar ambas imágenes mediante el flujo ECR existente. Si cambia el origen
público, reconstruir frontend y desplegar su imagen. No basta cambiar una
variable del contenedor después del build.

## Ejecución cuando se autorice un despliegue

Estos comandos consultan AWS; deploy también modifica las EC2. No forman parte
de la validación local:

```sh
ansible-inventory --graph
ansible-playbook playbooks/connectivity.yml
ansible-playbook playbooks/deploy.yml
```

El primer play valida variables, cardinalidad, transporte y direcciones privadas
en el controlador antes de abrir sesiones. Luego ejecuta common en las tres
EC2, backend, frontend y proxy. Un fallo detiene el despliegue. Los pulls ocurren
antes de retirar el contenedor anterior. ECR utiliza `--password-stdin`, tareas
`no_log` y configuración Docker temporal eliminada incluso si falla el pull;
no deja tokens en `/root/.docker/config.json`.

Las tareas de paquetes, directorios y modelos son repetibles. Frontend y Caddy reemplazan sus contenedores en cada ejecución. Backend y
Coturn conservan el contenedor si imagen y configuración no cambian. Todos usan
`--restart unless-stopped`; hay una breve interrupción, sin rollback automático.
Los tags son `common`, `backend`, `frontend`, `proxy`, `deploy` y `preflight`:

```sh
ansible-playbook playbooks/deploy.yml --tags common,backend
```

La validación inicial lleva `always`. Para ejecuciones parciales usar tags, sin
`--limit` (podría excluir localhost) ni `--skip-tags always`. Los roles parciales
requieren common previamente aplicado. No usar `--check` como prueba de
conectividad o de contenedores.

## Proxy y verificaciones

Caddy escucha solo `:80`, con HTTPS automático desactivado. Obtiene las IP
privadas de `hostvars[groups[...][0]].private_ip_address`.
`handle_path /api/*` elimina `/api` y envía a backend:8000; `handle` envía el resto
al frontend:3000. `reverse_proxy` maneja WebSocket automáticamente. Consultar
[handle_path](https://caddyserver.com/docs/caddyfile/directives/handle_path) y
[reverse_proxy](https://caddyserver.com/docs/caddyfile/directives/reverse_proxy).

El playbook valida Caddyfile antes de reemplazar el proxy y espera con reintentos:

- Backend: `curl -fsS http://localhost:8000/health`.
- Frontend: `curl -fsS http://localhost:3000/`.
- Desde proxy: `curl -fsS http://localhost/api/health` y `curl -fsS http://localhost/`.

Después de un despliegue autorizado, comprobar desde el controlador:

```sh
curl -fsS "${POLYP_PUBLIC_ORIGIN}/api/health"
curl -fsS "${POLYP_PUBLIC_ORIGIN}/"
```

HTTPS y dominio quedan para otra fase. La cámara del navegador en HTTP público
está limitada por el requisito de contexto seguro; estas verificaciones HTTP no
demuestran que WebRTC ni la inferencia funcionen.

## Validación local sin AWS

Usar inventario local explícito para comprobar sintaxis, sin ejecutar tareas:

```sh
ANSIBLE_LOCAL_TEMP=/tmp/polyp-ansible-local ansible-playbook -i 'localhost,' --syntax-check playbooks/connectivity.yml
ANSIBLE_LOCAL_TEMP=/tmp/polyp-ansible-local ansible-playbook -i 'localhost,' --syntax-check playbooks/deploy.yml
```

Para comprobar inventario y preflight sin AWS, crear fuera de Git un inventario
YAML estático de prueba con una entrada ficticia en cada grupo, transporte
`amazon.aws.aws_ssm`, región us-east-2 y `private_ip_address` en backend/frontend.
Copiar `inventory/group_vars/all.yml` a `group_vars/all.yml` junto a ese inventario
y exportar valores **ficticios** con los formatos requeridos. Ejecutar:

```sh
ANSIBLE_LOCAL_TEMP=/tmp/polyp-ansible-local ansible-inventory -i /tmp/polyp-local-inventory/hosts.yml --graph
ANSIBLE_LOCAL_TEMP=/tmp/polyp-ansible-local ansible-playbook -i /tmp/polyp-local-inventory/hosts.yml playbooks/deploy.yml --tags preflight
```

Con ese inventario estático, preflight solo ejecuta asserts en localhost. No
usar el playbook completo con el inventario de prueba. Un inventario vacío,
roles duplicados, variables incompletas o una región distinta deben fallar.


## Fase 7C: TURN REST

El navegador obtiene `GET /api/webrtc/ice-servers` antes de crear el peer. FastAPI
responde `Cache-Control: no-store` y genera `username=<expiración UNIX>:<aleatorio>`
y `credential=Base64(HMAC-SHA1(secreto, username))`. El backend crea otro usuario
efímero para su propio peer. No se modifica el contrato de `/webrtc/offer` ni el
pipeline ONNX. No guardar respuestas ICE en logs ni compartir volcados SDP.

Desarrollo local: `TURN_URL` y `TURN_SHARED_SECRET` son opcionales en FastAPI;
si falta cualquiera, devuelve `{"iceServers":[]}` y usa ICE sin TURN.
`TURN_CREDENTIAL_TTL_SECONDS` tiene default 3600, debe ser positivo y no renueva
sesiones en curso; volver a conectar obtiene otra identidad. Los relojes de
backend y proxy deben estar sincronizados. La URL frontend sigue compilándose
con `PUBLIC_API_URL`, también en `/webrtc-test`.

Variables nuevas, siempre exportadas en el entorno del controlador:

| Variable | Valor/origen |
| --- | --- |
| `POLYP_TURN_PARAMETER_NAME` | output Terraform `turn_parameter_name` (`/polyp/staging/turn/shared-secret`) |
| `POLYP_PROXY_PUBLIC_IP` | output existente `proxy_public_ip` (EIP) |
| `POLYP_PROXY_PRIVATE_IP` | IP privada de la EC2 proxy; debe coincidir con el inventario |
| `POLYP_TURN_URL` | `turn:<EIP>:3478?transport=udp` o `turn:<EIP>:3478?transport=tcp` |

No exportar el secreto compartido en el controlador. Los scripts copiados a
cada EC2 llaman remotamente a `aws ssm get-parameter --with-decryption` usando
su rol IAM. La salida queda en memoria remota, nunca en resultados Ansible.
Backend genera `/opt/polyp/backend/turn.env` (0600, directorio 0700), lo pasa a
Docker con `--env-file` y lo elimina mediante `always`, incluso ante fallos.
El secreto permanece en el entorno del contenedor: el acceso root/Docker en la
EC2 es privilegiado; no volcar `docker inspect`. Proxy escribe atómicamente
`/opt/polyp/turn/turnserver.conf` (0600, directorio 0700) y lo monta read-only.
Las tareas sensibles usan `no_log` y no imprimen secretos ni credenciales.

Coturn está fijado a `coturn/coturn:4.18.0-r0`, separado de `polyp-proxy` y llamado
`polyp-turn`, con restart `unless-stopped`. Caddy conserva el puerto 80 y sus rutas.
El contenedor TURN usa `--network host`: publica directamente 3478 TCP/UDP y
49160–49200 UDP en la interfaz privada del proxy, que AWS mapea mediante la EIP.
No usa `-p`, porque Docker lo ignora con red host. Esta decisión mantiene
`external-ip=<EIP>/<IP privada>` y `relay-ip=<IP privada>` coherentes, sin un
segundo NAT de Docker. [Coturn recomienda red host](https://github.com/coturn/coturn/blob/master/docker/coturn/README.md).
Terraform agrega solo esos tres ingress al SG proxy existente; frontend y backend
no reciben puertos nuevos. Se presupone la salida a Internet/NAT ya existente
del backend privado y conectividad de retorno stateful de los SG.

Se conserva `lt-cred-mech` junto a `use-auth-secret` por el contrato solicitado;
Coturn da prioridad a TURN REST. Se configuran fingerprint, no-cli y
no-multicast-peers. `no-loopback-peers` fue eliminado de Coturn moderno: se
mantiene su efecto seguro por defecto y con `denied-peer-ip` explícitos para
127.0.0.0/8 y ::1, sin habilitar `allow-loopback-peers`. También se deniega
169.254.0.0/16 (metadata). Ver la [configuración oficial](https://github.com/coturn/coturn/blob/master/docker/coturn/turnserver.conf).
TURN escucha sin TLS/DTLS de transporte en esta fase; WebRTC conserva DTLS-SRTP.
No se abre 5349 ni relay TCP. El cliente TURN puede conectarse por TCP 3478 y
solicitar relay UDP. Hay cuotas de 4 asignaciones por usuario y 40 totales para
el rango reducido de relay; no representan una garantía de capacidad.

Antes de reemplazar Coturn, el generador valida estrictamente las directivas,
puertos, secreto e IPs y solo entonces reemplaza el archivo de forma atómica.
Esto es validación del contrato generado, no un parser oficial de Coturn. Se
reconcilian imagen/configuración y, después de iniciar, se comprueban por UDP y
TCP tanto STUN Binding como rechazo 401 de un Allocate sin autenticar. El hash
de revisión del archivo permite retomar una ejecución fallida y detectar rotaciones
sin guardar el secreto en etiquetas Docker. Los logs Coturn están deshabilitados.
La verificación local de esta fase no ejecuta contenedores; estas comprobaciones
remotas solo correrán durante un despliegue autorizado.

### Orden para un futuro despliegue autorizado

1. Revisar Terraform staging, inicializar proveedores y preparar/revisar el plan
   mediante el flujo existente. Aplicar solo con autorización posterior. El cambio
   crea el SecureString Standard y los permisos exactos de lectura en proxy/backend.
   Se añade un Deny fuera del ARN porque AmazonSSMManagedInstanceCore ya concede
   GetParameter/GetParameters amplios; esto restringe también otras lecturas de
   parámetros desde estos roles y debe considerarse al añadir funciones futuras.
2. Obtener únicamente outputs no sensibles (`turn_parameter_name` y
   `proxy_public_ip`), y exportar las cuatro variables anteriores junto a las de
   Fase 7B. No consultar el valor del parámetro desde el controlador.
3. Construir/publicar ambas imágenes, compilando frontend con
   `PUBLIC_API_URL=${POLYP_PUBLIC_ORIGIN}/api`, como en la sección anterior.
4. Ejecutar preflight y Ansible mediante el flujo existente. Backend y proxy
   recuperan el mismo secreto por IAM. Tras una rotación, actualizar ambos y
   reconectar sesiones. Mantener el secreto estable durante sesiones activas.
5. Verificar salud HTTP y probar WebRTC con archivo desde una red pública;
   confirmar candidatos `relay` y transferencia de medios en las estadísticas
   WebRTC, sin publicar SDP ni credenciales. La sonda STUN/401 no prueba una
   asignación autenticada ni el flujo multimedia de extremo a extremo.

**Terraform state contiene material sensible**, incluido el valor del secreto
aleatorio y el SecureString. `sensitive` oculta la presentación, no cifra el state.
Por eso permanece en el bucket remoto cifrado (AES256 ya configurado en bootstrap),
con bloqueo público y acceso restringido. No guardar state/planes ni usar outputs,
consola, debug o logs para imprimir secretos. No hay output del secreto.

HTTP sirve para la demo con archivo; **HTTPS es obligatorio antes de usar una
cámara clínica real**, incluida la señalización y la entrega de credenciales
efímeras. La cámara pública requiere contexto seguro. TURN REST limita la vigencia
de las credenciales, pero no autentica al usuario de la API: el endpoint comparte
el control de acceso existente de señalización; no se añade autenticación de
usuarios en esta fase.

### Validaciones locales de Fase 7C

No ejecutar Ansible, AWS CLI ni Docker para estas comprobaciones. Desde
`infra/ansible`, los tests mockean todas las llamadas remotas:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s tests -v
```

Desde `backend`, con el entorno Python del proyecto:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m unittest discover -s tests -v
```

Desde `frontend`, con una URL de ejemplo (no conecta con ella):

```sh
PUBLIC_API_URL=http://proxy.example.test/api npm run check
PUBLIC_API_URL=http://proxy.example.test/api npm run test -- --project=server
```

Terraform se puede validar en una copia temporal con `init -backend=false`,
`terraform fmt -check` y `terraform validate`; la instalación de proveedores solo
consulta el registry de HashiCorp. El backend remoto deshabilitado evita acceder
a AWS. El lock incluye random y conserva la versión AWS existente.
