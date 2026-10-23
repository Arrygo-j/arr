extends Node
## 输入映射：在运行时补齐移动/交互动作，避免手写 project.godot 的事件序列。
## 支持方向键与 WASD，交互键为 E / 空格。

const ACTIONS := {
	"move_left": [KEY_A, KEY_LEFT],
	"move_right": [KEY_D, KEY_RIGHT],
	"move_up": [KEY_W, KEY_UP],
	"move_down": [KEY_S, KEY_DOWN],
	"interact": [KEY_E, KEY_SPACE],
}

func _enter_tree() -> void:
	for action: String in ACTIONS:
		if not InputMap.has_action(action):
			InputMap.add_action(action)
		for key: Key in ACTIONS[action]:
			if not _has_key(action, key):
				var event := InputEventKey.new()
				event.physical_keycode = key
				InputMap.action_add_event(action, event)

func _has_key(action: String, key: Key) -> bool:
	for event: InputEvent in InputMap.action_get_events(action):
		if event is InputEventKey and event.physical_keycode == key:
			return true
	return false
