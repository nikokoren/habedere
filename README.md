# habedere

Steirisch-oesterreichische Woerter fuer ein TRMNL-Display. `habedere.json` wird
von der Plugin-Vorlage abgeholt, die sich daraus jeden Tag ein Wort zieht.

```
habedere.json                 das einzige Artefakt, das TRMNL liest
inbox/                        Ablage fuer neue Woerter (der Shortcut schreibt hierher)
scripts/merge_inbox.py        pruefen und uebernehmen
scripts/eval_enrichment.py    Stichprobe gegen den Bestand
.claude/skills/enrich-word/   die Anweisung, nach der ergaenzt wird
trmnl/                        die TRMNL-Vorlage und was sie erwartet
```

Ein Eintrag:

```json
{
  "word": "Bartwisch",
  "pronunciation": "BOAT-wisch",
  "phrase": "Geh, gib ma den Bartwisch, i muaß do schnell wos zammkehrn.",
  "translation": "Gib mir bitte den Besen, ich muss hier kurz etwas zusammenkehren."
}
```

`translation` ist die hochdeutsche Entsprechung **des Beispielsatzes**, nicht
eine Woerterbuch-Definition des Stichworts.

## Ein neues Wort aufnehmen

Der Shortcut legt eine Datei in `inbox/` ab. Es reicht das Stichwort:

```json
{ "word": "Kudelmudel" }
```

Steht schon alles drin, wird nichts ergaenzt - der Eintrag geht direkt durch
die Pruefung.

Der Push loest `Neues Wort aufnehmen` aus:

1. `merge_inbox.py --report` sieht nach, ob Felder fehlen.
2. Nur dann startet Claude Code und ergaenzt **die Inbox-Datei**, nach der
   Anweisung in `.claude/skills/enrich-word/SKILL.md`. Als Massstab liest es
   vorher den vorhandenen Bestand.
3. `merge_inbox.py --merge` validiert und haengt an `habedere.json` an.

Die Trennung ist der Kern: das Sprachmodell fasst `habedere.json` nie an. Was
die Pruefung nicht besteht, bleibt in der Inbox liegen und laesst sich von
Hand nachbessern - der Lauf schlaegt deswegen nicht fehl.

Abgelehnt wird: fehlende oder leere Felder, unbekannte Felder, ein Wort das
schon in der Liste steht (Vergleich ohne Gross-/Kleinschreibung und
Sonderzeichen), zu lange Felder (Wort 40, Aussprache 50, Satz 90, Uebersetzung
100 Zeichen), identischer Mundart- und Hochdeutschsatz, kaputtes JSON.
Als Hinweis, aber nicht als Ablehnungsgrund: fehlendes Satzzeichen, oder ein
Beispielsatz ohne das Stichwort (bei Redewendungen weicht die Beugung ab).

### Einrichtung

Die Anreicherung laeuft ueber das Claude-Abo, nicht ueber API-Guthaben. Dafuer
braucht das Repository ein Secret:

1. `claude setup-token` lokal ausfuehren. Der Befehl oeffnet den Browser und
   gibt danach ein Token aus - **es wird nirgends gespeichert**, also gleich
   kopieren. Ein Jahr gueltig, setzt Pro, Max, Team oder Enterprise voraus.
2. Unter Settings -> Secrets and variables -> Actions als
   `CLAUDE_CODE_OAUTH_TOKEN` hinterlegen.

Laeuft das Token ab, ergaenzt der Workflow nichts mehr; die Dateien bleiben in
der Inbox liegen. Ein Kalendereintrag auf das Ablaufdatum erspart die
Fehlersuche.

## Taugt die Anreicherung was?

Die vorhandenen Eintraege sind selbst geschrieben und damit der Massstab:

```sh
python3 scripts/eval_enrichment.py --prepare -n 20   # Stichprobe in die Inbox
# Anreicherung laufen lassen (Workflow oder lokal)
python3 scripts/eval_enrichment.py --compare         # alt und neu nebeneinander
python3 scripts/eval_enrichment.py --cleanup
```

Die Stichprobe ist fest gesetzt (Seed), damit zwei Laeufe vergleichbar sind.
Einen automatischen Punktwert gibt es nicht - ob ein Mundartsatz sitzt,
entscheidet das Ohr. Die Frage beim Durchlesen ist nicht, ob die Neufassung
dem Original gleicht, sondern ob sie so aufs Display duerfte.

## Die Tagesauswahl

Die Vorlage rechnet selbst:

```liquid
day_index  = local_seconds / 86400
idx        = day_index modulo pool_size
item       = austrian_words[idx]
```

Ein Schritt pro Tag durch das Array, Wechsel um lokal Mitternacht. Die
Reihenfolge in `habedere.json` ist damit die Reihenfolge der Tage. Der Bestand
liegt in gemischter Reihenfolge, darum fallen keine thematischen Bloecke auf.
Neue Woerter haengen hinten an und kommen entsprechend am Ende des Durchlaufs.

### Warum refresh.yml nicht entfallen darf

TRMNL erzeugt einen Screen **nur dann neu, wenn sich die Nutzdaten geaendert
haben** ("skips generating screens if the merge variables are the same between
requests"). Die Vorlage liest `last_updated` zwar nicht - aber der Zeitstempel
ist die einzige taegliche Aenderung an der Datei und loest damit den Wechsel
aus. Ohne diesen Lauf bliebe dasselbe Wort stehen, egal was die Vorlage
rechnet.

Der Cron steht auf `5 23 * * *`: 00:05 MEZ im Winter, 01:05 MESZ im Sommer,
also ganzjaehrig kurz nach lokaler Mitternacht. Eine feste UTC-Zeit kann wegen
der Sommerzeit nicht in beiden Halbjahren exakt Mitternacht treffen. Frueher
stand hier `0 * * * *` - stuendlich, trotz des Kommentars "Midnight UTC", also
24 Nutzdaten-Aenderungen und damit 24 Screen-Renderings pro Tag fuer ein
einziges neues Wort.

Beide schreibenden Workflows teilen sich eine `concurrency`-Gruppe, damit sie
sich nicht gegenseitig den Push zerschiessen.
