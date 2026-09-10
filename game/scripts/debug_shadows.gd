extends SceneTree
## Render the same grazing-angle flashlight view with/without shadow casting.
## Run with --rendering-method gl_compatibility (requires a display).


func _initialize() -> void:
	call_deferred("_run")


func _run() -> void:
	var main: Node3D = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	main.get_node("Ghost").set_physics_process(false)
	main.get_node("Ghost").position = Vector3(0, -60, -100)
	var player = main.get_node("Player")
	player.set_physics_process(false)
	player.position = Vector3(0, 0.05, 39)
	player.rotation.y = -0.18
	player.head.rotation.x = -0.22
	main.get_node("UI").hide()
	print("SHADOW SETTINGS bias=%s normal=%s atlas=%s 16bits=%s" % [
		player.flashlight.shadow_bias, player.flashlight.shadow_normal_bias,
		ProjectSettings.get_setting("rendering/lights_and_shadows/positional_shadow/atlas_size"),
		ProjectSettings.get_setting("rendering/lights_and_shadows/positional_shadow/atlas_16_bits")])
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/opencode/shadow_current.png")
	player.flashlight.shadow_enabled = false
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/opencode/shadow_disabled.png")
	main.queue_free()
	await process_frame
	quit()
