with open("ремонт из DAT.txt", "r", encoding="UTF-8") as file:
    text = file.read().split("\n")
with open("осмотр.tex", "w", encoding="UTF-8") as file:
    for i in range(len(text)):
        if text[i].startswith("Окрасить"):
            file.write("\\акт{" + text[i][9:] + "}{}{}{\\7}\n")
        if text[i].startswith("Заменить"):
            file.write("\\акт{" + text[i][9:] + "}{\\7}{}{}\n")
        else:
            file.write("\\акт{" + text[i][9:].split()[0] + "}{}{\\7}{}\n")


with open("осмотр.tex", "a", encoding="UTF-8") as file:
    file.write("\\end{longtable}\\setcounter{rownum}{0}")