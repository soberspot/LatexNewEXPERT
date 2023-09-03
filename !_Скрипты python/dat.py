import xml.etree.ElementTree as ET

with open("vxs.xml", "r", encoding="UTF-8") as f:
    xml_string = f.read()

root = ET.fromstring(xml_string)
namespace = {"ns2": "http://www.dat.de/vxs"}

# with open("dossier_ids.txt", "w", encoding="UTF-8") as ff:
for dossier in root.findall(".//ns2:RepairPosition", namespace):
    repear_type = dossier.find("ns2:RepairType", namespace).text
    parts_name = dossier.find("ns2:Description", namespace).text
    if repear_type == "replace":
        print("Заменить " + parts_name)
    if repear_type == "lacquer":
        print("Окрасить " + parts_name)
    if repear_type == "repeare":
        print("Ремонтировать " + parts_name)
        # ff.write(dossier_id + parts_name + "\\n")

for dossier in root.findall(".//ns2:MaterialPosition", namespace):
    part_namber = dossier.find("ns2:DATPartNumber", namespace).text
    parts_name = dossier.find("ns2:Description", namespace).text
    print(parts_name + "    " +  part_namber)