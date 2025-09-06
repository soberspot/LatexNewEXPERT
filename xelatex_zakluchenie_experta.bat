@echo off
chcp 65001
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode Expert Report.tex
biber.exe Expert Report.tex  backend=biber
pythontex Expert Report.tex
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode Expert Report.tex