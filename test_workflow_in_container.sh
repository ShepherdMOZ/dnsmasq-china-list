#!/bin/bash
set -e

echo "=== Starting Workflow Test inside Container ==="

# 1. Create a dummy selected-domains.txt if it doesn't exist
if [ ! -f selected-domains.txt ]; then
  echo "Creating temporary selected-domains.txt..."
  cat <<EOF > selected-domains.txt
baidu.com
www.baidu.com
google.com
0000wb.com
EOF
fi

# 2. Run the python script
echo "Running generate_opnsense_unbound.py..."
python3 generate_opnsense_unbound.py

# 3. Verify output
if [ ! -f selected-domains.unbound.conf ]; then
  echo "Error: selected-domains.unbound.conf was not created!"
  exit 1
fi

echo "=== Output Configuration ==="
cat selected-domains.unbound.conf

# Ensure we have a clean git repo context inside the container for diff checks
if [ -e .git ]; then
  rm -rf .git
fi

# 4. Check for git diff simulation (commit & push setup)
echo "Simulating git config and commit..."
git config --global user.email "test@example.com"
git config --global user.name "Test User"
git config --global safe.directory /app

if [ ! -d .git ]; then
  git init
  git add .
  git commit -m "initial commit" || true
fi

# Simulate upstream sync step
echo "Simulating upstream sync inside container..."
git remote add upstream https://github.com/felixonmars/dnsmasq-china-list.git || true
git fetch --depth=1 upstream master
git merge upstream/master --no-edit -m "merge: sync upstream changes" || echo "Local test merge warning/conflict ignored"

# Modify selected-domains.txt and run again to verify diff works
echo "Adding new domain to selected-domains.txt..."
echo "taobao.com" >> selected-domains.txt
python3 generate_opnsense_unbound.py

# Check git diff of the output file
git add selected-domains.unbound.conf
if git diff --cached --quiet; then
  echo "Error: git diff showed no changes, but taobao.com was added!"
  exit 1
else
  echo "Git diff detected changes as expected!"
  git diff --cached
fi

echo "=== Workflow Container Test PASSED successfully! ==="
