import glob

dossier = glob.glob("*.txt")

for name in dossier:
    fichier = open(name, "r")
    contenu = fichier.read()
    fichier.close()
    contenu = contenu.split()

    # Calcul des valeurs centre, width, height
    center_x = float(contenu[0]) + (float(contenu[2]) - float(contenu[0])) / 2
    center_y = float(contenu[1]) + (float(contenu[7]) - float(contenu[1])) / 2
    width = float(contenu[2]) - float(contenu[0])
    height = float(contenu[7]) - float(contenu[1])

    #Ecriture dans le fichier
    new_ligne = "0 " + str(center_x) + " " + str(center_y) + " " + str(width) + " " + str(height)
    fichier = open(name, "w")
    contenu[1] = str(float(contenu[1]) + 0.5)
    contenu[2] = str(float(contenu[2]) + 0.5)
    fichier = open("new/" + name, "w")
    fichier.write(new_ligne)
    fichier.close()
