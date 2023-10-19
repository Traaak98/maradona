import glob

dossier_train = glob.glob("/media/apolline/B2C2CC8EC2CC586D/apolline/Ecole/ENSTA/M2/UE52-VS-IK/maradona/YOLODataset_simimages/data/Ball/images/train/*.png")
dossier_valid = glob.glob("/media/apolline/B2C2CC8EC2CC586D/apolline/Ecole/ENSTA/M2/UE52-VS-IK/maradona/YOLODataset_simimages/data/Ball/images/val/*.png")

fichier_train = open("train.txt", "w")
fichier_valid = open("valid.txt", "w")

for name in dossier_train:
    fichier_train.write(name+"\n")

for name in dossier_valid:
    fichier_valid.write(name+"\n")

fichier_train.close()
fichier_valid.close()