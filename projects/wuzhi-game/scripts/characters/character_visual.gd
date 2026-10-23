extends AnimatedSprite2D
## 人物外观加载器。
##
## 只认 character_id + appearance_id，从 data/characters/manifest.json 读取图集信息，
## 在运行时切出 SpriteFrames，避免把角色绑定到某张固定贴图的绝对路径。
## 本类不读取任何时间/年龄字段：外观完全由配置决定。

const MANIFEST_PATH := "res://data/characters/manifest.json"

static var _manifest: Dictionary = {}

@export var character_id: String = ""
@export var appearance_id: String = ""
@export var fps: float = 7.0

func setup(cid: String, aid: String) -> void:
	character_id = cid
	appearance_id = aid
	_build()

func _ready() -> void:
	if not character_id.is_empty():
		_build()

func _build() -> void:
	var manifest := _load_manifest()
	var entry: Variant = manifest.get("characters", {}).get(character_id, {}).get(appearance_id, null)
	if entry == null:
		push_warning("manifest 中没有外观：%s / %s" % [character_id, appearance_id])
		return
	var info: Dictionary = entry.get("sprite", {})
	var path: String = info.get("path", "")
	if path.is_empty():
		push_warning("外观缺少 sprite.path：%s / %s" % [character_id, appearance_id])
		return
	var texture := load(path)
	if texture == null:
		push_warning("图集加载失败：" + path)
		return

	var size: Array = info.get("frame_size", [64, 96])
	var fw: int = int(size[0])
	var fh: int = int(size[1])
	var cols: int = int(info.get("columns", 3))
	var rows: int = int(info.get("rows", 4))
	var row_order: Array = info.get("row_order", ["down", "left", "right", "up"])
	var sequence: Array = info.get("walk_sequence", [1, 0, 1, 2])
	var speed: float = float(info.get("fps", fps))

	var frames := SpriteFrames.new()
	if frames.has_animation("default"):
		frames.remove_animation("default")

	for row in range(min(rows, row_order.size())):
		var dir := String(row_order[row])
		var walk := "walk_" + dir
		frames.add_animation(walk)
		frames.set_animation_speed(walk, speed)
		frames.set_animation_loop(walk, true)
		for col: int in sequence:
			if col < 0 or col >= cols:
				continue
			frames.add_frame(walk, _slice(texture, col, row, fw, fh))

		var idle := "idle_" + dir
		frames.add_animation(idle)
		frames.set_animation_speed(idle, 1.0)
		frames.set_animation_loop(idle, false)
		frames.add_frame(idle, _slice(texture, 1, row, fw, fh))

	sprite_frames = frames
	centered = true
	offset = Vector2(0, -fh / 2.0)   # 脚底落在节点原点
	play("idle_down")

func _slice(texture: Texture2D, col: int, row: int, fw: int, fh: int) -> AtlasTexture:
	var atlas := AtlasTexture.new()
	atlas.atlas = texture
	atlas.region = Rect2(col * fw, row * fh, fw, fh)
	return atlas

func _load_manifest() -> Dictionary:
	if not _manifest.is_empty():
		return _manifest
	var file := FileAccess.open(MANIFEST_PATH, FileAccess.READ)
	if file == null:
		push_error("找不到人物清单：" + MANIFEST_PATH)
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	if typeof(parsed) != TYPE_DICTIONARY:
		push_error("人物清单不是合法 JSON：" + MANIFEST_PATH)
		return {}
	_manifest = parsed
	return _manifest
