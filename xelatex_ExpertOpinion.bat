@echo off
chcp 65001
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode ExpertOpinion.tex 
biber.exe ExpertOpinion.tex  backend=biber
pythontex ExpertOpinion.tex
xelatex.exe  --shell-escape  -synctex=1   -interaction=nonstopmode ExpertOpinion.tex 