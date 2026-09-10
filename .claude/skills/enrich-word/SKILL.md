---
name: enrich-word
description: Fuellt fehlende Felder in inbox/*.json aus - Aussprache, Mundartsatz und hochdeutsche Entsprechung zu einem steirisch-oesterreichischen Stichwort. Wird vom Workflow "Neues Wort aufnehmen" aufgerufen, wenn eine Inbox-Datei nur das Wort enthaelt.
allowed-tools: Read, Write, Edit, Glob, Bash(python3 scripts/merge_inbox.py --report)
---

# Neues Wort ergaenzen

Eine Datei in `inbox/` enthaelt ein steirisches bzw. oesterreichisches Wort,
oft nur das Feld `word`. Ergaenze die fehlenden Felder - und sonst nichts.

## Ablauf

1. `python3 scripts/merge_inbox.py --report` zeigt, welche Dateien offen sind
   und welche Felder fehlen.
2. **Lies zuerst `habedere.json`.** Die 231 vorhandenen Eintraege sind der
   Massstab fuer Ton, Registerhoehe und Satzlaenge. Such dir vor dem Schreiben
   ein paar Eintraege heraus, die dem neuen Wort aehneln (gleiche Wortart,
   aehnliche Alltagssituation), und richte dich danach.
3. Schreib die fehlenden Felder in die Inbox-Datei zurueck. `word` bleibt
   unveraendert.
4. `habedere.json` **nicht** anfassen. Das Uebernehmen macht danach
   `scripts/merge_inbox.py --merge`, und nur was dort durch die Pruefung geht.

## Die vier Felder

```json
{
  "word": "Bartwisch",
  "pronunciation": "BOAT-wisch",
  "phrase": "Geh, gib ma den Bartwisch, i muaß do schnell wos zammkehrn.",
  "translation": "Gib mir bitte den Besen, ich muss hier kurz etwas zusammenkehren."
}
```

**`word`** - unveraendert uebernehmen. Nur offensichtliche Tippfehler
korrigieren, und das im Zweifel lieber nicht.

**`pronunciation`** - eine Lesehilfe, keine Lautschrift. Silben mit
Bindestrich trennen, die betonte Silbe in GROSSBUCHSTABEN: `RIH-bisl`,
`SPAH-tsi`, `KLESCH-a`. Bei einsilbigen Woertern reicht das Wort in
Grossbuchstaben (`FAAD`). Bei Redewendungen eine lockere Sprechhilfe fuer die
ganze Wendung (`a HIRN wia a NUDL-sieb`). Kein IPA. Hoechstens 50 Zeichen.

**`phrase`** - ein Satz auf Steirisch/Oesterreichisch, in dem das Wort
tatsaechlich vorkommt, so wie er am Wirtshaustisch fallen wuerde. Dialektnah
schreiben (`i`, `ma`, `wos`, `net`, `ned`, `oa`), nicht hochdeutsch mit
eingestreutem Dialektwort. Ein Satz, hoechstens 90 Zeichen, endet auf `.`,
`!` oder `?`. Bei Redewendungen darf die Beugung vom Stichwort abweichen.

**`translation`** - **die hochdeutsche Entsprechung des Beispielsatzes**, nicht
eine Woerterbuch-Definition des Stichworts. Das ist der Fehler, der hier am
haeufigsten passiert. Sinngemaess uebersetzen, nicht Wort fuer Wort; die
Aussage soll auf Hochdeutsch genauso natuerlich klingen wie das Original auf
Steirisch. Hoechstens 100 Zeichen, gleiches Satzzeichen wie die `phrase`.

## Was bei Unsicherheit gilt

Wenn du dir bei der Bedeutung nicht sicher bist, **rate nicht**. Ein falscher
Eintrag faellt auf dem Display erst Monate spaeter auf und ist bis dahin
gelernt. Lass die Datei stattdessen unveraendert liegen und schreib in die
Zusammenfassung, was unklar ist - der Workflow laesst sie dann in der Inbox
liegen, und sie kann von Hand ergaenzt werden.

Dasselbe gilt, wenn das Wort gar nicht oesterreichisch ist, oder wenn es
mehrere weit auseinanderliegende Bedeutungen hat und aus der Eingabe nicht
hervorgeht, welche gemeint war.

## Laengen im Blick behalten

Der Eintrag landet im Quadranten eines 800x480-Displays. Kurze Saetze lesen
sich dort deutlich besser: das Stichwort bekommt rund 48 % der Hoehe, die
beiden Saetze teilen sich den Rest. Ein 90-Zeichen-Satz schrumpft auf 18px.
Im Bestand liegt der Median bei 28 Zeichen fuer die `phrase` und 32 fuer die
`translation` - daran orientieren.
