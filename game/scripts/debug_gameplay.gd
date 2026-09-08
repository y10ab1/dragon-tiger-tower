extends Node3D
## Headless gameplay test: chase kill, flashlight repel, win condition.
## Run: godot --headless res://scenes/debug_gameplay.tscn

var phase := 0
var timer := 0.0
var results: Array[String] = []

@onready var main: Node3D = $Main
@onready var player: CharacterBody3D = $Main/Player
@onready var ghost: CharacterBody3D = $Main/Ghost


func _physics_process(delta: float) -> void:
	timer += delta
	match phase:
		0:  # ghost should chase and catch a nearby player
			if timer < 0.1:
				player.global_position = Vector3(0, 0.3, 2)
				player.rotation.y = deg_to_rad(180)  # face away
				player.flashlight.visible = false
				ghost.global_position = Vector3(0, 0.05, -4)
			if player.dead:
				results.append("chase_kill OK (%.1fs)" % timer)
				_next()
			elif timer > 12.0:
				results.append("chase_kill FAIL (not caught, ghost=%s state=%d)"
						% [str(ghost.global_position), ghost.state])
				_next()
		1:  # flashlight should repel a chasing ghost
			if timer < 0.1:
				player.dead = false
				player.global_position = Vector3(0, 0.3, 5)
				ghost.global_position = Vector3(0, 0.05, -3)
				ghost.state = 1  # CHASE
				player.flashlight.visible = true
			# keep facing the ghost
			var d := ghost.global_position - player.global_position
			player.rotation.y = atan2(-d.x, -d.z)
			player.get_node("Head").rotation.x = 0.1
			if ghost.state == 2:
				results.append("flashlight_repel OK (%.1fs)" % timer)
				_next()
			elif player.dead:
				results.append("flashlight_repel FAIL (killed)")
				_next()
			elif timer > 10.0:
				results.append("flashlight_repel FAIL (state=%d dist=%.1f)"
						% [ghost.state, d.length()])
				_next()
		2:  # entering the dragon mouth with 7 talismans should win
			if timer < 0.1:
				player.dead = false
				ghost.global_position = Vector3(0, -60, -100)
				main.collected = 7
				player.global_position = Vector3(-8, 0.3, 7.2)
			if player.won:
				results.append("win_condition OK (%.1fs)" % timer)
				_next()
			elif timer > 6.0:
				results.append("win_condition FAIL")
				_next()
		3:
			var fails := 0
			for r in results:
				print("TEST ", r)
				if "FAIL" in r:
					fails += 1
			print("GAMEPLAY_TEST_DONE fails=%d" % fails)
			get_tree().quit(1 if fails > 0 else 0)


func _next() -> void:
	phase += 1
	timer = 0.0
