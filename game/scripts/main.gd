extends Node3D
## Game director: builds night environment, spawns talismans & ghost,
## handles win/lose and the HUD.

const TALISMAN_SCENE := preload("res://scenes/talisman.tscn")
const TOTAL_TALISMANS := 7

const TALISMAN_SPOTS: Array[Vector3] = [
	Vector3(4, 1.0, 23.5),      # bridge corner
	Vector3(0, 1.4, 50.4),      # shore pavilion (above the stone bench)
	Vector3(8, 1.1, -3),        # tiger tower, ground floor
	Vector3(6.5, 11.2, -3),     # tiger tower, 4F
	Vector3(6.5, 21.4, -3),     # tiger tower, 7F
	Vector3(-8, 1.1, -3),       # dragon tower, ground floor
	Vector3(-9.5, 21.4, -3),    # dragon tower, 7F
]

const LANTERN_LIGHTS: Array[Vector3] = [
	Vector3(-13, 2.85, 7), Vector3(13, 2.85, 7),
	Vector3(-13, 2.85, -8), Vector3(13, 2.85, -8),
	Vector3(-3.4, 2.85, 9.3), Vector3(3.4, 2.85, 9.3),
	Vector3(0, 2.35, 16.5), Vector3(4, 2.35, 16.5),
	Vector3(4, 2.35, 23.5), Vector3(-2.5, 2.35, 23.5),
	Vector3(-2.5, 2.35, 30.5), Vector3(3, 2.35, 30.5),
	Vector3(3, 2.35, 37.5), Vector3(0, 2.35, 37.5),
]

const GHOST_WAYPOINTS: Array[Vector3] = [
	Vector3(0, 0, 0), Vector3(-13, 0, -6), Vector3(13, 0, -6),
	Vector3(-13, 0, 7), Vector3(13, 0, 7), Vector3(0, 0, 8.5),
	Vector3(0, 0, 14), Vector3(4, 0, 20), Vector3(-2.5, 0, 27),
	Vector3(3, 0, 34), Vector3(0, 0, 41),
]

var collected := 0
var _whisper_cd := 12.0

@onready var player: CharacterBody3D = $Player
@onready var ghost: CharacterBody3D = $Ghost
@onready var counter_label: Label = $UI/Counter
@onready var message_label: Label = $UI/Message
@onready var fade_rect: ColorRect = $UI/Fade
@onready var stamina_bar: ColorRect = $UI/StaminaBar/Fill
@onready var heartbeat: AudioStreamPlayer = $Heartbeat
@onready var wind: AudioStreamPlayer = $Wind
@onready var whisper: AudioStreamPlayer = $Whisper


func _ready() -> void:
	_setup_environment()
	_setup_lanterns()
	_setup_talismans()
	_loop_wav(wind.stream)
	wind.play()
	ghost.setup(player, GHOST_WAYPOINTS)
	player.died.connect(_on_player_died)
	player.escaped.connect(_on_player_escaped)
	$ExitZone.body_entered.connect(_on_exit_zone)
	_update_counter()
	_show_message("深夜，你從「虎口」走了進來……犯了大忌。\n" +
			"收集七張符咒，再從「龍口」離開，方可化解厄運。\n\n" +
			"WASD 移動｜Shift 衝刺｜F 手電筒｜空白鍵 跳躍", 9.0)


func _process(delta: float) -> void:
	stamina_bar.scale.x = player.stamina / player.STAMINA_MAX
	# heartbeat when the wraith hunts you
	if ghost.state == 1 and not player.dead and not player.won:
		if not heartbeat.playing:
			heartbeat.play()
	# occasional whispers
	_whisper_cd -= delta
	if _whisper_cd <= 0.0:
		_whisper_cd = randf_range(18.0, 40.0)
		if not player.dead and not player.won:
			whisper.pitch_scale = randf_range(0.7, 1.1)
			whisper.play()
	if Input.is_action_just_pressed("restart"):
		get_tree().reload_current_scene()


# ---------------------------------------------------------------- environment
func _setup_environment() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(0.006, 0.009, 0.016)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.10, 0.13, 0.19)
	env.ambient_light_energy = 0.35
	env.tonemap_mode = Environment.TONE_MAPPER_FILMIC
	env.fog_enabled = true
	env.fog_light_color = Color(0.035, 0.05, 0.075)
	env.fog_density = 0.022
	env.fog_sky_affect = 1.0
	env.volumetric_fog_enabled = true
	env.volumetric_fog_density = 0.025
	env.volumetric_fog_albedo = Color(0.6, 0.7, 0.8)
	env.volumetric_fog_length = 80.0
	env.glow_enabled = true
	env.glow_intensity = 0.6
	env.glow_bloom = 0.1
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	var moon := DirectionalLight3D.new()
	moon.light_color = Color(0.5, 0.62, 0.85)
	moon.light_energy = 0.22
	moon.shadow_enabled = true
	moon.rotation_degrees = Vector3(-38, 152, 0)
	add_child(moon)


func _setup_lanterns() -> void:
	for pos in LANTERN_LIGHTS:
		var l := OmniLight3D.new()
		l.position = pos
		l.light_color = Color(1.0, 0.42, 0.15)
		l.light_energy = 1.6
		l.omni_range = 7.0
		l.omni_attenuation = 1.6
		add_child(l)
	# glowing statue eyes
	for x in [-8.0, 8.0]:
		var e := OmniLight3D.new()
		e.position = Vector3(x, 3.9, 7.0)
		e.light_color = Color(1.0, 0.25, 0.05)
		e.light_energy = 0.9
		e.omni_range = 4.0
		add_child(e)


func _setup_talismans() -> void:
	for pos in TALISMAN_SPOTS:
		var t := TALISMAN_SCENE.instantiate()
		t.position = pos
		t.collected.connect(_on_talisman_collected)
		add_child(t)


func _loop_wav(stream: AudioStream) -> void:
	if stream is AudioStreamWAV:
		stream.loop_mode = AudioStreamWAV.LOOP_FORWARD
		stream.loop_begin = 0
		stream.loop_end = stream.data.size() / 2


# ---------------------------------------------------------------- game events
func _on_talisman_collected() -> void:
	collected += 1
	$Pickup.play()
	_update_counter()
	if collected >= TOTAL_TALISMANS:
		_show_message("七張符咒已集齊——快到「龍口」離開！", 6.0)
	else:
		_show_message("拾獲符咒（%d／%d）" % [collected, TOTAL_TALISMANS], 3.0)


func _on_exit_zone(body: Node3D) -> void:
	if not body.is_in_group("player"):
		return
	if collected >= TOTAL_TALISMANS:
		player.win()
	else:
		_show_message("龍口緊閉……似乎還缺符咒（%d／%d）"
				% [collected, TOTAL_TALISMANS], 4.0)


func _on_player_died() -> void:
	$DeathSfx.play()
	heartbeat.stop()
	var tw := create_tween()
	fade_rect.color = Color(0.25, 0.0, 0.0, 0.0)
	tw.tween_property(fade_rect, "color", Color(0.02, 0.0, 0.0, 1.0), 1.2)
	message_label.text = "虎靈把你拖進了黑暗……\n\n按 R 重新來過"
	message_label.visible = true


func _on_player_escaped() -> void:
	$Gong.play()
	heartbeat.stop()
	var tw := create_tween()
	fade_rect.color = Color(1.0, 0.98, 0.9, 0.0)
	tw.tween_property(fade_rect, "color", Color(1.0, 0.98, 0.9, 1.0), 3.0)
	message_label.text = "你從龍口踏出，厄運盡除。\n遠方的天，亮了。\n\n按 R 再玩一次"
	message_label.visible = true


func _update_counter() -> void:
	counter_label.text = "符咒 %d／%d" % [collected, TOTAL_TALISMANS]


func _show_message(text: String, duration: float) -> void:
	message_label.text = text
	message_label.visible = true
	var timer := get_tree().create_timer(duration)
	timer.timeout.connect(func() -> void:
		if not player.dead and not player.won:
			message_label.visible = false)
