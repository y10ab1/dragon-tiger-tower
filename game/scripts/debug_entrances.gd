extends Node3D
## Walk both statue entrances in and out using real player movement.
## Run: godot --headless --path game res://scenes/debug_entrances.tscn

const ENTRANCES := [-8.0, 8.0]
# Z=0 is inside the tower doorway. Farther in, the stair flight crosses this
# axis; debug_climb tests its actual walking route rather than its side wall.
const ROUTE := [6.8, 3.0, 0.0, 3.0, 6.8, 9.0]
var entrance := 0
var waypoint := 0
var timer := 0.0

@onready var player: CharacterBody3D = $Main/Player
@onready var ghost: CharacterBody3D = $Main/Ghost


func _ready() -> void:
	process_physics_priority = -1
	$Main/ExitZone.set_deferred("monitoring", false)
	player.won = false
	_start_entrance()


func _start_entrance() -> void:
	Input.action_release("move_forward")
	player.global_position = Vector3(ENTRANCES[entrance], 0.2, 9.0)
	player.velocity = Vector3.ZERO
	waypoint = 0
	timer = 0.0


func _physics_process(delta: float) -> void:
	ghost.global_position = Vector3(0, -60, -100)
	player.won = false
	if player.dead:
		print("ENTRANCES_FAIL player died at %s" % str(player.global_position))
		_finish(1)
		return
	var target := Vector3(ENTRANCES[entrance], 0, ROUTE[waypoint])
	var d := target - player.global_position
	d.y = 0
	if d.length() < 0.25 and absf(player.global_position.y) < 0.75:
		Input.action_release("move_forward")
		print("ENTRANCE x=%.1f z=%.1f OK" % [target.x, target.z])
		waypoint += 1
		timer = 0.0
		if waypoint == ROUTE.size():
			entrance += 1
			if entrance == ENTRANCES.size():
				_finish(0)
			else:
				_start_entrance()
		return
	timer += delta
	if timer > 8.0:
		print("ENTRANCES_STUCK target=%s pos=%s" % [
				str(target), str(player.global_position)])
		_finish(1)
		return
	player.rotation.y = atan2(-d.x, -d.z)
	Input.action_press("move_forward")


func _finish(fails: int) -> void:
	Input.action_release("move_forward")
	set_physics_process(false)
	print("ENTRANCES_DONE fails=%d" % fails)
	get_tree().quit(1 if fails > 0 else 0)
