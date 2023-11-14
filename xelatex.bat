@echo off
chcp 65001
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode zakluchenie_experta.tex 
pythontex Заключение_эксперта.tex
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode zakluchenie_experta.tex