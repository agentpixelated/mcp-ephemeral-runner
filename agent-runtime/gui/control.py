#!/usr/bin/env python3
import json, os, sys, time

try:
    import pyautogui
except Exception as exc:
    print(json.dumps({"ok": False, "error": f"pyautogui unavailable: {exc}"}))
    raise SystemExit(2)

pyautogui.PAUSE = 0.05
pyautogui.FAILSAFE = True

def run(actions):
    results = []
    for i, a in enumerate(actions):
        op = str(a.get("op", ""))
        if op == "move":
            pyautogui.moveTo(int(a["x"]), int(a["y"]), duration=float(a.get("duration", 0.15)))
        elif op == "click":
            pyautogui.click(int(a.get("x", pyautogui.position().x)), int(a.get("y", pyautogui.position().y)), clicks=int(a.get("clicks", 1)), button=str(a.get("button", "left")))
        elif op == "type":
            pyautogui.write(str(a.get("text", "")), interval=float(a.get("interval", 0.01)))
        elif op == "key":
            pyautogui.press(str(a["key"]), presses=int(a.get("presses", 1)), interval=float(a.get("interval", 0.03)))
        elif op == "hotkey":
            keys = a.get("keys") or []
            pyautogui.hotkey(*[str(k) for k in keys])
        elif op == "scroll":
            pyautogui.scroll(int(a.get("clicks", 0)), x=a.get("x"), y=a.get("y"))
        elif op == "sleep":
            time.sleep(float(a.get("seconds", 0.5)))
        elif op == "position":
            p = pyautogui.position(); results.append({"index": i, "position": [p.x, p.y]}); continue
        else:
            raise ValueError(f"unsupported GUI op: {op}")
        results.append({"index": i, "op": op, "ok": True})
    return results

if __name__ == "__main__":
    actions = json.loads(sys.argv[1]) if len(sys.argv) > 1 else json.load(sys.stdin)
    print(json.dumps({"ok": True, "display": os.getenv("DISPLAY"), "results": run(actions)}))
