extends SceneTree
## 冒烟测试：不依赖窗口，校验人物清单、图集规格与 SpriteFrames 构建。
##
## 运行：
##   godot --headless --path . --script res://tests/smoke_test.gd
## 退出码 0 = 通过，1 = 失败。

const MANIFEST := "res://data/characters/manifest.json"
const PLAYER_SCENE := "res://scenes/characters/player.tscn"

var _failures: Array[String] = []
var _checks := 0

func _initialize() -> void:
	_test_manifest()
	_test_player_visual()
	_report()

func _check(condition: bool, message: String) -> void:
	_checks += 1
	if not condition:
		_failures.append(message)

func _test_manifest() -> void:
	var file := FileAccess.open(MANIFEST, FileAccess.READ)
	if file == null:
		_failures.append("无法读取 " + MANIFEST)
		return
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		_failures.append("manifest 不是 JSON 对象")
		return

	var doc: Dictionary = parsed
	var characters: Dictionary = doc.get("characters", {})
	_check(not characters.is_empty(), "manifest 里没有任何角色")

	var time_growth: Dictionary = doc.get("time_growth", {})
	_check(time_growth.get("enabled", true) == false, "time_growth.enabled 必须为 false")
	_check(time_growth.get("auto_appearance_switch", true) == false,
		"time_growth.auto_appearance_switch 必须为 false")

	var forbidden := ["age", "birth_year", "age_up", "growth_stage", "time_to_appearance"]
	for key: String in forbidden:
		_check(not JSON.stringify(doc).contains("\"" + key + "\""),
			"manifest 出现禁用字段 " + key)

	for cid: String in characters:
		for aid: String in characters[cid]:
			var entry: Dictionary = characters[cid][aid]
			var sprite: Dictionary = entry.get("sprite", {})
			var path: String = sprite.get("path", "")
			_check(path.begins_with("res://"), "%s/%s 的 path 不是 res://" % [cid, aid])
			_check(sprite.get("columns", 0) == 3, "%s/%s 列数应为 3" % [cid, aid])
			_check(sprite.get("rows", 0) == 4, "%s/%s 行数应为 4" % [cid, aid])
			var order: Array = sprite.get("row_order", [])
			_check(order == ["down", "left", "right", "up"],
				"%s/%s 行序必须为 down/left/right/up" % [cid, aid])

			var texture := load(path) as Texture2D
			_check(texture != null, "%s/%s 图集加载失败：%s" % [cid, aid, path])
			if texture != null:
				_check(texture.get_width() == 192 and texture.get_height() == 384,
					"%s/%s 图集应为 192x384，实际 %dx%d" % [cid, aid,
					texture.get_width(), texture.get_height()])

func _test_player_visual() -> void:
	var scene := load(PLAYER_SCENE) as PackedScene
	_check(scene != null, "玩家场景加载失败")
	if scene == null:
		return
	var player := scene.instantiate()
	var visual := player.get_node_or_null("Visual") as AnimatedSprite2D
	_check(visual != null, "玩家场景缺少 Visual 节点")
	if visual == null:
		player.free()
		return

	visual.setup("rudeus", "child")
	var frames := visual.sprite_frames
	_check(frames != null, "SpriteFrames 未构建")
	if frames != null:
		var names := frames.get_animation_names()
		_check(names.size() == 8, "动画数量应为 8，实际 %d：%s" % [names.size(), names])
		for dir: String in ["down", "left", "right", "up"]:
			var walk := "walk_" + dir
			var idle := "idle_" + dir
			_check(frames.has_animation(walk), "缺少动画 " + walk)
			_check(frames.has_animation(idle), "缺少动画 " + idle)
			if frames.has_animation(walk):
				_check(frames.get_frame_count(walk) == 4,
					"%s 应有 4 帧，实际 %d" % [walk, frames.get_frame_count(walk)])
			if frames.has_animation(idle):
				_check(frames.get_frame_count(idle) == 1,
					"%s 应有 1 帧，实际 %d" % [idle, frames.get_frame_count(idle)])
	_check(is_equal_approx(visual.offset.y, -48.0),
		"脚底偏移应为 -48，实际 %.1f" % visual.offset.y)
	player.free()

func _report() -> void:
	if _failures.is_empty():
		print("SMOKE PASS  (%d 项检查)" % _checks)
		quit(0)
		return
	print("SMOKE FAIL  (%d 项检查，%d 项失败)" % [_checks, _failures.size()])
	for message: String in _failures:
		print("  - " + message)
	quit(1)
