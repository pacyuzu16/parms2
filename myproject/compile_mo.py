from babel.messages.mofile import write_mo
from babel.messages.pofile import read_po

pairs = [
    ("locale/fr/LC_MESSAGES/django.po", "locale/fr/LC_MESSAGES/django.mo"),
    ("locale/rw/LC_MESSAGES/django.po", "locale/rw/LC_MESSAGES/django.mo"),
]
for po_path, mo_path in pairs:
    with open(po_path, "rb") as f:
        catalog = read_po(f)
    with open(mo_path, "wb") as f:
        write_mo(f, catalog)
    print("Compiled: " + mo_path)
print("Done.")
