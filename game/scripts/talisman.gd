extends Area3D
## Floating, spinning talisman pickup.

signal collected

var _t := 0.0
@onready var mesh_root: Node3D = $TalismanMesh


func _ready() -> void:
	body_entered.connect(_on_body)


func _process(delta: float) -> void:
	_t += delta
	rotate_y(delta * 1.5)
	mesh_root.position.y = 0.15 * sin(_t * 2.0)


func _on_body(body: Node3D) -> void:
	if body.is_in_group("player"):
		collected.emit()
		queue_free()
