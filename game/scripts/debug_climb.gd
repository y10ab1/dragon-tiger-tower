extends Node3D
## Headless walking bot: presses real input actions to walk the player up
## all six flights of the tiger tower. Validates ramps, headroom and holes.
## Run: godot --headless res://scenes/debug_climb.tscn

var waypoints: Array[Vector3] = []
var _idx := 0
var _stuck := 0.0

@onready var player: CharacterBody3D = $Main/Player
@onready var ghost: CharacterBody3D = $Main/Ghost


func _ready() -> void:
	var cx := 8.0
	var cz := -3.0
	waypoints.append(Vector3(cx, 0, cz))
	for i in range(6):
		var ang := -i * PI / 2
		var s := Vector2(-2.2, -1.4).rotated(ang)   # flight start (local)
		var e := Vector2(2.2, -1.4).rotated(ang)    # flight end (local)
		var o := Vector2(3.0, -1.4).rotated(ang)    # step off, past the hole
		var o2 := Vector2(3.0, 1.2).rotated(ang)    # around the hole corner
		waypoints.append(Vector3(cx + s.x, 0, cz - s.y))
		waypoints.append(Vector3(cx + e.x, 0, cz - e.y))
		waypoints.append(Vector3(cx + o.x, 0, cz - o.y))
		waypoints.append(Vector3(cx + o2.x, 0, cz - o2.y))
		waypoints.append(Vector3(cx, 0, cz))        # floor centre above
	player.global_position = Vector3(cx, 0.2, cz)


func _physics_process(delta: float) -> void:
	ghost.global_position = Vector3(0, -60, -100)
	player.dead = false
	if _idx >= waypoints.size():
		var final_y := player.global_position.y
		print("CLIMB_DONE y=%.2f %s" % [final_y,
				"OK" if final_y > 20.0 else "FAIL"])
		get_tree().quit(0 if final_y > 20.0 else 1)
		return
	var target := waypoints[_idx]
	var d := target - player.global_position
	d.y = 0
	if d.length() < 0.3:
		print("wp %d reached  y=%.2f" % [_idx, player.global_position.y])
		_idx += 1
		_stuck = 0.0
		return
	_stuck += delta
	if _stuck > 8.0:
		print("CLIMB_STUCK at wp %d pos=%s" % [_idx,
				str(player.global_position)])
		get_tree().quit(1)
		return
	player.rotation.y = atan2(-d.x, -d.z)
	Input.action_press("move_forward")
