import time
from PIL import Image, ImageDraw
import pyautogui
import requests

min_pixels = 256*28*28
max_pixels = 1344*28*28

_NAV_SYSTEM = """You are an assistant trained to navigate the {_APP} screen. 
Given a task instruction, a screen observation, and an action history sequence, 
output the next action and wait for the next observation. 
Here is the action space:
{_ACTION_SPACE}
"""

_NAV_FORMAT = """
Format the action as a dictionary with the following keys:
{'action': 'ACTION_TYPE', 'value': 'element', 'position': [x,y]}

If value or position is not applicable, set it as `None`.
Position might be [[x1,y1], [x2,y2]] if the action requires a start and end position.
Position represents the relative coordinates on the screenshot and should be scaled to a range of 0-1.
"""

action_map = {
'web': """
1. `CLICK`: Click on an element, value is not applicable and the position [x,y] is required. 
2. `INPUT`: Type a string into an element, value is a string to type and the position [x,y] is required. 
3. `SELECT`: Select a value for an element, value is not applicable and the position [x,y] is required. 
4. `HOVER`: Hover on an element, value is not applicable and the position [x,y] is required.
5. `ANSWER`: Answer the question, value is the answer and the position is not applicable.
6. `ENTER`: Enter operation, value and position are not applicable.
7. `SCROLL`: Scroll the screen, value is the direction to scroll and the position is not applicable.
8. `SELECT_TEXT`: Select some text content, value is not applicable and position [[x1,y1], [x2,y2]] is the start and end position of the select operation.
9. `COPY`: Copy the text, value is the text to copy and the position is not applicable.
""",

'phone': """
1. `INPUT`: Type a string into an element, value is not applicable and the position [x,y] is required. 
2. `SWIPE`: Swipe the screen, value is not applicable and the position [[x1,y1], [x2,y2]] is the start and end position of the swipe operation.
3. `TAP`: Tap on an element, value is not applicable and the position [x,y] is required.
4. `ANSWER`: Answer the question, value is the status (e.g., 'task complete') and the position is not applicable.
5. `ENTER`: Enter operation, value and position are not applicable.
"""
}


def get_showui_res(messages, url="http://127.0.0.1:8000/generate"):
    res = requests.post(url, json=messages)
    return res.json()["showui_res"]


def screenshot(output_path):
    # 截取屏幕截图
    screenshot = pyautogui.screenshot()
    print(screenshot.size)
    screenshot = screenshot.resize((2560, 1664))
    print(screenshot.size)
    # 保存缩小后的截图
    screenshot.save(output_path)
    print("Screenshot taken successfully, saved at " + output_path)


def pyautogui_map(action, position, value, img_url):
    """
    use pyautogui to perform the action
    :param action:
    :param position:
    :param value:
    :return:
    """
    image = Image.open(img_url)
    width, height = image.size

    x, y = position[0] * width, position[1] * height

    print(f'position: [{x}, {y}]')
    if action == 'CLICK':
        # 移动到指定位置
        pyautogui.moveTo(x, y, duration=1)
        # 等待一秒钟
        time.sleep(1)
        # 点击指定位置
        pyautogui.doubleClick()
    elif action == 'INPUT':
        # 移动到指定位置
        pyautogui.moveTo(x, y, duration=1)
        pyautogui.click(x, y)
        # 等待一秒钟
        time.sleep(1)
        # 输入文本
        pyautogui.write(value)
        pyautogui.press('enter')
    elif action == 'ENTER':
        pyautogui.press('enter')
    else:
        print("Unknown action: " + action)


if __name__ == '__main__':
    split = 'web'
    system_prompt = _NAV_SYSTEM.format(_APP=split, _ACTION_SPACE=action_map[split])
    query = "open google chrome, input weather in beijing"

    img_idx = 1
    img_url = f"./screenshots/screen_{img_idx}.png"

    screenshot(img_url)

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": system_prompt},
                {"type": "text", "text": f'Task: {query}'},
                # {"type": "text", "text": PAST_ACTION},
                {"type": "image", "image": img_url, "min_pixels":
                    min_pixels, "max_pixels": max_pixels}
            ]
        }
    ]

    for i in range(3):
        showui_res = get_showui_res(messages)
        print(showui_res)

        for action in  showui_res:
            action["img_url"] = img_url
            pyautogui_map(**action)
            if len(messages[0]['content']) == 3:
                messages[0]['content'].insert(2, {"type": "text", "text": action['action']})
            else:
                messages[0]['content'][2] = {"type": "text", "text": action['action']}

        img_idx += 1
        img_url = f"./screenshots/screen_{img_idx}.png"
        screenshot(img_url)
        messages[0]["content"][-1] = {"type": "image", "image": img_url,
                                      "min_pixels": min_pixels, "max_pixels": max_pixels}
