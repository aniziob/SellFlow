$ErrorActionPreference = 'Stop'
& .\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean --onefile --windowed --name SellFlow desktop_sellflow.py
Write-Host "Executável criado em dist\SellFlow.exe"
