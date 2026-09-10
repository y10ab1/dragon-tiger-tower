extends SceneTree
## Real input, both towers, both directions, and three lanes across every flight.
## godot --headless --path game --fixed-fps 60 --script res://scripts/debug_tower_walk.gd

var player: CharacterBody3D
var main: Node3D


func _initialize() -> void:
	call_deferred("_run")


func _point(cx: float, floor_index: int, x: float, y: float, height: float) -> Vector3:
	var p := Vector2(x, y).rotated(-floor_index * PI / 2)
	return Vector3(cx + p.x, height, -3 - p.y)


func _walk(target: Vector3) -> bool:
	var time := 0.0
	while time < 5.0:
		await physics_frame
		var d := target - player.global_position
		var vertical := d.y
		d.y = 0
		if d.length() < 0.13 and absf(vertical) < 0.35:
			Input.action_release("move_forward")
			return true
		if player.dead:
			break
		player.rotation.y = atan2(-d.x, -d.z)
		Input.action_press("move_forward")
		time += 1.0 / Engine.physics_ticks_per_second
	Input.action_release("move_forward")
	print("TOWER_WALK_STUCK target=%s actual=%s" % [target, player.global_position])
	for i in player.get_slide_collision_count():
		var hit := player.get_slide_collision(i)
		print("  collider=%s normal=%s" % [hit.get_collider().name, hit.get_normal()])
	return false


func _run() -> void:
	main = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	player = main.get_node("Player")
	main.get_node("Ghost").set_physics_process(false)
	main.get_node("Ghost").position = Vector3(0, -60, -100)
	main.get_node("ExitZone").monitoring = false
	var fails := 0
	for cx in [-8.0, 8.0]:
		for lane in [-0.22, 0.0, 0.22]:
			player.dead = false
			player.won = false
			player.velocity = Vector3.ZERO
			player.position = Vector3(cx, 0.1, -3)
			var route: Array[Vector3] = [Vector3(cx, 0, -3)]
			for i in range(6):
				var y := i * 3.4
				route.append(_point(cx, i, -2.65, 0, y))
				route.append(_point(cx, i, -2.65, -1.4 + lane, y))
				route.append(_point(cx, i, 2.2, -1.4 + lane, y + 3.4))
				# Turn on the widened landing, inside the narrowing octagon.
				route.append(_point(cx, i, 2.48, -1.4 + lane, y + 3.4))
				route.append(_point(cx, i, 2.48, 0.1, y + 3.4))
				route.append(Vector3(cx, y + 3.4, -3))
			var ok := true
			for index in range(route.size()):
				var target := route[index]
				if not await _walk(target):
					ok = false
					break
				if index % 6 == 4:
					# Deliberately push into each outer landing corner, then back
					# away using input. This catches wedges that a centerline bot misses.
					var angle := -((index - 1) / 6) * PI / 2
					var out := Vector2.RIGHT.rotated(angle)
					player.rotation.y = atan2(-out.x, out.y)
					Input.action_press("move_forward")
					for tick in range(15):
						await physics_frame
					Input.action_release("move_forward")
					if not await _walk(target):
						ok = false
						break
			if ok:
				print("TOWER_WALK x=%s lane=%s ascended to %.2f" % [cx, lane, player.position.y])
				route.reverse()
				for target in route:
					if not await _walk(target):
						ok = false
						break
			if not ok:
				fails += 1
			print("TOWER_WALK x=%s lane=%s round trip %s" % [cx, lane, "OK" if ok else "FAIL"])
	print("TOWER_WALK_DONE fails=%d" % fails)
	main.queue_free()
	await process_frame
	quit(1 if fails else 0)
