@echo off
chcp 65001
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode Expert_Report.tex
biber.exe Expert_Report.tex  backend=biber
pythontex Expert_Report.tex
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode Expert_Report.tex