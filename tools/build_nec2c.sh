#!/usr/bin/env bash
# nec2c'yi kaynaktan derler (paket yoneticisinde yoksa).
# Kullanim: ./tools/build_nec2c.sh   -> ./nec2c ikili dosyasi olusur; PATH'e kopyalayin.
set -euo pipefail
tmp=$(mktemp -d)
git clone --depth 1 https://github.com/KJ7LNW/nec2c.git "$tmp/nec2c"
cd "$tmp/nec2c"
# nec2c.c eski tek-dosya surumudur; derlemeye dahil edilmez
gcc -O2 -DPACKAGE_STRING='"nec2c"' -o nec2c $(ls *.c | grep -v '^nec2c.c$') -lm
cp nec2c "$OLDPWD/nec2c"
echo "Derlendi: $OLDPWD/nec2c  (ornek: sudo cp nec2c /usr/local/bin/)"
