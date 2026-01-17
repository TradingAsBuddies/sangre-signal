#!/bin/bash
# Quick script to manually publish Super Signal to PyPI

set -e

echo "🔨 Building Super Signal..."
rm -rf dist/ build/ *.egg-info
python -m build

echo "✅ Checking package..."
twine check dist/*

echo ""
echo "📦 Ready to upload!"
echo ""
echo "To upload to Test PyPI:"
echo "  twine upload --repository testpypi dist/*"
echo ""
echo "To upload to PyPI (production):"
echo "  twine upload dist/*"
echo ""
