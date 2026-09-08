extends Node3D
## Debug fly-through: teleports the player through checkpoints while
## recording with --write-movie, to validate collisions & visuals.

const SPOTS := [
	# [position, yaw_degrees, pitch_degrees]
	[Vector3(0, 0.4, 46), 0.0, -5.0],        # pavilion spawn, view bridge
	[Vector3(0, 0.5, 30), 0.0, -5.0],        # mid bridge
	[Vector3(8, 0.5, 9.5), 0.0, -5.0],       # facing tiger statue mouth
	[Vector3(8, 0.5, 5), 0.0, 0.0],          # inside tiger mouth tunnel
	[Vector3(8, 0.5, -3), 45.0, 10.0],       # tiger tower ground floor
	[Vector3(8, 4.0, -3), 135.0, -10.0],     # tiger tower 2F (falls to slab)
	[Vector3(8, 21.0, -3), 225.0, -10.0],    # tiger tower 7F
	[Vector3(-8, 0.5, 9.5), 0.0, -5.0],      # facing dragon statue
	[Vector3(-8, 0.5, -3), 0.0, 10.0],       # dragon tower ground
	[Vector3(0, 0.5, -5), 180.0, 0.0],       # plaza north, look at ghost area
	[Vector3(-13, 0.5, 0), 90.0, -5.0],      # west plaza edge
	[Vector3(0, 0.5, 44), 0.0, 0.0],         # look at the pinned ghost
]
const SECONDS_PER_SPOT := 2.0

var _idx := -1
var _t := 999.0

@onready var main: Node3D = $Main
@onready var player: CharacterBody3D = $Main/Player
@onready var ghost: CharacterBody3D = $Main/Ghost


func _physics_process(delta: float) -> void:
	# park the ghost; show it up close only for the final camera spot
	if _idx >= SPOTS.size() - 1:
		ghost.global_position = Vector3(0.8, 0.05, 40.5)
	else:
		ghost.global_position = Vector3(0, -60, -100)
	# keep the player alive no matter what
	player.dead = false
	main.get_node("UI/Fade").color = Color(0, 0, 0, 0)
	_t += delta
	if _t >= SECONDS_PER_SPOT:
		_t = 0.0
		_idx += 1
		if _idx >= SPOTS.size():
			get_tree().quit()
			return
		var s: Array = SPOTS[_idx]
		player.velocity = Vector3.ZERO
		player.global_position = s[0]
		player.rotation = Vector3(0, deg_to_rad(s[1]), 0)
		player.get_node("Head").rotation.x = deg_to_rad(s[2])
		print("TOUR spot %d: %s" % [_idx, str(s[0])])
