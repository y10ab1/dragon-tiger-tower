extends SceneTree
## Input travels through the viewport, including HUD hit-testing.
## godot --path game --script res://scripts/debug_controls.gd
## Requires a display: Godot's headless driver cannot capture a mouse.
## Add -- --screenshots with a display to save HUD previews to /tmp/opencode.

var fails := 0
var main: Node3D
var player: CharacterBody3D
var ghost: CharacterBody3D


func _initialize() -> void:
	call_deferred("_run")


func check(ok: bool, description: String) -> void:
	print("CONTROLS %s %s" % [description, "OK" if ok else "FAIL"])
	if not ok:
		fails += 1


func motion(delta: Vector2) -> void:
	var event := InputEventMouseMotion.new()
	event.position = root.get_visible_rect().size / 2
	event.global_position = event.position
	# Deliberately different: look sensitivity must use unscaled screen pixels.
	event.relative = delta * 0.5
	event.screen_relative = delta
	root.push_input(event)


func action(name: String) -> void:
	var event := InputEventAction.new()
	event.action = name
	event.pressed = true
	root.push_input(event)
	event = InputEventAction.new()
	event.action = name
	event.pressed = false
	root.push_input(event)


func _run() -> void:
	if DisplayServer.get_name() == "headless":
		push_error("Mouse capture test requires a display; run without --headless.")
		quit(1)
		return
	main = load("res://scenes/main.tscn").instantiate()
	root.add_child(main)
	player = main.get_node("Player")
	ghost = main.get_node("Ghost")
	player.set_physics_process(false)
	ghost.set_physics_process(false)
	player.position = Vector3(0, 0.1, 5)
	await process_frame
	await process_frame
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	var yaw := player.rotation.y
	var pitch: float = player.head.rotation.x
	motion(Vector2(120, -55))
	check(is_equal_approx(player.rotation.y, yaw - 120 * player.MOUSE_SENS), "horizontal mouse look through HUD")
	check(is_equal_approx(player.head.rotation.x, pitch + 55 * player.MOUSE_SENS), "vertical mouse look / screen pixels")
	check(player.flashlight.global_basis.is_equal_approx(player.cam.global_basis), "beam follows camera")
	ghost.position = player.flashlight.global_position - player.flashlight.global_basis.z * 6 - Vector3.UP * 1.5
	await physics_frame
	await physics_frame
	check(player.flashlight_hits(ghost), "mouse-aimed beam hits ghost")
	motion(Vector2(350, 0))
	check(not player.flashlight_hits(ghost), "turning away misses ghost")
	motion(Vector2(-350, 0))
	action("flashlight")
	check(not player.flashlight_hits(ghost), "F disables beam")
	action("flashlight")
	check(player.flashlight_hits(ghost), "F restores beam")
	var near_position := ghost.position
	ghost.position = player.flashlight.global_position - player.flashlight.global_basis.z * 15 - Vector3.UP * 1.5
	check(not player.flashlight_hits(ghost), "visible beam range matches hit range")
	ghost.position = near_position
	var blocker := StaticBody3D.new()
	var shape := CollisionShape3D.new()
	var box := BoxShape3D.new()
	box.size = Vector3(2, 3, 0.5)
	shape.shape = box
	blocker.add_child(shape)
	main.add_child(blocker)
	blocker.position = player.flashlight.global_position - player.flashlight.global_basis.z * 3
	await physics_frame
	await physics_frame
	check(not player.flashlight_hits(ghost), "wall blocks flashlight")
	blocker.queue_free()
	await physics_frame
	motion(Vector2(0, -10000))
	check(is_equal_approx(player.head.rotation.x, 1.45), "pitch clamped upward")
	motion(Vector2(0, 20000))
	check(is_equal_approx(player.head.rotation.x, -1.45), "pitch clamped downward")
	action("ui_cancel")
	yaw = player.rotation.y
	motion(Vector2(100, 100))
	check(Input.mouse_mode == Input.MOUSE_MODE_VISIBLE and is_equal_approx(yaw, player.rotation.y), "Esc releases mouse without moving view")
	await process_frame
	await process_frame
	check(main.get_node("UI/CaptureHint").visible, "recapture instruction visible")
	var click := InputEventMouseButton.new()
	click.button_index = MOUSE_BUTTON_LEFT
	click.pressed = true
	click.position = root.get_visible_rect().size / 2
	root.push_input(click)
	check(Input.mouse_mode == Input.MOUSE_MODE_CAPTURED, "left click recaptures mouse over HUD")
	player.notification(Node.NOTIFICATION_APPLICATION_FOCUS_OUT)
	check(Input.mouse_mode == Input.MOUSE_MODE_VISIBLE, "focus loss releases mouse")
	action("ui_cancel")
	check(Input.mouse_mode == Input.MOUSE_MODE_CAPTURED, "Esc resumes look")
	for control in main.get_node("UI").find_children("*", "Control"):
		check(control.mouse_filter == Control.MOUSE_FILTER_IGNORE, "HUD ignores mouse: " + control.name)
	var font: Font = main.get_node("UI/Title").get_theme_font("font")
	var glyphs_present := true
	for character in "龍虎塔蓮池潭子時禁入鎮煞符氣息燈火厄運盡除魂留蓮潭祂":
		glyphs_present = glyphs_present and font.has_char(character.unicode_at(0))
	check(glyphs_present and "WenKai" in font.get_font_name(), "bundled Traditional Chinese ink font")
	main._show_message("舊提示", 0.01)
	main._show_message("新提示", 5.0)
	await create_timer(0.05).timeout
	check(main.message_label.visible and main.message_label.text == "新提示", "new message outlives old expiry")
	if "--screenshots" in OS.get_cmdline_user_args():
		await _screenshots()
	player.kill()
	yaw = player.rotation.y
	motion(Vector2(100, 0))
	check(Input.mouse_mode == Input.MOUSE_MODE_VISIBLE and is_equal_approx(yaw, player.rotation.y), "death releases pointer and stops aiming")
	check(main.get_node("UI/EndTitle").visible, "death typography visible")
	print("CONTROLS_TEST_DONE fails=%d" % fails)
	main.queue_free()
	await process_frame
	quit(1 if fails else 0)


func _screenshots() -> void:
	player.rotation = Vector3.ZERO
	player.head.rotation.x = 0
	player.position = Vector3(0, 0.1, 8.5)
	ghost.position = Vector3(0, 0.1, 1.5)
	ghost.illuminated = true
	ghost.state = 1
	ghost._repel_time = 0.7
	main._show_message("龍口進，虎口出。你卻逆了規矩……\n尋齊七道鎮煞符；遇見祂，持燈直照，別回頭。", 20)
	Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/opencode/hud_aim.png")
	root.size = Vector2i(960, 540)
	await process_frame
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/opencode/hud_aim_small.png")
	for name in ["Title", "Counter", "Controls", "LightStatus", "Message"]:
		var label: Label = main.get_node("UI/" + name)
		check(root.get_visible_rect().encloses(label.get_global_rect()), "small window bounds: " + name)
	root.size = Vector2i(1280, 720)
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	await process_frame
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/opencode/hud_released.png")
	player.kill()
	await create_timer(1.3).timeout
	await RenderingServer.frame_post_draw
	root.get_texture().get_image().save_png("/tmp/opencode/hud_death.png")
