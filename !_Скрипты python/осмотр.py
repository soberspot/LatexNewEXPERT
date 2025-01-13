with open("ремонт.txt", "r", encoding="UTF-8") as file:
    text = file.read().split("\n")

with open("осмотр.tex", "w", encoding="UTF-8") as file:
    for line in text:
        if line.startswith("Окрасить"):
            file.write("\\акт{" + line[9:] + "}{}{}{\\7}\n")
        elif line.startswith("Заменить"):
            file.write("\\акт{" + line[9:] + "}{\\7}{}{}\n")
        else:
            file.write("\\акт{" + line[9:] + "}{}{\\7}{}\n")

with open("осмотр.tex", "a", encoding="UTF-8") as file:
    file.write("\\end{longtable}\\setcounter{rownum}{0}")
