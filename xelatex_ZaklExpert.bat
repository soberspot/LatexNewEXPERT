@echo off
chcp 65001
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode ZaklExpert.tex 
biber.exe ZaklExpert.tex  backend=biber
pythontex ZaklExpert.tex
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode ZaklExpert.tex 