extends Control
## Camera-aligned aiming mark; the arc uses the ghost's actual repel progress.

var illuminated := false
var progress := 0.0
var repelled := false
var light_on := true


func update_aim(lit: bool, amount: float, retreating: bool, enabled: bool) -> void:
	illuminated = lit
	progress = amount
	repelled = retreating
	light_on = enabled
	queue_redraw()


func _draw() -> void:
	var center := size / 2
	var ink := Color(0.85, 0.81, 0.69, 0.75) if light_on else Color(0.5, 0.48, 0.43, 0.5)
	if illuminated:
		ink = Color(1.0, 0.72, 0.32)
	draw_circle(center, 2.0, ink)
	for direction in [Vector2.LEFT, Vector2.RIGHT, Vector2.UP, Vector2.DOWN]:
		draw_line(center + direction * 8, center + direction * 12, ink, 1.0, true)
	if progress > 0.0 or (repelled and illuminated):
		var amount := 1.0 if repelled else progress
		draw_arc(center, 19, -PI / 2, -PI / 2 + TAU * amount, 48, ink, 2.0, true)
