"""Catalogue d'émoticônes et remplacement des raccourcis clavier (« :) » → 🙂), pur Python."""

# (caractère, nom, raccourcis, catégorie)
EMOJIS = [
    ("😀", "Grand sourire", [":D", ":grin:"], "Visages"),
    ("🙂", "Sourire", [":)", ":smile:"], "Visages"),
    ("😉", "Clin d'œil", [";)", ":wink:"], "Visages"),
    ("😂", "Mort de rire", [":joy:"], "Visages"),
    ("😍", "Yeux en cœur", [":love:"], "Visages"),
    ("😛", "Langue tirée", [":P", ":tongue:"], "Visages"),
    ("😎", "Lunettes de soleil", ["B)", ":cool:"], "Visages"),
    ("😇", "Auréole", ["O:)", ":angel:"], "Visages"),
    ("😈", "Diablotin", [">:)", ":devil:"], "Visages"),
    ("🙁", "Triste", [":(", ":sad:"], "Visages"),
    ("😢", "Larme", [":'(", ":cry:"], "Visages"),
    ("😮", "Surpris", [":o", ":O"], "Visages"),
    ("😐", "Neutre", [":|", ":neutral:"], "Visages"),
    ("😕", "Perplexe", [":/", ":confused:"], "Visages"),
    ("🤔", "Réflexion", [":think:"], "Visages"),
    ("😴", "Endormi", [":zzz:"], "Visages"),
    ("😡", "En colère", [":angry:"], "Visages"),
    ("😱", "Effrayé", [":scream:"], "Visages"),
    ("🥳", "Fête", [":party:"], "Visages"),
    ("👍", "Pouce levé", ["(y)", ":+1:"], "Gestes"),
    ("👎", "Pouce baissé", ["(n)", ":-1:"], "Gestes"),
    ("👏", "Applaudissements", [":clap:"], "Gestes"),
    ("🙏", "Mains jointes", [":pray:"], "Gestes"),
    ("👋", "Salut", [":wave:"], "Gestes"),
    ("💪", "Biceps", [":muscle:"], "Gestes"),
    ("✌️", "Victoire", [":v:"], "Gestes"),
    ("👌", "OK", [":ok:"], "Gestes"),
    ("❤️", "Cœur", ["<3", ":heart:"], "Symboles"),
    ("💔", "Cœur brisé", ["</3", ":broken:"], "Symboles"),
    ("⭐", "Étoile", [":star:"], "Symboles"),
    ("✅", "Validé", [":check:"], "Symboles"),
    ("❌", "Refusé", [":x:"], "Symboles"),
    ("⚠️", "Attention", [":warning:"], "Symboles"),
    ("❓", "Question", [":?:"], "Symboles"),
    ("❗", "Important", [":!:"], "Symboles"),
    ("💡", "Idée", [":idea:"], "Symboles"),
    ("🔥", "Feu", [":fire:"], "Symboles"),
    ("⚡", "Éclair", [":zap:"], "Symboles"),
    ("🎯", "Cible", [":target:"], "Symboles"),
    ("🚀", "Fusée", [":rocket:"], "Symboles"),
    ("🏁", "Arrivée", [":finish:"], "Symboles"),
    ("📌", "Épingle", [":pin:"], "Symboles"),
    ("🔒", "Cadenas", [":lock:"], "Symboles"),
    ("➡️", "Flèche droite", [":arrow:"], "Symboles"),
    ("✨", "Étincelles", [":sparkles:"], "Symboles"),
    ("⏰", "Réveil", [":clock:"], "Symboles"),
    ("📅", "Calendrier", [":calendar:"], "Objets"),
    ("📧", "Courriel", [":mail:"], "Objets"),
    ("📞", "Téléphone", [":phone:"], "Objets"),
    ("💻", "Ordinateur", [":computer:"], "Objets"),
    ("📎", "Trombone", [":clip:"], "Objets"),
    ("📝", "Bloc-notes", [":memo:"], "Objets"),
    ("📚", "Livres", [":books:"], "Objets"),
    ("💰", "Argent", [":money:"], "Objets"),
    ("🎁", "Cadeau", [":gift:"], "Objets"),
    ("🏆", "Trophée", [":trophy:"], "Objets"),
    ("☀️", "Soleil", [":sun:"], "Nature"),
    ("🌙", "Lune", [":moon:"], "Nature"),
    ("☁️", "Nuage", [":cloud:"], "Nature"),
    ("🌧️", "Pluie", [":rain:"], "Nature"),
    ("🌳", "Arbre", [":tree:"], "Nature"),
    ("🌸", "Fleur", [":flower:"], "Nature"),
    ("🐱", "Chat", [":cat:"], "Nature"),
    ("🐶", "Chien", [":dog:"], "Nature"),
]
CATEGORIES = list(dict.fromkeys(e[3] for e in EMOJIS))

# plus longs d'abord : « O:) » doit l'emporter sur « :) »
_SHORTCUTS = sorted(((s, e[0]) for e in EMOJIS for s in e[2]), key=lambda t: -len(t[0]))


def replace_shortcut(text):
    """Si `text` se termine par un raccourci isolé (début de texte ou espace avant), le remplace.

    Renvoie le nouveau texte, ou None s'il n'y a rien à remplacer.
    """
    for shortcut, char in _SHORTCUTS:
        if text.endswith(shortcut):
            head = text[:-len(shortcut)]
            if not head or head[-1].isspace():
                return head + char
    return None


def search(query="", category=None):
    """Émoticônes dont le nom, un raccourci ou le caractère contient `query` (catégorie optionnelle)."""
    q = query.strip().lower()
    return [e for e in EMOJIS
            if (category is None or e[3] == category)
            and (not q or q in e[1].lower() or q in e[0] or any(q in s.lower() for s in e[2]))]
