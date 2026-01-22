pyinstaller --onefile --windowed --exclude-module matplotlib --exclude-module numpy --exclude-module scipy --exclude-module PyQt5 --hidden-import babel.numbers attendance.py
copy dist\attendance.exe .
