# -*- coding: utf-8 -*-
"""Testet die Anreicherung gegen den bestehenden Bestand.

Die 231 Eintraege sind selbst geschrieben und damit der Massstab. Der Test
nimmt ein paar davon heraus, laesst sie neu erzeugen und stellt Original und
Neufassung nebeneinander.

    python3 scripts/eval_enrichment.py --prepare        # Holdout in die Inbox legen
    # dann die Anreicherung laufen lassen (Workflow oder lokal)
    python3 scripts/eval_enrichment.py --compare        # Ergebnis gegenueberstellen
    python3 scripts/eval_enrichment.py --cleanup        # Reste wegraeumen

Bewusst kein automatischer Score: ob ein Mundartsatz sitzt, entscheidet das
Ohr. Der Test spart nur die Sucharbeit und macht die Stichprobe wiederholbar.
"""
import argparse
import json
import random
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MAIN = ROOT / "habedere.json"
INBOX = ROOT / "inbox"
EVAL = ROOT / "eval"
GOLD = EVAL / "gold.json"

FIELDS = ("word", "pronunciation", "phrase", "translation")
SEED = 20260910          # feste Stichprobe, damit Laeufe vergleichbar bleiben


def load_words():
    return json.loads(MAIN.read_text(encoding="utf-8"))["austrian_words"]


def cmd_prepare(n):
    words = load_words()
    rng = random.Random(SEED)
    sample = rng.sample(words, min(n, len(words)))

    EVAL.mkdir(exist_ok=True)
    GOLD.write_text(json.dumps(sample, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")

    for i, entry in enumerate(sample):
        path = INBOX / f"eval_{i:02d}.json"
        path.write_text(json.dumps({"word": entry["word"]},
                                   indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")

    print(f"{len(sample)} Stichwoerter in die Inbox gelegt, Originale in {GOLD.name}.")
    print("Die Eintraege stehen weiterhin in habedere.json - der Merge wird sie")
    print("darum als Dubletten ueberspringen. Genau so soll es sein: zum")
    print("Vergleichen reichen die ergaenzten Inbox-Dateien.")
    for e in sample:
        print(f"  {e['word']}")
    return 0


def cmd_compare():
    if not GOLD.exists():
        print("Kein Holdout gefunden - erst --prepare laufen lassen.")
        return 1
    gold = {e["word"]: e for e in json.loads(GOLD.read_text(encoding="utf-8"))}

    produced = {}
    for path in sorted(INBOX.glob("eval_*.json")):
        try:
            entry = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        if entry.get("word") in gold:
            produced[entry["word"]] = entry

    if not produced:
        print("Keine ergaenzten eval_*.json in der Inbox. Lief die Anreicherung?")
        return 1

    offen = [w for w in gold if w not in produced]
    fertig = 0

    for word, orig in gold.items():
        neu = produced.get(word)
        if not neu:
            continue
        fehlend = [f for f in FIELDS if not str(neu.get(f, "")).strip()]
        print("=" * 72)
        print(word + ("   [unvollstaendig: " + ", ".join(fehlend) + "]" if fehlend else ""))
        for f in FIELDS[1:]:
            a, b = orig.get(f, ""), neu.get(f, "")
            gleich = "=" if a.strip() == b.strip() else " "
            print(f"  {f:<14} alt {gleich} {a}")
            print(f"  {'':<14} neu   {b}")
        if not fehlend:
            fertig += 1

    print("=" * 72)
    print(f"{fertig} von {len(gold)} vollstaendig ergaenzt.")
    if offen:
        print(f"Nicht bearbeitet: {', '.join(offen)}")
    print()
    print("Lies die Paare durch. Die Frage ist nicht, ob die Neufassung dem")
    print("Original gleicht - zwei gute Saetze duerfen verschieden sein -,")
    print("sondern ob du die neue Zeile so aufs Display lassen wuerdest.")
    return 0


def cmd_cleanup():
    weg = list(INBOX.glob("eval_*.json"))
    for p in weg:
        p.unlink()
    if EVAL.exists():
        shutil.rmtree(EVAL)
    print(f"{len(weg)} Inbox-Dateien und {EVAL.name}/ entfernt.")
    return 0


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--prepare", action="store_true")
    g.add_argument("--compare", action="store_true")
    g.add_argument("--cleanup", action="store_true")
    ap.add_argument("-n", type=int, default=20, help="Groesse der Stichprobe")
    args = ap.parse_args()
    if args.prepare:
        return cmd_prepare(args.n)
    if args.compare:
        return cmd_compare()
    return cmd_cleanup()


if __name__ == "__main__":
    sys.exit(main())
