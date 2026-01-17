@echo off
REM Quick script to manually publish Super Signal to PyPI

echo Building Super Signal...
rmdir /s /q dist build 2>nul
del /q *.egg-info 2>nul
python -m build

echo.
echo Checking package...
twine check dist/*

echo.
echo Ready to upload!
echo.
echo To upload to Test PyPI:
echo   twine upload --repository testpypi dist/*
echo.
echo To upload to PyPI (production):
echo   twine upload dist/*
echo.
pause
