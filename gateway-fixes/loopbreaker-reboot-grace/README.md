# Restart-Loop-Breaker: Host-Reboot-Grace

Optionaler Patch fuer das Hermes-Runtime-File `gateway/restart_loop_guard.py`.
Betrifft nur Installationen, die den Auto-Resume Restart-Loop-Breaker der Hermes-Runtime
nutzen. Das Kit selbst aendert sich nicht; der Patch wird vom Betreiber bewusst angewendet.

## Problem

Der Breaker verkettet "restart-interrupted" Gateway-Boots (Schwelle 3, kein Gap groesser
als 300s) und schaltet Auto-Resume ab, sobald die Kette die Schwelle erreicht. Er ist
periodenagnostisch und kann eine LEGITIME Host-Reboot-Kaskade (mehrere Gateway-Slots
starten beim Hochfahren schnell hintereinander) nicht von einem selbstverschuldeten
Respawn-Loop unterscheiden. Folge: nach einem Host-Reboot bleibt Auto-Resume aus, bis
`<HERMES_HOME>/gateway/restart_loop.json` manuell geloescht wird.

## Fix

Boots, die innerhalb von `DEFAULT_REBOOT_GRACE_SECONDS` (120s) nach dem Hochkommen des
Hosts passieren (System-Uptime aus `/proc/uptime`), gelten als Teil eines echten Reboots.
Sie verlaengern die Loop-Kette nicht, sondern setzen sie auf genau diesen Boot zurueck.

Sicherheitseigenschaften:
- Echter Crash-Loop auf lang laufendem Host (hohe Uptime): unveraendert hart gekappt, kein Bypass.
- Unlesbare `/proc/uptime`: fail closed, Verhalten wie der alte Breaker.
- Abschaltbar: `reboot_grace_seconds=0` (Argument oder Konstante) stellt das alte Verhalten her.
- Neue Parameter sind keyword-only mit Defaults, bestehende Aufrufer brechen nicht.

## Dateien

- `restart_loop_guard.reboot-grace.patch`: Unified-Diff (`-p1`) gegen
  `gateway/restart_loop_guard.py` im Hermes-Install.
- `restart_loop_guard.patched.py`: Referenz-Endversion, die der Patch reproduziert.
- `tests/test_loopbreaker_reboot_grace.py`: stdlib-`unittest`, laedt die Referenz-Endversion
  direkt (kein Hermes-Install noetig).

## Anwenden (Opt-in, Betreiber)

Der Patch wurde gegen den Upstream-Stand von `gateway/restart_loop_guard.py` erzeugt
(NousResearch/hermes-agent, main, Commit 63d0b94). Weicht deine installierte Version ab,
schlaegt `git apply --check` fehl; dann den Patch NICHT erzwingen, sondern die drei Hunks
manuell uebernehmen oder auf ein Upstream-Update warten.

    cd <HERMES_INSTALL_DIR>
    cp gateway/restart_loop_guard.py /root/restart_loop_guard.py.bak
    git apply --check -p1 /pfad/zu/restart_loop_guard.reboot-grace.patch
    git apply -p1 /pfad/zu/restart_loop_guard.reboot-grace.patch
    python3 -m py_compile gateway/restart_loop_guard.py
    diff gateway/restart_loop_guard.py /pfad/zu/restart_loop_guard.patched.py

Erwartete Abweichung beim `diff`: genau eine Kommentarzeile (ein Sonderzeichen in einem
Upstream-Kommentar wurde in der Referenz durch ein einfaches Minus ersetzt). Sonst identisch.

Danach die Gateways neu starten. Der Aufruf `check_and_record(...)` im Gateway braucht
keine Aenderung, die Grace ist per Default aktiv (ausser er setzt `reboot_grace_seconds=0`).
Ein Hermes-Update kann den Patch ueberschreiben; nach Updates erneut pruefen.

## Tests

    python3 -m unittest tests.test_loopbreaker_reboot_grace -v

Nicht verifiziert: Verhalten unter einem echten Host-Reboot mit realem `/proc/uptime`
(die Tests injizieren Uptime-Werte). Das Fenster von 120s ist ein Startwert; erzeugen
Reboots auf deinem System laengere Boot-Kaskaden, die Konstante erhoehen.
