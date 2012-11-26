#!/bin/sh -e

export PYTHONPATH=.

echo "=== Nuking old .pyc files..."
find transports/ -name '*.pyc' -delete
find dispatchers/ -name '*.pyc' -delete
echo "=== Erasing previous coverage data..."
coverage erase
echo "=== Running trial tests..."
coverage run --include='transports/*,dispatchers/*' --omit='vumi/*' --append --branch `which trial` --reporter=subunit tests | tee results.txt | subunit2pyunit
subunit2junitxml <results.txt >test_results.xml
rm results.txt
echo "=== Processing coverage data..."
coverage xml --omit='ve/src/vumi/*'
echo "=== Checking for PEP-8 violations..."
pep8 --repeat transports dispatchers | tee pep8.txt
echo "=== Done."
