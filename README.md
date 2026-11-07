<<<<<<< HEAD
# LEGO Companion

Ein Blender-Addon (ab Blender 4.0) für LEGO- und Stop-Motion-Animationsprojekte. Es sammelt mehrere Werkzeuge rund um organische Bewegungsverfeinerung, Stop-Motion-Timing, Transform-Bereinigung, Shader-Skalierung und den Import eines Floor-Generator-Objekts in einem Sidebar-Panel unter **View3D > Sidebar > LEGO Companion**.

## Inhalt

- [Organic Motion](#organic-motion)
- [Animation on 2s](#animation-on-2s)
- [Reset LEGO Delta Offset](#reset-lego-delta-offset)
- [Shader & Scale](#shader--scale)
  - [Node Scale Setter](#node-scale-setter)
  - [MecaFace Scale Patcher](#mecaface-scale-patcher)
  - [Shader Patcher (MMUA)](#shader-patcher-mmua)
- [Floor Generator Import](#floor-generator-import)

---

## Organic Motion

Fügt Kamera- und Pose-Bone-Rotationen zufälliges Noise über F-Curve-Modifier hinzu, damit mechanisch wirkende Animationen ein organischeres, weniger steifes Bewegungsgefühl erhalten.

- Getrennte Einstellungen für Kamera und Pose-Bones.
- Pro Achse (X, Y, Z) einzeln aktivierbar, mit eigenem **Scale**- und **Strength**-Wert.
- Fügt bei Bedarf automatisch Keyframes und eine Action hinzu, bevor der Noise-Modifier gesetzt wird.
- Zufälliger Phase- und Offset-Wert pro Achse, damit sich mehrere Objekte nicht synchron bewegen.
- "Reset"-Button, um die Standardwerte pro Kamera/Bone-Einstellung wiederherzustellen.
- "Apply"-Button, aktiv je nach Kontext (Kamera ausgewählt bzw. Pose-Mode mit ausgewählten Bones).

## Animation on 2s

Wandelt vorhandene Animationen in ein gestuftes Stop-Motion-Timing um ("on 2s", "on 3s" etc., frei einstellbar), wie es für klassische Stop-Motion-/LEGO-Optik typisch ist.

- **Step Size**: Anzahl der Frames, die jede Pose gehalten wird (1–24, Standard 2).
- **Respect Camera Switches**: Setzt an Kamera-Wechsel-Markern in der Timeline neue Stepping-Segmente an, damit der Wechselframe nicht "verschluckt" wird.
- **Selected Bones Only**: Beschränkt die Anwendung auf aktuell ausgewählte Pose-Bones der aktiven Armature.
- **Replace Existing On2s**: Entfernt vorher erzeugte On2s-Stepped-Modifier, bevor neue erzeugt werden, um Doppelungen zu vermeiden.
- Verarbeitet alle ausgewählten Objekte inklusive ihrer Actions, überspringt bereits verarbeitete Actions (z. B. bei geteilten Actions) und gibt eine detaillierte Konsolen-Zusammenfassung aus (bearbeitete Actions, F-Curves, entfernte/erstellte Modifier).
- Eigener Button **"Remove Step Modifiers"**, um alle zuvor gesetzten On2s-Modifier wieder vollständig zu entfernen.

## Reset LEGO Delta Offset

Setzt Delta Location und Delta Rotation aller ausgewählten Objekte auf 0 zurück.

- Wechselt bei Bedarf automatisch den Rotationsmodus (z. B. von Quaternion/Axis-Angle) auf XYZ-Euler, um Delta Rotation zuverlässig zurücksetzen zu können.
- Meldet die Anzahl der zurückgesetzten Objekte bzw. warnt, wenn keine Objekte ausgewählt sind.

## Shader & Scale

Sammlung von Werkzeugen zum Anpassen von Shader-Werten, wenn LEGO-Assets oder Materialien in einer anderen Skalierung verwendet werden als ursprünglich modelliert.

### Node Scale Setter

Setzt global den Wert einer benannten "Scale"-Value-Node im aktiven Material aller ausgewählten Mesh-Objekte.

- Sucht pro Objekt automatisch nach einer `ShaderNodeValue`-Node mit dem Label "Scale".
- Setzt den eingegebenen Zielwert direkt am Node-Output.
- Gibt zurück, bei wie vielen Objekten die Node gefunden bzw. nicht gefunden wurde.
- Standardwert: 0.01.

### MecaFace Scale Patcher

Patcht gezielt Node-Gruppen mit dem Basisnamen **MecaFace.Material** in allen Materialien der Szene – global und pro Node-Tree nur einmal.

- Sucht in der Node-Gruppe nach einer Noise-Texture mit Scale-Wert 3.75 (Noise-Texturen mit Scale 50 werden bewusst ignoriert) und setzt deren Scale auf `3.75 × Patcher-Scale-Wert`.
- Sucht eine Bevel-Node, deren Radius-Eingang bereits über eine Multiply-Node gespeist wird, und fügt davor eine zusätzliche Multiply-Node ein, die den Wert mit dem Patcher-Scale-Wert multipliziert (Bevel-Nodes ohne verkabelten Radius werden ignoriert).
- **Lock-Mechanismus**: Jeder gepatchte Node-Tree wird über eine Custom Property markiert, damit er nicht versehentlich mehrfach gepatcht wird.
- **Force Repatch**-Option, um die Sperre bei Bedarf zu ignorieren und erneut zu patchen (z. B. bei geändertem Scale-Wert).
- Ausführliches Konsolen-Log inkl. Anzahl gepatchter und übersprungener (gesperrter) Materialien.
- Standardwert: 0.01.

### Shader Patcher (MMUA)

Rekursiver Shader-Patcher für MMUA-Materialien, der mehrere Teilbereiche gleichzeitig anpasst:

- **Bump/Bevel-Patch**: Skaliert Bump-Distance- und Bevel-Radius-Werte rekursiv durch alle verschachtelten Node-Gruppen, überspringt dabei bewusst Bevel-Nodes innerhalb der Gruppe `mb_config_normal`.
- **Microscratches-Patch**: Setzt einen festen Ziel-Multiplikationswert (0.2) für Microscratch-Multiply-Nodes innerhalb der Node-Gruppe `thorn_triplanar microscratches`.
- **SSS-Depth-Patch**: Skaliert den "Sss Depth"-Eingang in `mmua_base_solid`-Node-Gruppen rekursiv mit dem Scale-Faktor.
- **Triplanar-Normalize-Patch**: Fügt bei Bedarf eine fehlende Normalize-Node zwischen Cross-Product- und Scale-Node in `thorn_triplanar normal map`-Gruppen ein, um korrektes Normal-Mapping bei Skalierung sicherzustellen.
- Erkennt bereits vorhandene automatische Patch-Nodes (Label "Scale Multiply (auto)") und aktualisiert deren Wert statt sie erneut einzufügen.
- **Select MMUA Objects**: Wählt alle Mesh-Objekte in der Szene aus, deren Material die Node-Gruppe `mmua_base_solid` enthält – Button liegt direkt über dem "Shader patchen"-Button, um vor dem Patchen schnell alle relevanten Objekte zu markieren.
- Zeigt eine Liste der aktuell ausgewählten Mesh-Objekte (bis 10, mit Zähler für weitere) direkt im Panel an.
- Ausführliches Konsolen-Log für jeden Patch-Durchlauf mit Anzahl der bearbeiteten Einträge pro Objekt.
- Standardwert: 0.01.

## Floor Generator Import

Importiert mit einem Klick ein vorgefertigtes LEGO-Parkettboden-Objekt (Geometry-Nodes-Setup) aus einer im Addon gebündelten `.blend`-Datei, ohne dass die Quelldatei manuell geöffnet werden muss.

- Die Quelldatei liegt im Addon-Ordner unter `assets/LEGO Floor Generator_wood_01.blend`, das Zielobjekt heißt `LEGO Floor v01`.
- Beim Import wird das Objekt per Append (nicht Link) aus der gebündelten Datei geladen und am 3D-Cursor in der aktuellen Szene platziert.
- **Shader Scale**-Feld (Standardwert 0.01): Der eingegebene Wert wird direkt (ohne Berechnung) in die Scale-Value-Node auf der ersten Ebene jedes Materials des importierten Objekts eingetragen.
- Keine Prüf- oder Lock-Logik – das Objekt wird bei jedem Klick neu importiert.
- Rein als Import-Werkzeug gedacht; die Parameter des Floor-Generators selbst (Breite, Länge, Versatz) werden aktuell nicht über das Addon gesteuert.

---

## Installation

Da das Addon eine gebündelte `.blend`-Datei benötigt, wird es als **Ordner-Paket** installiert, nicht als einzelne `.py`-Datei:

```
lego_companion/
├── __init__.py
└── assets/
    └── LEGO Floor Generator_wood_01.blend
```

1. Ordner `lego_companion/` als ZIP packen (von innen, sodass `__init__.py` direkt im Archiv-Root des Ordners liegt).
2. In Blender: `Edit > Preferences > Add-ons > Install...` → ZIP-Datei auswählen.
3. Addon in der Liste aktivieren (Häkchen setzen).
4. Panel öffnen über `View3D > Sidebar (N) > LEGO Companion`.

## Kompatibilität

Getestet mit Blender 4.0+.
=======
# LEGO-Companion
A Blender add-on (for Blender 4.0 and above) for LEGO and stop-motion animation projects. It brings together several tools for organic motion refinement, stop-motion timing, transform cleanup, shader scaling, and importing a floor generator object, all within a sidebar panel under View3D > Sidebar > LEGO Companion.
>>>>>>> 4c818b671fef0d5621ebeae8ed52063bc5ceeb09
