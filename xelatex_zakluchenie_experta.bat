@echo off
chcp 65001
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode zakluchenie_experta.tex
biber.exe zakluchenie_experta.tex  backend=biber
pythontex zakluchenie_experta.tex
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode zakluchenie_experta.tex