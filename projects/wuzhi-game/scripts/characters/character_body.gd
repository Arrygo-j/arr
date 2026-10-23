extends CharacterBody2D
## 玩家角色：四方向移动 + 待机/行走动画切换。
##
## 移动用 move_and_slide，velocity 不再重复乘 delta；
## 朝向在停止移动时保持最后一次的方向，避免原地转身翻错。

@export var character_id: String = "rudeus"
@export var appearance_id: String = "child"
@export var move_speed: float = 110.0

@onready var visual: AnimatedSprite2D = $Visual

var _facing: String = "down"

func _ready() -> void:
	visual.setup(character_id, appearance_id)

func _physics_process(_delta: float) -> void:
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = direction * move_speed
	move_and_slide()
	_update_visual(direction)

func _update_visual(direction: Vector2) -> void:
	var moving := direction.length() > 0.01
	if moving:
		if absf(direction.x) >= absf(direction.y):
			_facing = "right" if direction.x > 0.0 else "left"
		else:
			_facing = "down" if direction.y > 0.0 else "up"
	var anim := ("walk_" if moving else "idle_") + _facing
	if visual.animation != anim:
		visual.play(anim)
