extends CanvasLayer
## All HUD elements are decorative: none can intercept captured mouse motion.

const INK_THEME := preload("res://assets/fonts/horror_theme.tres")


func _ready() -> void:
	_ignore_pointer(self)


func _ignore_pointer(node: Node) -> void:
	if node is Control:
		node.theme = INK_THEME
		node.mouse_filter = Control.MOUSE_FILTER_IGNORE
		node.focus_mode = Control.FOCUS_NONE
	for child in node.get_children():
		_ignore_pointer(child)


func update_state(player: Node3D, ghost: Node3D) -> void:
	var playing: bool = not player.dead and not player.won
	var captured := Input.mouse_mode == Input.MOUSE_MODE_CAPTURED
	$Crosshair.visible = playing and captured
	$AimHint.visible = playing and captured
	$CaptureHint.visible = playing and not captured
	$LightStatus.text = "燈火　明  /  F" if player.flashlight.visible else "燈火　滅  /  F"
	$Crosshair.update_aim(ghost.illuminated, ghost.repel_progress(), ghost.state == 2,
			player.flashlight.visible)
	if ghost.illuminated:
		$AimHint.text = "煞退" if ghost.state == 2 else "照住祂，別移開"
	elif not player.flashlight.visible:
		$AimHint.text = "按 F 點亮手電筒"
	else:
		$AimHint.text = ""


func show_ending(escaped: bool) -> void:
	$EndTitle.text = "厄運盡除" if escaped else "魂留蓮潭"
	$EndTitle.add_theme_color_override("font_color",
			Color(0.96, 0.85, 0.56) if escaped else Color(0.82, 0.22, 0.16))
	$EndTitle.show()
	$Message.set_anchors_and_offsets_preset(Control.PRESET_CENTER)
	$Message.offset_left = -360
	$Message.offset_right = 360
	$Message.offset_top = 28
	$Message.offset_bottom = 164
