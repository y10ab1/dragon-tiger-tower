extends Node3D
## Headless physics check: drop the player onto stair ramps and slabs,
## print the resting height. Run:
##   godot --headless res://scenes/debug_stairs.tscn --quit-after 400

const CHECKS := [
	# [name, drop_position, expected_min_y, expected_max_y]
	["tiger_ground", Vector3(8, 1.5, -3), 0.0, 0.4],
	["tiger_stair0_mid", Vector3(9.0, 3.4, -1.6), 2.2, 3.1],
	["tiger_slab_2f", Vector3(8, 4.4, -3), 3.3, 3.7],
	["tiger_stair1_mid", Vector3(6.6, 5.4, -3.0), 4.7, 5.6],
	["tiger_slab_7f", Vector3(8, 21.4, -3), 20.3, 20.8],
	["bridge_deck", Vector3(4, 1.0, 20), -0.05, 0.4],
	["plaza", Vector3(0, 1.0, 0), -0.05, 0.4],
	["pavilion", Vector3(0, 1.0, 48), -0.05, 0.4],
	["dragon_tunnel", Vector3(-8, 1.0, 3), -0.05, 0.4],
]

var _idx := 0
var _settle := 0.0
var fails := 0

@onready var player: CharacterBody3D = $Main/Player
@onready var ghost: CharacterBody3D = $Main/Ghost


func _physics_process(delta: float) -> void:
	ghost.global_position = Vector3(0, -60, -100)
	player.dead = false
	if _idx >= CHECKS.size():
		print("STAIRS_TEST_DONE fails=%d" % fails)
		get_tree().quit(1 if fails > 0 else 0)
		return
	_settle += delta
	if _settle < 0.05:
		return
	if _settle >= 1.2:
		var c: Array = CHECKS[_idx]
		var y := player.global_position.y
		var ok: bool = y >= c[2] and y <= c[3]
		var floor_name := "?"
		for ci in player.get_slide_collision_count():
			floor_name = str(player.get_slide_collision(ci).get_collider().name)
		print("%s: y=%.2f expect[%.1f..%.1f] %s on=%s"
				% [c[0], y, c[2], c[3], "OK" if ok else "FAIL", floor_name])
		if not ok:
			fails += 1
		_idx += 1
		_settle = 0.0
		if _idx < CHECKS.size():
			_drop(CHECKS[_idx][1])
	elif _settle - delta < 0.05:
		_drop(CHECKS[_idx][1])


func _drop(pos: Vector3) -> void:
	player.velocity = Vector3.ZERO
	player.global_position = pos
