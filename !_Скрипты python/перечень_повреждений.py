with open("осмотр.tex", "r", encoding="UTF-8") as file:
    text = file.read()
    text = text.replace("\\акт", "\\пов")
    text = text.replace("{\\7}{}{}", "{}")
    text = text.replace("{}{\\7}{}", "{}")
    text = text.replace("{}{}{\\7}", "{}")
    text = text.replace("{}{\\7}{\\7}", "{}")      
    text = text.replace("{\\7}{}{\\7}", "{}")

with open("перечень_повреждений.tex", "w", encoding="UTF-8") as file:
    file.write(text)
                                                                           