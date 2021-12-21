@echo off
chcp 65001
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode Заключение_эксперта.tex 
PythonTeX Заключение_эксперта.tex
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode Заключение_эксперта.tex 