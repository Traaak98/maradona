<img align="right" src="images/cat.gif" alt="Éditer sur GitLab" width="350px"/>  

# Maradonna


### Auteurs
* DE VAULCHIER Apolline <apolline.de_vaulchier@ensta-bretagne.org> (Promotion ENSTA Bretagne 2024 - Spécialité Robotique Autonome)
* Clara Gondot <clara.gondot@ensta-bretagne.org> (Promotion ENSTA Bretagne 2024 - Spécialité Robotique Autonome)

### Description
Imaginer un futur où les NAO remplacent les joueurs de foot. 

* Objectif principal : faire marquer un but par Nao en utilisant un asservissement visuel.
* Deuxième objectif : faire la passe à un Nao qui ensuite marque 
* Objectifs ultimes : lui apprendre le tacle et simuler la foulure.

### Logiciels
* Simulation sur V-REP
* Environnement virtuel sous python 2.7
* Utilisation de yolov3 : https://github.com/hjinnkim/yolov3-python2.7


## Sommaire
1. [Structure du Git](#structure-du-git)
2. [Informations générales](#informations-générales)
	1. [État du projet](#état-du-projet)
	2. [Travail effectué](#travail-effectué)
	3. [Travail en cours](#travail-en-cours)
3. [Fonctionnement de la FSM](#fonctionnement-de-la-fsm)
4. [Guide d'utilisation](#guide-dutilisation)
   1. [Lancer le robot en simulation](#lancer-le-robot-en-simulation)
   2. [Lancer le robot réel](#lancer-le-robot-réel)
   3. [Passage filmé](#passage-filmé)

## Structure du Git
Le répertoire GitLab contient les dossiers suivants :
* **images** : contient les images utilisées dans le README.
* **YoloDataset_simimages** : contient les images utilisées pour l'entrainement de Yolov3 et le modèle entrainé.
* **src** : contient les fichiers python utilisés pour le projet.
