extends Node2D
## 开发期测试场景：32px 网格地面 + 若干障碍物，用于验证移动、碰撞与 Y 排序。
## 正式地图接入后本场景只保留为 dev_tests 里的回归用例。

const TILE := 32

var map_size := Vector2(1280, 960)

# 障碍物矩形（x, y, w, h），32 的整数倍，便于和瓦片地图对齐
var obstacles: Array[Rect2] = [
	Rect2(320, 224, 192, 32),    # 横向矮墙
	Rect2(640, 352, 32, 128),    # 纵向立柱
	Rect2(160, 480, 128, 96),    # 房屋地基
	Rect2(832, 160, 96, 96),     # 箱子堆
]

func _ready() -> void:
	for rect: Rect2 in obstacles:
		var body := StaticBody2D.new()
		body.name = "Obstacle_%d_%d" % [int(rect.position.x), int(rect.position.y)]
		body.position = rect.position + rect.size * 0.5
		var shape := CollisionShape2D.new()
		var box := RectangleShape2D.new()
		box.size = rect.size
		shape.shape = box
		body.add_child(shape)
		add_child(body)
	_apply_camera_limits()

func _apply_camera_limits() -> void:
	var player := get_tree().get_first_node_in_group("player")
	if player == null:
		return
	var camera := player.get_node_or_null("Camera") as Camera2D
	if camera == null:
		return
	camera.limit_left = 0
	camera.limit_top = 0
	camera.limit_right = int(map_size.x)
	camera.limit_bottom = int(map_size.y)

func _draw() -> void:
	draw_rect(Rect2(Vector2.ZERO, map_size), Color("3c4a34"))
	var grid := Color("44543a")
	for x in range(0, int(map_size.x) + TILE, TILE):
		draw_line(Vector2(x, 0), Vector2(x, map_size.y), grid, 1.0)
	for y in range(0, int(map_size.y) + TILE, TILE):
		draw_line(Vector2(0, y), Vector2(map_size.x, y), grid, 1.0)
	for rect: Rect2 in obstacles:
		draw_rect(rect, Color("6b5a44"))
		draw_rect(rect, Color("8a7360"), false, 2.0)
	# 地图边界
	draw_rect(Rect2(Vector2.ZERO, map_size), Color("20261c"), false, 4.0)
