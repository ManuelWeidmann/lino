# -*- coding: UTF-8 -*-
# Copyright 2014 Luc Saffre
# License: BSD (see file COPYING for details)

from __future__ import unicode_literals

from django.conf import settings
from lino import dd, rt
from lino.utils import Cycler
from lino.ad import _


def objects():

    polls = rt.modules.polls

    name = dd.str2kw('name', _("Acquired"))['name']
    acquired = polls.ChoiceSet.objects.get(name=name)

    USERS = Cycler(settings.SITE.user_model.objects.all())

    def poll(choiceset, title, details, questions):
        obj = polls.Poll(
            user=USERS.pop(),
            title=title.strip(),
            details=details.strip(),
            state=polls.PollStates.published,
            questions_to_add=questions,
            default_choiceset=choiceset)
        obj.full_clean()
        obj.save()
        obj.after_ui_save(None)
        return obj

    yield poll(
        acquired,
        "Pour commencer ma recherche d'emploi, je dois", """
Veuillez sélectionner votre réponse pour chaque question
""", """
Avoir une farde de recherche d’emploi organisée
Réaliser mon curriculum vitae
Savoir faire une lettre de motivation adaptée au poste de travail visé
Respecter les modalités de candidature
Me créer une boite e-mail appropriée à la recherche d’emploi
Créer mon compte sur le site de Forem
Mettre mon curriculum vitae sur le site du Forem
Connaître les aides à l’embauche qui me concernent
Etre préparé à l’entretien d’embauche ou téléphonique
""")

    yield poll(
        acquired,
        "Est-ce que je sais...", """
Veuillez sélectionner votre réponse pour chaque question
""", """
Utiliser le site du Forem pour consulter les offres d’emploi
Décoder une offre d’emploi
Adapter mon curriculum vitae par rapport à une offre ou pour une candidature spontanée
Réaliser une lettre de motivation suite à une offre d’emploi
Adapter une lettre de motivation par rapport à l’offre d’emploi
Réaliser une lettre de motivation spontanée
Utiliser le fax pour envoyer mes candidatures
Utiliser ma boite e-mail pour envoyer mes candidatures
Mettre mon curriculum vitae en ligne sur des sites d’entreprise
Compléter en ligne les formulaires de candidature
M’inscrire aux agences intérim via Internet
M’inscrire auprès d’agence de recrutement via Internet
Utiliser Internet pour faire des recherches sur une entreprise
Préparer un entretien d’embauche (questions, argumentation du C.V.,…)
Utiliser Internet pour gérer ma mobilité (transport en commun ou itinéraire voiture)
Utiliser la photocopieuse (ex : copie de lettre de motivation que j’envoie par courrier)
Utiliser le téléphone pour poser ma candidature
Utiliser le téléphone pour relancer ma candidature
"Trouver et imprimer les formulaires de demandes d’aides à l’embauche se trouvant 
sur le site de l’ONEm"

""")
