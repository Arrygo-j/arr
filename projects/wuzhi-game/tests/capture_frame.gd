extends SceneTree
## 抓取一帧渲染结果，作为「实机画面」证据。
##
## 运行（需要窗口，不能用 --headless）：
##   godot --path . --script res://tests/capture_frame.gd

const SCENE := "res://scenes/dev_tests/character_motion_test.tscn"
const OUT_DIR := "res://.screenshots"

func _initialize() -> void:
	_run()

func _run() -> void:
	var scene := load(SCENE) as PackedScene
	if scene == null:
		print("CAPTURE FAIL: 场景加载失败")
		quit(1)
		return
	var root_node := scene.instantiate()
	root.add_child(root_node)

	# 让玩家走向左上方，顺便验证朝向切换
	var player := root_node.get_node_or_null("Player")
	for i in 20:
		await process_frame
	if player != null and player.has_method("_update_visual"):
		player.call("_update_visual", Vector2(-1, -1))
	for i in 10:
		await process_frame

	DirAccess.make_dir_recursive_absolute(ProjectSettings.globalize_path(OUT_DIR))
	var image := root.get_viewport().get_texture().get_image()
	var path := ProjectSettings.globalize_path(OUT_DIR + "/motion_test.png")
	var err := image.save_png(path)
	if err == OK:
		print("CAPTURE OK: " + path)
		quit(0)
	else:
		print("CAPTURE FAIL: " + str(err))
		quit(1)
