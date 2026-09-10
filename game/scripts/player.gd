extends CharacterBody3D
## First-person player: movement, mouse look, flashlight, stamina, HUD.

signal died
signal escaped

const WALK_SPEED := 4.0
const SPRINT_SPEED := 6.4
const JUMP_VELOCITY := 4.2
const MOUSE_SENS := 0.0022
const STAMINA_MAX := 4.0

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var stamina: float = STAMINA_MAX
var dead := false
var won := false
var _bob_t := 0.0
var _step_accum := 0.0

@onready var head: Node3D = $Head
@onready var cam: Camera3D = $Head/Camera3D
@onready var flashlight: SpotLight3D = $Head/Camera3D/Flashlight
@onready var step_sfx: AudioStreamPlayer = $StepSfx


func _ready() -> void:
	# Browsers require a click/key event before granting pointer lock.
	if not OS.has_feature("web"):
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED


func _input(event: InputEvent) -> void:
	# Captured motion must run before GUI hit-testing (the reticle sits under
	# the captured pointer). Decorative HUD Controls also ignore mouse input.
	if dead or won:
		return
	if event is InputEventMouseMotion and Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
		rotate_y(-event.screen_relative.x * MOUSE_SENS)
		head.rotation.x = clampf(head.rotation.x - event.screen_relative.y * MOUSE_SENS,
				-1.45, 1.45)
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("flashlight") and not event.is_echo():
		flashlight.visible = not flashlight.visible
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_cancel") and not event.is_echo():
		if Input.mouse_mode == Input.MOUSE_MODE_CAPTURED:
			Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		else:
			Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		get_viewport().set_input_as_handled()
	elif event is InputEventMouseButton and event.pressed \
			and event.button_index == MOUSE_BUTTON_LEFT \
			and Input.mouse_mode != Input.MOUSE_MODE_CAPTURED:
		Input.mouse_mode = Input.MOUSE_MODE_CAPTURED
		get_viewport().set_input_as_handled()


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_FOCUS_OUT:
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE


func _physics_process(delta: float) -> void:
	if dead or won:
		return
	if not is_on_floor():
		velocity.y -= gravity * delta
	elif Input.is_action_just_pressed("jump"):
		velocity.y = JUMP_VELOCITY

	var input_dir := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var direction := (transform.basis * Vector3(input_dir.x, 0, input_dir.y)).normalized()

	var sprinting := Input.is_action_pressed("sprint") and stamina > 0.0 \
			and input_dir.length() > 0.1
	var speed := SPRINT_SPEED if sprinting else WALK_SPEED
	if sprinting:
		stamina = maxf(0.0, stamina - delta)
	else:
		stamina = minf(STAMINA_MAX, stamina + delta * 0.7)

	if direction:
		velocity.x = direction.x * speed
		velocity.z = direction.z * speed
	else:
		velocity.x = move_toward(velocity.x, 0, speed * 0.2)
		velocity.z = move_toward(velocity.z, 0, speed * 0.2)

	move_and_slide()

	# head bob + footsteps
	var planar := Vector2(velocity.x, velocity.z).length()
	if is_on_floor() and planar > 0.5:
		_bob_t += delta * planar * 1.6
		cam.position.y = 0.06 * sin(_bob_t)
		_step_accum += planar * delta
		if _step_accum > 2.2:
			_step_accum = 0.0
			step_sfx.pitch_scale = randf_range(0.85, 1.15)
			step_sfx.play()
	else:
		cam.position.y = lerpf(cam.position.y, 0.0, delta * 6.0)

	# fell into the lake
	if global_position.y < -1.2:
		kill()


func flashlight_hits(target: Node3D) -> bool:
	## Whether the flashlight beam is currently shining on `target`.
	if dead or won or not flashlight.is_visible_in_tree():
		return false
	var to_target: Vector3 = target.global_position + Vector3.UP * 1.5 \
			- flashlight.global_position
	var dist := to_target.length()
	if dist > flashlight.spot_range:
		return false
	var fwd := -flashlight.global_transform.basis.z
	if fwd.dot(to_target.normalized()) < cos(deg_to_rad(flashlight.spot_angle)):
		return false
	var space := get_world_3d().direct_space_state
	var ray := PhysicsRayQueryParameters3D.create(
			flashlight.global_position, target.global_position + Vector3.UP * 1.5)
	ray.exclude = [get_rid()]
	var hit := space.intersect_ray(ray)
	if hit.is_empty():
		return true
	return hit.collider == target


func kill() -> void:
	if dead or won:
		return
	dead = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	died.emit()


func win() -> void:
	if dead or won:
		return
	won = true
	Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
	escaped.emit()
