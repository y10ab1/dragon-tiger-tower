extends SceneTree
## Probe the actual capsule at window recesses and under the solid-looking steps.

var fails := 0


func _initialize() -> void:
	call_deferred("_run")


func check(ok: bool, label: String) -> void:
	print("TOWER_EDGES %s %s" % [label, "OK" if ok else "FAIL"])
	if not ok:
		fails += 1


func _run() -> void:
	var main: Node3D = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	main.get_node("Ghost").set_physics_process(false)
	main.get_node("Ghost").position = Vector3(0, -60, -100)
	var player: CharacterBody3D = main.get_node("Player")
	player.set_physics_process(false)
	# Isolate the wall envelope for capsule probes. Some window positions lie
	# behind the solid high end of a stair, not at a valid standing location.
	# The real-input tower-walk test covers the combined collision geometry.
	for body in main.find_children("*TowerShell", "StaticBody3D", true, false):
		body.collision_layer = 4
	await physics_frame
	await physics_frame
	for cx in [-8.0, 8.0]:
		player.collision_mask = 4
		for floor_index in range(7):
			var r := 4.3 - 0.1 * floor_index
			var wall := r * cos(PI / 8) - 0.15
			var y := floor_index * 3.4
			# Airborne at sill height: windows must not swallow the capsule.
			for side in range(8):
				if floor_index == 0 and side == 6:
					continue
				var angle := side * PI / 4
				var out := Vector3(cos(angle), 0, -sin(angle))
				var origin := Vector3(cx, y + 0.45, -3) + out * (wall - 0.5)
				var pose := Transform3D(Basis.IDENTITY, origin)
				var hit := KinematicCollision3D.new()
				var blocked := player.test_move(pose, out * 0.75, hit)
				check(blocked and hit.get_travel().length() < 0.3,
						"x=%s floor=%s window=%s blocks recess" % [cx, floor_index + 1, side])
				if blocked:
					pose.origin += hit.get_travel()
					check(not player.test_move(pose, -out * 0.3), "can back away from window")
		# The high end visually reaches the ground, so it must block entry below.
		player.collision_mask = 1
		var under_stairs := Transform3D(Basis.IDENTITY, Vector3(cx + 1.9, 0.01, -3))
		check(player.test_move(under_stairs, Vector3(0, 0, 1.5)),
				"x=%s cannot enter solid stair dead-end" % cx)
		# Perimeter floors meet the walls instead of leaving a fall-through crack.
		for floor_index in range(1, 7):
			var wall := (4.3 - floor_index * 0.1) * cos(PI / 8) - 0.15
			for side in range(8):
				var angle := side * PI / 4
				var point := Vector3(cx, floor_index * 3.4 + 0.2, -3)
				point += Vector3(cos(angle), 0, -sin(angle)) * (wall - 0.08)
				var ray := PhysicsRayQueryParameters3D.create(point, point + Vector3.DOWN * 0.4)
				ray.collision_mask = 1
				var hit := root.world_3d.direct_space_state.intersect_ray(ray)
				check(not hit.is_empty(), "x=%s floor=%s edge=%s has floor" % [cx, floor_index + 1, side])
	print("TOWER_EDGES_DONE fails=%d" % fails)
	main.queue_free()
	await process_frame
	quit(1 if fails else 0)
