#!/bin/sh

PACKAGE_PATH=/usr/local/lib/python3.11/site-packages/zep_python

echo "=== $PACKAGE_PATH/client.py ==="
if [ -f "$PACKAGE_PATH/client.py" ]; then
  cat "$PACKAGE_PATH/client.py"
else
  echo "❌ Fichier introuvable"
fi

echo
echo "=== $PACKAGE_PATH/__init__.py ==="
if [ -f "$PACKAGE_PATH/__init__.py" ]; then
  cat "$PACKAGE_PATH/__init__.py"
else
  echo "❌ Fichier introuvable"
fi

echo
echo "=== $PACKAGE_PATH/user/__init__.py ==="
if [ -f "$PACKAGE_PATH/user/__init__.py" ]; then
  cat "$PACKAGE_PATH/user/__init__.py"
else
  echo "❌ Fichier introuvable"
fi

echo
echo "=== $PACKAGE_PATH/types.py ==="
if [ -f "$PACKAGE_PATH/types.py" ]; then
  cat "$PACKAGE_PATH/types.py"
else
  echo "❌ Fichier introuvable"
fi

echo
echo "=== Contenu de $PACKAGE_PATH/memory/ ==="
if [ -d "$PACKAGE_PATH/memory" ]; then
  for file in "$PACKAGE_PATH/memory"/*.py; do
    echo
    echo "--- $(basename "$file") ---"
    cat "$file"
  done
else
  echo "❌ Dossier introuvable"
fi

echo
echo "--- Fait."
