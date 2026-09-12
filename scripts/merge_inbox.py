# -*- coding: utf-8 -*-
"""Inbox pruefen und in habedere.json uebernehmen.

Zwei Modi:

  --report   Was liegt in der Inbox, und fehlen Felder? Schreibt
             needs_enrichment nach $GITHUB_OUTPUT.
  --merge    Validieren, anhaengen, Dubletten ueberspringen, Inbox leeren.

Die Trennung ist Absicht: das Sprachmodell fuellt nur die fehlenden Felder in
der Inbox-Datei aus. habedere.json aendert ausschliesslich dieses Skript, und
nur was hier durch die Pruefung kommt. So kann ein Fehlgriff des Modells die
Hauptliste nicht beschaedigen.
"""
import argparse
import glob
import json
import os
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "habedere.json"
INBOX = ROOT / "inbox"

FIELDS = ("word", "pronunciation", "phrase", "translation")

# Grenzen aus dem Bestand: Maximum plus etwas Luft. Laengere Eintraege passen
# im Quadranten nicht mehr lesbar aufs Display.
LIMITS = {"word": 40, "pronunciation": 50, "phrase": 90, "translation": 100}
SENTENCE_END = ".!?"


def load_main():
    data = json.loads(MAIN.read_text(encoding="utf-8"))
    return data, data["austrian_words"]


def key(word):
    """Vergleichsform fuer Dublettenpruefung."""
    s = unicodedata.normalize("NFKD", word.lower())
    return re.sub(r"[^a-z0-9äöüß]", "", s)


def inbox_files():
    return sorted(glob.glob(str(INBOX / "*.json")))


def read_entry(path):
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return None, f"kein gueltiges JSON ({e})"
    if isinstance(raw, list):
        return None, "Liste statt Objekt - bitte ein Wort pro Datei"
    if not isinstance(raw, dict):
        return None, "kein JSON-Objekt"
    return raw, None


def missing_fields(entry):
    return [f for f in FIELDS if not str(entry.get(f, "")).strip()]


def validate(entry, existing_keys):
    """Harte Fehler (Liste) und weiche Hinweise (Liste) zurueckgeben."""
    errors, warnings = [], []

    for f in FIELDS:
        v = entry.get(f)
        if not isinstance(v, str) or not v.strip():
            errors.append(f"{f} fehlt oder ist leer")
        elif len(v) > LIMITS[f]:
            errors.append(f"{f} ist {len(v)} Zeichen lang, erlaubt sind {LIMITS[f]}")

    extra = [k for k in entry if k not in FIELDS]
    if extra:
        errors.append(f"unbekannte Felder: {extra}")
    if errors:
        return errors, warnings

    if key(entry["word"]) in existing_keys:
        errors.append(f"'{entry['word']}' steht schon in der Liste")

    for f in ("phrase", "translation"):
        if entry[f][-1] not in SENTENCE_END:
            warnings.append(f"{f} endet nicht auf . ! oder ?")

    # Im Bestand steht das Stichwort in 209 von 232 Beispielsaetzen. Kein
    # Muss - bei Redewendungen weicht die Beugung ab -, aber einen Hinweis wert.
    stem = key(entry["word"].split()[0])[:5]
    if stem and stem not in key(entry["phrase"]):
        warnings.append("Stichwort taucht im Beispielsatz nicht auf")

    if key(entry["phrase"]) == key(entry["translation"]):
        errors.append("phrase und translation sind identisch")

    return errors, warnings


def emit_output(name, value):
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as f:
            f.write(f"{name}={value}\n")


def cmd_report():
    files = inbox_files()
    if not files:
        print("Inbox ist leer.")
        emit_output("needs_enrichment", "false")
        emit_output("has_files", "false")
        return 0

    needs = False
    for path in files:
        entry, err = read_entry(path)
        name = Path(path).name
        if err:
            print(f"  {name}: {err}")
            continue
        miss = missing_fields(entry)
        word = entry.get("word", "?")
        if miss:
            needs = True
            print(f"  {name}: '{word}' - es fehlen {', '.join(miss)}")
        else:
            print(f"  {name}: '{word}' - vollstaendig")

    emit_output("needs_enrichment", "true" if needs else "false")
    emit_output("has_files", "true")
    return 0


# TRMNL lehnt Nutzdaten ueber 100 KB ab und setzt das Plugin dann auf
# "degraded" - es holt gar nichts mehr, bis man die Gesundheit von Hand
# zuruecksetzt. habedere.json geht als Ganzes raus, weil die Vorlage den Index
# selbst rechnet und dafuer die Liste braucht. Also mitzaehlen.
TRMNL_MAX = 100 * 1024
TRMNL_WARN = 80 * 1024


def warn_groesse():
    size = MAIN.stat().st_size
    anteil = size / TRMNL_MAX * 100
    print(f"{MAIN.name}: {size} Bytes, {anteil:.0f} % von TRMNLs 100-KB-Grenze.")
    if size >= TRMNL_WARN:
        je = size // max(1, len(json.loads(
            MAIN.read_text(encoding="utf-8"))["austrian_words"]))
        print(f"  Achtung: nur noch rund {(TRMNL_MAX - size) // max(1, je)} "
              f"Eintraege Luft. Darueber holt das Display gar nichts mehr.")
        print("  Ausweg: nur den Eintrag des Tages ausliefern, wie mythai es")
        print("  macht (dort schreibt refresh.py eine zweite, kleine Datei).")


def cmd_merge():
    files = inbox_files()
    if not files:
        print("Nichts zu uebernehmen.")
        emit_output("changed", "false")
        return 0

    data, words = load_main()
    existing = {key(w["word"]) for w in words}
    added, skipped = [], []

    for path in files:
        name = Path(path).name
        entry, err = read_entry(path)
        if err:
            skipped.append((name, err))
            continue

        errors, warnings = validate(entry, existing)
        for w in warnings:
            print(f"  Hinweis {name}: {w}")
        if errors:
            skipped.append((name, "; ".join(errors)))
            continue

        clean = {f: entry[f].strip() for f in FIELDS}
        words.append(clean)
        existing.add(key(clean["word"]))
        added.append(clean["word"])
        os.remove(path)

    if added:
        data["austrian_words"] = words
        MAIN.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    for name, why in skipped:
        print(f"  UEBERSPRUNGEN {name}: {why}")
    print(f"Aufgenommen: {len(added)} ({', '.join(added) or '-'}), "
          f"liegen geblieben: {len(skipped)}, Bestand: {len(words)}")
    warn_groesse()

    emit_output("changed", "true" if added else "false")
    emit_output("added", ", ".join(added))
    # Liegengebliebene Dateien sind kein Job-Fehler: sie bleiben in der Inbox
    # und koennen von Hand korrigiert werden.
    return 0


def cmd_dedupe():
    data, words = load_main()
    seen, out, dropped = set(), [], []
    for w in words:
        k = key(w["word"])
        if k in seen:
            dropped.append(w["word"])
            continue
        seen.add(k)
        out.append(w)
    if dropped:
        data["austrian_words"] = out
        MAIN.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print(f"Dubletten entfernt: {dropped or '-'} (Bestand: {len(out)})")
    return 0


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--report", action="store_true")
    g.add_argument("--merge", action="store_true")
    g.add_argument("--dedupe", action="store_true")
    args = ap.parse_args()
    if args.report:
        return cmd_report()
    if args.merge:
        return cmd_merge()
    return cmd_dedupe()


if __name__ == "__main__":
    sys.exit(main())
