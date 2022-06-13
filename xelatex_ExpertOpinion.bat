@echo off
chcp 65001
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode ExpertOpinion.tex 
PythonTeX ExpertOpinion.tex
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode ExpertOpinion.tex 