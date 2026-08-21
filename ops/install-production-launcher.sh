#!/bin/sh
set -eu

[ "$(id -u)" -eq 0 ] || {
  echo "Ejecutar una sola vez con sudo." >&2
  exit 1
}

launcher=/usr/local/sbin/whatamicraft-up
sudoers=/etc/sudoers.d/whatamicraft-up
tmp_launcher=$(mktemp)
tmp_sudoers=$(mktemp)
trap 'rm -f "$tmp_launcher" "$tmp_sudoers"' EXIT

cat >"$tmp_launcher" <<'EOF'
#!/bin/sh
set -eu

[ "$#" -eq 0 ] || {
  echo "Este launcher no acepta argumentos." >&2
  exit 2
}

app_dir=/home/brian/MinecraftQuizGuesser
env_file=/etc/whatamicraft/production.env

[ -r "$env_file" ] || {
  echo "No se puede acceder al archivo de entorno de producción." >&2
  exit 1
}
[ -f "$app_dir/compose.yaml" ] || {
  echo "No existe compose.yaml en el proyecto de producción." >&2
  exit 1
}

cd "$app_dir"
exec /usr/bin/docker compose \
  --ansi never \
  --project-directory "$app_dir" \
  --env-file "$env_file" \
  -f "$app_dir/compose.yaml" \
  up -d --build dashboard bot publisher-worker backup-rollback media
EOF

printf '%s\n' \
  'brian ALL=(root) NOPASSWD: /usr/local/sbin/whatamicraft-up ""' \
  >"$tmp_sudoers"
chmod 440 "$tmp_sudoers"
/usr/sbin/visudo -cf "$tmp_sudoers" >/dev/null

install -o root -g root -m 700 "$tmp_launcher" "$launcher"
install -o root -g root -m 440 "$tmp_sudoers" "$sudoers"

echo "Launcher instalado: $launcher"
echo "Solo permite: sudo $launcher"
