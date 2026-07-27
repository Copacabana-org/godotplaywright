extends Node
## Godot Playwright — portable Godot automation bridge (web only).
##
## Drop into any Godot+Vue shell game as an autoload named `AutomationBridge`.
## Enable by shell writing localStorage `__GAME_AUTO__ = "1"` (never on prod).
##
## Protocol (parent → iframe via godotMessageReceiver):
##   { "action": "auto", "id": "<req-id>", "cmd": "<cmd>", "args": { ... } }
##
## Responses (iframe → parent postMessage):
##   { "status": "auto_ready" }
##   { "status": "auto_result", "id": "...", "ok": true|false, "data"|"error": ... }
##
## Pointer commands use **viewport coordinates** of the Godot game (not CSS pixels).
## Free scripting: move / down / up / click / drag — no game-specific knowledge required.

const FLAG_KEY := "__GAME_AUTO__"
const PROTOCOL_VERSION := 1

var enabled: bool = false
var _last_pos: Vector2 = Vector2.ZERO
var _button_mask: int = 0


func _ready() -> void:
	if not OS.has_feature("web"):
		return
	if not _flag_enabled():
		return
	enabled = true
	# Defer so main scene / receiver exist.
	call_deferred("_announce_ready")


func _flag_enabled() -> bool:
	var raw = JavaScriptBridge.eval("localStorage.getItem('%s')" % FLAG_KEY)
	if raw == null:
		return false
	var s := str(raw).to_lower()
	return s == "1" or s == "true"


## Called from main.gd when a godotMessageReceiver payload has action == "auto".
func handle(data: Dictionary) -> void:
	var req_id := str(data.get("id", ""))
	if not enabled:
		_reply(req_id, false, {}, "automation_disabled")
		return

	var cmd := str(data.get("cmd", ""))
	var args: Dictionary = {}
	if data.has("args") and data["args"] is Dictionary:
		args = data["args"]

	var result: Dictionary = _dispatch(cmd, args)
	var ok: bool = bool(result.get("ok", false))
	if ok:
		_reply(req_id, true, result.get("data", {}), "")
	else:
		_reply(req_id, false, result.get("data", {}), str(result.get("error", "unknown_error")))


func _dispatch(cmd: String, args: Dictionary) -> Dictionary:
	match cmd:
		"ping":
			return _ok({
				"pong": true,
				"protocol": PROTOCOL_VERSION,
				"viewport": _viewport_size_dict(),
			})
		"mouse_move":
			return _cmd_mouse_move(args)
		"mouse_down":
			return _cmd_mouse_button(args, true)
		"mouse_up":
			return _cmd_mouse_button(args, false)
		"click":
			return _cmd_click(args)
		"drag":
			return _cmd_drag(args)
		"get_state":
			return _ok(_collect_state())
		"set_currency":
			return _cmd_set_currency(args)
		"reload_config":
			return _cmd_reload_config()
		"wait_frames":
			return _cmd_wait_frames(args)
		# Reliable control activation (works when pure pointer fails on web GUI)
		"get_hotspots":
			return _ok({"hotspots": _collect_hotspots()})
		"tap_control":
			return _cmd_tap_control(args)
		"set_language":
			return _cmd_set_language(args)
		"open_menu":
			return _cmd_open_menu(args)
		"open_languages":
			return _cmd_open_languages(args)
		"open_rules":
			return _cmd_open_rules(args)
		"close_rules":
			return _cmd_close_rules(args)
		"bet_plus":
			return _cmd_bet_plus(args)
		"bet_minus":
			return _cmd_bet_minus(args)
		"spin":
			return _cmd_spin(args)
		_:
			return _err("unknown_cmd", {"cmd": cmd})


# ─── Pointer (free scripting) ─────────────────────────────────────────────────

func _cmd_mouse_move(args: Dictionary) -> Dictionary:
	var pos := _pos_from_args(args)
	_inject_motion(pos)
	return _ok({"x": pos.x, "y": pos.y})


func _cmd_mouse_button(args: Dictionary, pressed: bool) -> Dictionary:
	var pos := _pos_from_args(args, true)
	var button := _button_from_args(args)
	_inject_button(pos, button, pressed)
	return _ok({
		"x": pos.x,
		"y": pos.y,
		"button": _button_name(button),
		"pressed": pressed,
	})


func _cmd_click(args: Dictionary) -> Dictionary:
	var pos := _pos_from_args(args)
	var button := _button_from_args(args)
	# Move first so Control hover / mouse_entered paths behave like a real pointer.
	_inject_motion(pos)
	_inject_button(pos, button, true)
	_inject_button(pos, button, false)
	# Web GUI often ignores synthetic InputEvents for TextureButton; also activate
	# the topmost BaseButton under the point so clicks actually fire handlers.
	var activated := ""
	if bool(args.get("activate", true)):
		activated = _activate_at(pos)
	return _ok({
		"x": pos.x,
		"y": pos.y,
		"button": _button_name(button),
		"activated": activated,
	})


func _cmd_drag(args: Dictionary) -> Dictionary:
	var from := Vector2(
		float(args.get("x1", args.get("from_x", _last_pos.x))),
		float(args.get("y1", args.get("from_y", _last_pos.y)))
	)
	var to := Vector2(
		float(args.get("x2", args.get("to_x", from.x))),
		float(args.get("y2", args.get("to_y", from.y)))
	)
	var steps: int = maxi(1, int(args.get("steps", 10)))
	var button := _button_from_args(args)

	_inject_motion(from)
	_inject_button(from, button, true)
	for i in range(1, steps + 1):
		var t := float(i) / float(steps)
		var p := from.lerp(to, t)
		_inject_motion(p)
	_inject_button(to, button, false)
	return _ok({
		"x1": from.x, "y1": from.y,
		"x2": to.x, "y2": to.y,
		"steps": steps,
		"button": _button_name(button),
	})


func _pos_from_args(args: Dictionary, optional: bool = false) -> Vector2:
	if args.has("x") and args.has("y"):
		return Vector2(float(args["x"]), float(args["y"]))
	if optional:
		return _last_pos
	# Default to last known position if only button given after a move.
	return _last_pos


func _button_from_args(args: Dictionary) -> MouseButton:
	var raw = args.get("button", "left")
	var name := str(raw).to_lower()
	match name:
		"right", "r", "2", "mouse_right":
			return MOUSE_BUTTON_RIGHT
		"middle", "m", "3", "mouse_middle":
			return MOUSE_BUTTON_MIDDLE
		_:
			return MOUSE_BUTTON_LEFT


func _button_name(button: MouseButton) -> String:
	match button:
		MOUSE_BUTTON_RIGHT:
			return "right"
		MOUSE_BUTTON_MIDDLE:
			return "middle"
		_:
			return "left"


func _push_input(ev: InputEvent) -> void:
	# push_input delivers into the GUI stack more reliably than parse_input_event alone on web.
	var vp := get_viewport()
	if vp:
		vp.push_input(ev, true)
	else:
		Input.parse_input_event(ev)


func _inject_motion(pos: Vector2) -> void:
	var ev := InputEventMouseMotion.new()
	ev.position = pos
	ev.global_position = pos
	ev.relative = pos - _last_pos
	ev.button_mask = _button_mask
	_push_input(ev)
	_last_pos = pos


func _inject_button(pos: Vector2, button: MouseButton, pressed: bool) -> void:
	var bit := 1 << (button - 1)
	if pressed:
		_button_mask |= bit
	else:
		_button_mask &= ~bit

	var ev := InputEventMouseButton.new()
	ev.position = pos
	ev.global_position = pos
	ev.button_index = button
	ev.pressed = pressed
	ev.button_mask = _button_mask
	ev.double_click = false
	_push_input(ev)
	_last_pos = pos


var _hit_button: BaseButton = null


## Walk visible Controls; deepest BaseButton whose global rect contains pos → _hit_button.
func _walk_for_button(node: Node, pos: Vector2) -> void:
	for child in node.get_children():
		_walk_for_button(child, pos)
		if child is BaseButton:
			var btn := child as BaseButton
			if not btn.is_visible_in_tree() or btn.disabled:
				continue
			if btn.mouse_filter == Control.MOUSE_FILTER_IGNORE:
				continue
			var rect := btn.get_global_rect()
			if rect.has_point(pos):
				# Last DFS match ≈ topmost among siblings / deeper first when parent visited after.
				_hit_button = btn


func _activate_at(pos: Vector2) -> String:
	_hit_button = null
	_walk_for_button(get_tree().root, pos)
	if _hit_button == null:
		return ""
	_activate_button(_hit_button)
	return str(_hit_button.get_path())


func _activate_button(btn: BaseButton) -> void:
	# Fire the same signals real clicks would, covering pressed / button_down / toggle.
	if btn.disabled:
		return
	if btn.toggle_mode:
		btn.button_pressed = not btn.button_pressed
		btn.toggled.emit(btn.button_pressed)
	btn.button_down.emit()
	btn.pressed.emit()
	btn.button_up.emit()


func _find_named(name: String) -> Node:
	return get_tree().root.find_child(name, true, false)


func _cmd_tap_control(args: Dictionary) -> Dictionary:
	var name := str(args.get("name", args.get("path", "")))
	if name.is_empty():
		return _err("missing_name")
	var node: Node = null
	if name.begins_with("/") or name.begins_with("res://"):
		node = get_node_or_null(name)
	if node == null:
		node = _find_named(name)
	if node == null:
		return _err("control_not_found", {"name": name})
	if not (node is Control):
		return _err("not_a_control", {"name": name, "type": node.get_class()})
	var ctrl := node as Control
	var rect := ctrl.get_global_rect()
	var pos := rect.get_center()
	_inject_motion(pos)
	_inject_button(pos, MOUSE_BUTTON_LEFT, true)
	_inject_button(pos, MOUSE_BUTTON_LEFT, false)
	if ctrl is BaseButton:
		_activate_button(ctrl as BaseButton)
	return _ok({
		"name": name,
		"path": str(ctrl.get_path()),
		"x": pos.x,
		"y": pos.y,
		"rect": {"x": rect.position.x, "y": rect.position.y, "w": rect.size.x, "h": rect.size.y},
	})


func _collect_hotspots() -> Array:
	var names := [
		"PlusBtn", "MinusBtn", "SpinBg", "SpinBtn", "AutoBtn", "InfoBtn",
		"pt", "en", "Language", "Languages", "SideBar", "SideMenu",
	]
	var out: Array = []
	for n in names:
		var node := _find_named(n)
		if node == null or not (node is Control):
			continue
		var ctrl := node as Control
		if not ctrl.is_visible_in_tree():
			continue
		var rect := ctrl.get_global_rect()
		var c := rect.get_center()
		out.append({
			"name": n,
			"path": str(ctrl.get_path()),
			"x": c.x,
			"y": c.y,
			"w": rect.size.x,
			"h": rect.size.y,
			"visible": true,
		})
	return out


func _cmd_set_language(args: Dictionary) -> Dictionary:
	var code := str(args.get("code", args.get("lang", "pt"))).to_lower()
	if code.is_empty():
		code = "pt"
	var force_show := bool(args.get("show", true))
	# Prefer the in-game language panel so UI animates like a real pick.
	var panel := _find_named("Language")
	if panel != null and panel.has_method("_toggle_language"):
		if force_show and panel.has_method("_show") and not (panel as CanvasItem).visible:
			panel.call("_show")
		# Ensure the lang row is built and scrollable before toggle.
		if panel.has_method("_scroll_to_button") and "buttons" in panel:
			var buttons: Dictionary = panel.buttons
			if buttons.has(code):
				panel.call("_scroll_to_button", buttons[code])
		panel.call("_toggle_language", code)
		# Refresh sidebar flag/label if present
		var bar := _find_named("SideBar")
		if bar != null and bar.has_method("change_language"):
			bar.call("change_language")
		return _ok({"code": code, "via": "language_panel"})
	# Fallback: Helpers / TranslationServer only
	var helpers := _helpers()
	if helpers != null and helpers.has_method("set_language"):
		helpers.set_language(code)
	TranslationServer.set_locale(code)
	return _ok({"code": code, "via": "helpers"})


func _cmd_open_menu(_args: Dictionary) -> Dictionary:
	var sm := _find_named("SideMenu")
	if sm != null and sm.has_method("do_menu"):
		sm.call("do_menu")
		return _ok({"via": "SideMenu.do_menu"})
	# Fallback: press first menu Button near SideMenu
	if sm != null:
		var parent := sm.get_parent()
		if parent != null:
			var btn := parent.get_node_or_null("Button")
			if btn is BaseButton:
				_activate_button(btn as BaseButton)
				return _ok({"via": "Menu/Button"})
	return _err("menu_not_found")


func _cmd_open_languages(_args: Dictionary) -> Dictionary:
	# Prefer SideBar handler (opens Language panel + dimmer, closes sidebar anim).
	var bar := _find_named("SideBar")
	if bar != null and bar.has_method("_on_languages_pressed"):
		# Ensure sidebar is open so the action is visible
		var sm := _find_named("SideMenu")
		if sm != null and sm.has_method("do_menu"):
			var sidebar: Node = sm.get("sidebar") if "sidebar" in sm else null
			# do_menu is safe to call; if already open it still shows
			if bar is CanvasItem and not (bar as CanvasItem).visible:
				sm.call("do_menu")
		bar.call("_on_languages_pressed")
		return _ok({"via": "SideBar._on_languages_pressed"})
	var lang_btn := _find_named("Languages")
	if lang_btn is BaseButton:
		_activate_button(lang_btn as BaseButton)
		return _ok({"via": "Languages.pressed"})
	return _err("languages_entry_not_found")


func _menu_dimmer() -> CanvasItem:
	var d := _find_named("MenuDimmer")
	return d as CanvasItem if d is CanvasItem else null


## There are two nodes named "Rules": the SideBar menu Button and the Panel modal.
## Prefer the Panel that owns open/close animation.
func _rules_panel() -> Node:
	# Explicit path used in CrapsSlot / Template-line mains
	var direct := get_node_or_null("/root/Main/Menu/SideMenu/Rules")
	if direct != null and direct is Panel:
		return direct
	var candidates: Array = []
	_collect_named(get_tree().root, "Rules", candidates)
	for n in candidates:
		if n is Panel and (n.has_method("_show") or n.has_method("_on_close_button_pressed")):
			return n
	for n in candidates:
		if n is Panel:
			return n
	return null


func _collect_named(node: Node, name: String, out: Array) -> void:
	if node.name == name:
		out.append(node)
	for child in node.get_children():
		_collect_named(child, name, out)


func _cmd_open_rules(_args: Dictionary) -> Dictionary:
	# Prefer SideBar handler so dimmer + close-sidebar match real UX.
	var bar := _find_named("SideBar")
	if bar != null and bar.has_method("_on_rules_pressed"):
		# Open menu first if sidebar not visible (optional, for recording)
		if bool(_args.get("via_menu", false)):
			var sm := _find_named("SideMenu")
			if sm != null and sm.has_method("do_menu"):
				if bar is CanvasItem and not (bar as CanvasItem).visible:
					sm.call("do_menu")
		bar.call("_on_rules_pressed")
		return _ok({"via": "SideBar._on_rules_pressed"})
	var rules := _rules_panel()
	if rules != null and rules.has_method("_show"):
		rules.call("_show")
		var dim := _menu_dimmer()
		if dim:
			dim.show()
		return _ok({"via": "Rules._show"})
	return _err("rules_not_found")


func _cmd_close_rules(_args: Dictionary) -> Dictionary:
	var rules := _rules_panel()
	if rules == null:
		# Still try to clear dimmer so we never leave a stuck overlay
		var dim0 := _menu_dimmer()
		if dim0:
			dim0.hide()
		return _err("rules_not_found")
	if rules.has_method("_on_close_button_pressed"):
		rules.call("_on_close_button_pressed")
		# Ensure dimmer is gone even if the tween path stalls on web
		var dim := _menu_dimmer()
		if dim and dim.visible:
			# give the real close a frame; if still up, force hide
			dim.hide()
		if rules is CanvasItem:
			(rules as CanvasItem).hide()
		return _ok({"via": "Rules._on_close_button_pressed", "path": str(rules.get_path())})
	# Hard close fallback
	if rules is CanvasItem:
		(rules as CanvasItem).hide()
	var dim2 := _menu_dimmer()
	if dim2:
		dim2.hide()
	return _ok({"via": "Rules.hide_force", "path": str(rules.get_path())})


func _portrait() -> Node:
	return _find_named("Portrait")


func _cmd_bet_plus(args: Dictionary) -> Dictionary:
	var times: int = maxi(1, int(args.get("times", 1)))
	var portrait := _portrait()
	var plus := _find_named("PlusBtn")
	for i in times:
		if portrait != null and portrait.has_method("_on_plus_pressed"):
			portrait.call("_on_plus_pressed")
		elif plus is BaseButton:
			_activate_button(plus as BaseButton)
		else:
			return _err("plus_not_found")
	var helpers := _helpers()
	var bet := 0.0
	if helpers != null and "current_bet" in helpers:
		bet = float(helpers.current_bet)
	return _ok({"times": times, "current_bet": bet})


func _cmd_bet_minus(args: Dictionary) -> Dictionary:
	var times: int = maxi(1, int(args.get("times", 1)))
	var portrait := _portrait()
	for i in times:
		if portrait != null and portrait.has_method("_on_minus_pressed"):
			portrait.call("_on_minus_pressed")
		else:
			return _err("minus_not_found")
	var helpers := _helpers()
	var bet := 0.0
	if helpers != null and "current_bet" in helpers:
		bet = float(helpers.current_bet)
	return _ok({"times": times, "current_bet": bet})


func _cmd_spin(_args: Dictionary) -> Dictionary:
	var portrait := _portrait()
	if portrait != null and portrait.has_method("_on_spin_pressed"):
		portrait.call("_on_spin_pressed")
		return _ok({"via": "portrait._on_spin_pressed"})
	var spin := _find_named("SpinBg")
	if spin is BaseButton:
		_activate_button(spin as BaseButton)
		return _ok({"via": "SpinBg.pressed"})
	return _err("spin_not_found")


# ─── Currency (runtime, no remount) ───────────────────────────────────────────

# Mirrors Template-line Helpers._CURRENCY_DEFAULTS so a bare code fully replaces
# any previous currency (set_currency_from_backend only writes keys present in payload).
const _CURRENCY_DEFAULTS := {
	"BRL": {"symbol": "R$",  "precision": "2", "thousand_sep": ".", "decimal_sep": ","},
	"USD": {"symbol": "$",   "precision": "2", "thousand_sep": ",", "decimal_sep": "."},
	"EUR": {"symbol": "€",   "precision": "2", "thousand_sep": ".", "decimal_sep": ","},
	"GBP": {"symbol": "£",   "precision": "2", "thousand_sep": ",", "decimal_sep": "."},
	"INR": {"symbol": "₹",   "precision": "2", "thousand_sep": ",", "decimal_sep": "."},
	"RUB": {"symbol": "₽",   "precision": "2", "thousand_sep": " ", "decimal_sep": ","},
	"MXN": {"symbol": "MX$", "precision": "2", "thousand_sep": ",", "decimal_sep": "."},
	"ARS": {"symbol": "$",   "precision": "2", "thousand_sep": ".", "decimal_sep": ","},
	"CLP": {"symbol": "$",   "precision": "0", "thousand_sep": ".", "decimal_sep": ","},
	"COP": {"symbol": "$",   "precision": "0", "thousand_sep": ".", "decimal_sep": ","},
	"PEN": {"symbol": "S/",  "precision": "2", "thousand_sep": ",", "decimal_sep": "."},
}


## args keys (all optional except code recommended):
##   code | currency, symbol, format_precision | precision,
##   presentation_multiplier, thousand_sep, decimal_sep
func _cmd_set_currency(args: Dictionary) -> Dictionary:
	var helpers := _helpers()
	if helpers == null:
		return _err("helpers_missing")

	var code := str(args.get("code", args.get("currency", ""))).to_upper()
	if code.is_empty() and "currency_code" in helpers:
		code = str(helpers.currency_code).to_upper()

	var defaults: Dictionary = _CURRENCY_DEFAULTS.get(code, {})

	# Always send a full format so switching USD→BRL does not leave "$" behind.
	var symbol := str(args.get("symbol", defaults.get("symbol", "$")))
	var precision := str(args.get("format_precision", args.get("precision", defaults.get("precision", "2"))))
	var mult := str(args.get("presentation_multiplier", "1"))
	var thousand := str(args.get("thousand_sep", defaults.get("thousand_sep", ",")))
	var decimal := str(args.get("decimal_sep", defaults.get("decimal_sep", ".")))

	var payload := {
		"currency": code,
		"currency_symbol": symbol,
		"currency_format_precision": precision,
		"currency_presentation_multiplier": mult,
		"currency_thousand_sep": thousand,
		"currency_decimal_sep": decimal,
	}

	# Prefer shared API used across Template-line games.
	if helpers.has_method("set_currency_from_backend"):
		helpers.set_currency_from_backend(payload)
	else:
		_apply_currency_fallback(helpers, payload)

	# Force all fields on Helpers + localStorage (full replace).
	if "currency_code" in helpers:
		helpers.currency_code = code
	if "currency_symbol" in helpers:
		helpers.currency_symbol = symbol
	if "currency_format_precision" in helpers:
		helpers.currency_format_precision = precision
	if "currency_presentation_multiplier" in helpers:
		helpers.currency_presentation_multiplier = mult
	if "currency_thousand_sep" in helpers:
		helpers.currency_thousand_sep = thousand
	if "currency_decimal_sep" in helpers:
		helpers.currency_decimal_sep = decimal
	_ls_set("currency_code", code)
	_ls_set("currency_symbol", symbol)
	_ls_set("currency_format_precision", precision)
	_ls_set("currency_presentation_multiplier", mult)
	_ls_set("currency_thousand_sep", thousand)
	_ls_set("currency_decimal_sep", decimal)

	_refresh_currency_ui()
	return _ok(_currency_snapshot(helpers))


func _apply_currency_fallback(helpers: Node, payload: Dictionary) -> void:
	if payload.has("currency") and "currency_code" in helpers:
		helpers.currency_code = str(payload["currency"])
		_ls_set("currency_code", str(payload["currency"]))
	if payload.has("currency_symbol") and "currency_symbol" in helpers:
		helpers.currency_symbol = str(payload["currency_symbol"])
		_ls_set("currency_symbol", str(payload["currency_symbol"]))
	if payload.has("currency_format_precision") and "currency_format_precision" in helpers:
		helpers.currency_format_precision = str(payload["currency_format_precision"])
		_ls_set("currency_format_precision", str(payload["currency_format_precision"]))
	if payload.has("currency_presentation_multiplier") and "currency_presentation_multiplier" in helpers:
		helpers.currency_presentation_multiplier = str(payload["currency_presentation_multiplier"])
		_ls_set("currency_presentation_multiplier", str(payload["currency_presentation_multiplier"]))
	if payload.has("currency_thousand_sep") and "currency_thousand_sep" in helpers:
		helpers.currency_thousand_sep = str(payload["currency_thousand_sep"])
		_ls_set("currency_thousand_sep", str(payload["currency_thousand_sep"]))
	if payload.has("currency_decimal_sep") and "currency_decimal_sep" in helpers:
		helpers.currency_decimal_sep = str(payload["currency_decimal_sep"])
		_ls_set("currency_decimal_sep", str(payload["currency_decimal_sep"]))


func _cmd_reload_config() -> Dictionary:
	var helpers := _helpers()
	if helpers == null:
		return _err("helpers_missing")
	if helpers.has_method("_set_values"):
		helpers._set_values()
	_refresh_currency_ui()
	return _ok(_collect_state())


func _refresh_currency_ui() -> void:
	var scene := get_tree().current_scene
	if scene == null:
		return
	if scene.has_method("update_balance_display"):
		scene.update_balance_display()
	# Walk one level for common layout nodes (Portrait / GameLayout / etc.).
	for child in scene.get_children():
		if child.has_method("update_balance_display"):
			child.update_balance_display()
		for grand in child.get_children():
			if grand.has_method("update_balance_display"):
				grand.update_balance_display()


# ─── State ────────────────────────────────────────────────────────────────────

func _collect_state() -> Dictionary:
	var helpers := _helpers()
	var state := {
		"protocol": PROTOCOL_VERSION,
		"viewport": _viewport_size_dict(),
		"pointer": {"x": _last_pos.x, "y": _last_pos.y},
	}
	if helpers != null:
		state["currency"] = _currency_snapshot(helpers)
		if "balance" in helpers:
			state["balance"] = helpers.balance
		if "current_balance" in helpers:
			state["current_balance"] = helpers.current_balance
		if "current_bet" in helpers:
			state["current_bet"] = helpers.current_bet
		if "bet_min" in helpers:
			state["bet_min"] = helpers.bet_min
		if "bet_max" in helpers:
			state["bet_max"] = helpers.bet_max
		if "language" in helpers:
			state["language"] = helpers.language
		if helpers.has_method("format_currency") and "balance" in helpers:
			state["balance_formatted"] = helpers.format_currency(float(helpers.balance))
			if "current_bet" in helpers:
				state["bet_formatted"] = helpers.format_currency(float(helpers.current_bet))
	# Optional project version from ProjectSettings
	if ProjectSettings.has_setting("application/config/version"):
		state["game_version"] = str(ProjectSettings.get_setting("application/config/version"))
	return state


func _currency_snapshot(helpers: Node) -> Dictionary:
	var snap := {}
	for key in [
		"currency_code", "currency_symbol", "currency_format_precision",
		"currency_presentation_multiplier", "currency_thousand_sep", "currency_decimal_sep"
	]:
		if key in helpers:
			snap[key.replace("currency_", "")] = helpers.get(key)
	# Alias convenience
	if snap.has("code"):
		snap["currency"] = snap["code"]
	return snap


func _viewport_size_dict() -> Dictionary:
	var vp := get_viewport()
	if vp == null:
		return {"w": 0, "h": 0}
	var r := vp.get_visible_rect().size
	return {"w": r.x, "h": r.y}


func _cmd_wait_frames(args: Dictionary) -> Dictionary:
	# Synchronous multi-frame wait is not possible in one handle() call without
	# awaiting; document that clients should use page.waitForTimeout or shell sleeps.
	# We still accept the command and process N frames via await if called from async.
	var n: int = clampi(int(args.get("frames", 1)), 1, 120)
	# Best-effort: yield frames if we can (handle is sync from JS). Just report.
	return _ok({"frames_requested": n, "note": "use client-side delay; events are injected sync"})


# ─── Helpers / IO ─────────────────────────────────────────────────────────────

func _helpers() -> Node:
	return get_node_or_null("/root/Helpers")


func _ok(data: Dictionary = {}) -> Dictionary:
	return {"ok": true, "data": data}


func _err(error: String, data: Dictionary = {}) -> Dictionary:
	return {"ok": false, "error": error, "data": data}


func _ls_set(key: String, value: String) -> void:
	# Escape single quotes for safe eval embedding.
	var safe_key := key.replace("'", "")
	var safe_val := value.replace("\\", "\\\\").replace("'", "\\'")
	JavaScriptBridge.eval("localStorage.setItem('%s', '%s');" % [safe_key, safe_val])


func _announce_ready() -> void:
	if not enabled:
		return
	JavaScriptBridge.eval("window.parent.postMessage({ status: 'auto_ready', protocol: %d }, '*');" % PROTOCOL_VERSION)


func _reply(req_id: String, ok: bool, data: Dictionary, error: String) -> void:
	var payload := {
		"status": "auto_result",
		"id": req_id,
		"ok": ok,
		"data": data,
	}
	if not ok and not error.is_empty():
		payload["error"] = error
	var json := JSON.stringify(payload)
	JavaScriptBridge.eval("window.parent.postMessage(%s, '*');" % json)
