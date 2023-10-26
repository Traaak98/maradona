import glob

dossier = glob.glob("*.txt")

for name in dossier:
    fichier = open(name, "r")
    contenu = fichier.read()
    fichier.close()
    contenu = contenu.split()

    # Calcul des valeurs centre, width, height
    center_x = float(contenu[1]) + (float(contenu[3]) - float(contenu[1])) / 2
    center_y = float(contenu[2]) + (float(contenu[8]) - float(contenu[2])) / 2
    width = float(contenu[3]) - float(contenu[1])
    height = float(contenu[8]) - float(contenu[2])

    #Ecriture dans le fichier
    new_ligne = "0 " + str(center_x) + " " + str(center_y) + " " + str(width) + " " + str(height)
    fichier = open(name, "w")
    fichier = open("new/" + name, "w")
    fichier.write(new_ligne)
    fichier.close()
