extends CharacterBody2D
## 通用 NPC：固定站位，玩家靠近时转向玩家，按交互键输出占位对话。
## 对话内容与人物资源解耦：这里只暴露 character_id / appearance_id / display_name。

@export var character_id: String = "npc_villager_m"
@export var appearance_id: String = "base"
@export var display_name: String = "居民"
@export var interact_radius: float = 44.0

@onready var visual: AnimatedSprite2D = $Visual

var _player: Node2D = null

func _ready() -> void:
	visual.setup(character_id, appearance_id)
	add_to_group("npc")
	call_deferred("_find_player")

func _find_player() -> void:
	_player = get_tree().get_first_node_in_group("player") as Node2D

func _process(_delta: float) -> void:
	if _player == null:
		return
	var to_player := _player.global_position - global_position
	if to_player.length() > interact_radius:
		return
	_face(to_player)
	if Input.is_action_just_pressed("interact"):
		_on_interact()

func _face(to_player: Vector2) -> void:
	var dir := "down"
	if absf(to_player.x) >= absf(to_player.y):
		dir = "right" if to_player.x > 0.0 else "left"
	else:
		dir = "down" if to_player.y > 0.0 else "up"
	var anim := "idle_" + dir
	if visual.animation != anim:
		visual.play(anim)

func _on_interact() -> void:
	print("[interact] %s (%s:%s)" % [display_name, character_id, appearance_id])
