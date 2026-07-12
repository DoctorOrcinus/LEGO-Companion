# Doctor Orcinus LEGO Tweaks

Ein Blender-Addon (ab Blender 4.0) für LEGO- und Stop-Motion-Animationsprojekte. Es sammelt mehrere Werkzeuge rund um organische Bewegungsverfeinerung, Stop-Motion-Timing, Transform-Bereinigung und Shader-Skalierung in einem Sidebar-Panel unter **View3D > Sidebar > Doctor Orcinus**.

## Inhalt

- [Organic Motion](#organic-motion)
- [Animation on 2s](#animation-on-2s)
- [Reset LEGO Delta Offset](#reset-lego-delta-offset)
- [Shader & Scale](#shader--scale)
  - [Node Scale Setter](#node-scale-setter)
  - [MecaFace Scale Patcher](#mecaface-scale-patcher)
  - [Shader Patcher (MMUA)](#shader-patcher-mmua)

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

### MecaFace Scale Patcher

Patcht gezielt Node-Gruppen mit dem Basisnamen **MecaFace.Material** in allen Materialien der Szene – global und pro Node-Tree nur einmal.

- Sucht in der Node-Gruppe nach einer Noise-Texture mit Scale-Wert 3.75 (Noise-Texturen mit Scale 50 werden bewusst ignoriert) und setzt deren Scale auf `3.75 × Patcher-Scale-Wert`.
- Sucht eine Bevel-Node, deren Radius-Eingang bereits über eine Multiply-Node gespeist wird, und fügt davor eine zusätzliche Multiply-Node ein, die den Wert mit dem Patcher-Scale-Wert multipliziert (Bevel-Nodes ohne verkabelten Radius werden ignoriert).
- **Lock-Mechanismus**: Jeder gepatchte Node-Tree wird über eine Custom Property markiert, damit er nicht versehentlich mehrfach gepatcht wird.
- **Force Repatch**-Option, um die Sperre bei Bedarf zu ignorieren und erneut zu patchen (z. B. bei geändertem Scale-Wert).
- Ausführliches Konsolen-Log inkl. Anzahl gepatchter und übersprungener (gesperrter) Materialien.

### Shader Patcher (MMUA)

Rekursiver Shader-Patcher für MMUA-Materialien, der mehrere Teilbereiche gleichzeitig anpasst:

- **Bump/Bevel-Patch**: Skaliert Bump-Distance- und Bevel-Radius-Werte rekursiv durch alle verschachtelten Node-Gruppen, überspringt dabei bewusst Bevel-Nodes innerhalb der Gruppe `mb_config_normal`.
- **Microscratches-Patch**: Setzt einen festen Ziel-Multiplikationswert (0.2) für Microscratch-Multiply-Nodes innerhalb der Node-Gruppe `thorn_triplanar microscratches`.
- **SSS-Depth-Patch**: Skaliert den "Sss Depth"-Eingang in `mmua_base_solid`-Node-Gruppen rekursiv mit dem Scale-Faktor.
- **Triplanar-Normalize-Patch**: Fügt bei Bedarf eine fehlende Normalize-Node zwischen Cross-Product- und Scale-Node in `thorn_triplanar normal map`-Gruppen ein, um korrektes Normal-Mapping bei Skalierung sicherzustellen.
- Erkennt bereits vorhandene automatische Patch-Nodes (Label "Scale Multiply (auto)") und aktualisiert deren Wert statt sie erneut einzufügen.
- **MMUA Object Select**: Wählt alle Mesh-Objekte in der Szene aus, deren Material die Node-Gruppe `mmua_base_solid` enthält – praktisch, um vor dem Patchen schnell alle relevanten Objekte zu markieren.
- Zeigt eine Liste der aktuell ausgewählten Mesh-Objekte (bis 10, mit Zähler für weitere) direkt im Panel an.
- Ausführliches Konsolen-Log für jeden Patch-Durchlauf mit Anzahl der bearbeiteten Einträge pro Objekt.

---

## Installation

1. Datei über `Edit > Preferences > Add-ons > Install...` in Blender laden.
2. Addon aktivieren.
3. Panel öffnen über `View3D > Sidebar (N) > Doctor Orcinus`.

## Kompatibilität

Getestet mit Blender 4.0+.
