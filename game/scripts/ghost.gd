extends CharacterBody3D
## Tiger-spirit wraith: wanders the bridge & plaza, chases the player on
## sight, is repelled by the flashlight beam.

enum State { WANDER, CHASE, REPELLED }

const WANDER_SPEED := 1.7
const CHASE_SPEED := 5.1
const REPEL_SPEED := 2.2
const SIGHT_RANGE := 16.0
const CATCH_DIST := 1.3
const LOSE_SIGHT_TIME := 4.0
const REPEL_DURATION := 1.4

var state: int = State.WANDER
var waypoints: Array[Vector3] = []
var _wp_index := 0
var _lose_sight := 0.0
var _repel_time := 0.0
var _bob := 0.0
var player: Node3D = null
var illuminated := false

@onready var mesh_root: Node3D = $GhostMesh
@onready var moan: AudioStreamPlayer3D = $Moan
@onready var glow: OmniLight3D = $Glow


func _ready() -> void:
	if moan.stream is AudioStreamWAV:
		moan.stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		moan.stream.loop_begin = 0
		moan.stream.loop_end = moan.stream.data.size() / 2
	moan.play()


func setup(p_player: Node3D, p_waypoints: Array[Vector3]) -> void:
	player = p_player
	waypoints = p_waypoints
	_wp_index = randi() % waypoints.size()


func _physics_process(delta: float) -> void:
	if player == null or waypoints.is_empty():
		return
	if player.get("dead") or player.get("won"):
		illuminated = false
		velocity = Vector3.ZERO
		return

	_bob += delta * 2.0
	mesh_root.position.y = 0.15 + 0.1 * sin(_bob)

	var to_player := player.global_position - global_position
	var dist := to_player.length()
	var lit: bool = player.call("flashlight_hits", self)
	illuminated = lit
	var sees := _can_see_player(dist)

	match state:
		State.WANDER:
			if sees and dist < SIGHT_RANGE:
				_enter_chase()
			_move_towards(waypoints[_wp_index], WANDER_SPEED, delta)
			if _flat_dist(waypoints[_wp_index]) < 1.5:
				_wp_index = randi() % waypoints.size()
		State.CHASE:
			if lit:
				_repel_time += delta
				if _repel_time > REPEL_DURATION:
					state = State.REPELLED
					_repel_time = 0.0
			else:
				_repel_time = maxf(0.0, _repel_time - delta)
			if sees:
				_lose_sight = 0.0
			else:
				_lose_sight += delta
				if _lose_sight > LOSE_SIGHT_TIME:
					state = State.WANDER
					glow.light_energy = 0.6
			if not lit:
				_move_towards(player.global_position, CHASE_SPEED, delta)
			else:
				velocity.x = move_toward(velocity.x, 0, delta * 8)
				velocity.z = move_toward(velocity.z, 0, delta * 8)
				move_and_slide()
			if dist < CATCH_DIST:
				player.call("kill")
				state = State.WANDER
		State.REPELLED:
			var away := global_position - player.global_position
			away.y = 0
			_move_dir(away.normalized(), REPEL_SPEED, delta)
			_repel_time += delta
			if _repel_time > 3.0 or not lit:
				_repel_time = 0.0
				state = State.CHASE if dist < SIGHT_RANGE else State.WANDER

	# face movement direction / player
	var look_target := player.global_position if state == State.CHASE \
			else global_position + velocity
	look_target.y = global_position.y
	if (look_target - global_position).length() > 0.3:
		var t := global_transform.looking_at(look_target, Vector3.UP)
		global_transform.basis = global_transform.basis.slerp(
				t.basis, minf(1.0, delta * 5.0))


func _enter_chase() -> void:
	state = State.CHASE
	_lose_sight = 0.0
	glow.light_energy = 2.0


func repel_progress() -> float:
	return clampf(_repel_time / REPEL_DURATION, 0.0, 1.0) if state == State.CHASE else 0.0


func _can_see_player(dist: float) -> bool:
	if dist > SIGHT_RANGE and state != State.CHASE:
		return false
	if dist > SIGHT_RANGE * 1.6:
		return false
	var space := get_world_3d().direct_space_state
	var ray := PhysicsRayQueryParameters3D.create(
			global_position + Vector3.UP * 1.6,
			player.global_position + Vector3.UP * 0.5)
	ray.exclude = [get_rid(), player.get_rid()]
	var hit := space.intersect_ray(ray)
	return hit.is_empty()


func _flat_dist(p: Vector3) -> float:
	var d := p - global_position
	d.y = 0
	return d.length()


func _move_towards(target: Vector3, speed: float, delta: float) -> void:
	var dir := target - global_position
	dir.y = 0
	if dir.length() < 0.2:
		velocity = Vector3.ZERO
		return
	_move_dir(dir.normalized(), speed, delta)


func _move_dir(dir: Vector3, speed: float, _delta: float) -> void:
	velocity.x = dir.x * speed
	velocity.z = dir.z * speed
	velocity.y = 0
	move_and_slide()
