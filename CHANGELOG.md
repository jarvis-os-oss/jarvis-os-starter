# Starter-Kit Sync-Changelog

Nachvollziehbarkeits-Log des regelmaessigen Abgleichs gegen das getrackte Upstream-Repo. Jeder Eintrag haelt fest, welche Upstream-Commits geprueft und wie sie klassifiziert wurden (auch wenn noch nicht umgesetzt). Wird vom Sync-Skript erzeugt, nicht manuell.

Dies ist eine neutrale Vorlage. Reale Eintraege entstehen erst zur Laufzeit in der jeweiligen Instanz und referenzieren dort ausschliesslich das lokal konfigurierte Upstream-Repo.

## Beispiel-Eintrag (Vorlage)

## JJJJ-MM-TT - Sync-Lauf (upstream main &lt;from-sha&gt;..&lt;to-sha&gt;)

Geprueft: N neue Commits. Nachziehen: a, bewusst nicht: b, Entscheidung noetig: c.

- `<commit-sha>` <commit-titel>
  - Verdikt: SOLLTE NACHGEZOGEN WERDEN | BEWUSST NICHT UEBERNEHMEN | ENTSCHEIDUNG NOETIG
  - Grund: <generische Klassifikationsbegruendung, z.B. "Security/Infra-Signal", "generischer Bugfix", "Feature/Erweiterung - kein Muss fuers Kit">
  - Dateien: <betroffene Pfade>

Report an den Nutzer: JA/NEIN (Zahl der Nachzieh-Kandidaten - Freigabe pro Fall).
