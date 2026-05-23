# BOT-MACRO — Visual Automation Bot 🤖

**BOT-MACRO** is a professional desktop automation software designed for Android emulators (like LDPlayer and BlueStacks) and standard Windows applications. Moving beyond simple macro recorders, it features a **Drag & Drop Visual Editor** and an intelligent **Computer Vision** system to dynamically handle popups and unexpected UI states.

---

## 🌟 Core Features

*   **🎨 Visual Editor:** Construct macros intuitively by dragging and dropping action blocks (Click, Delay, Vision Scan, Sub-Macro) without writing any code.
*   **🖱️ Smart Recording:** Record your mouse clicks in real-time. Use the **F7** hotkey during recording to insert intelligent "Vision Checkpoints".
*   **👁️ Multi-Asset Vision Scanning:** The bot actively "sees" the screen. It automatically recognizes buttons or images placed in the `assets/` folder (like "X" buttons to close ads or "OK" buttons) and clicks them.
*   **♻️ Layered Popup Handling:** If multiple popups overlap, the bot closes them one by one, refreshing its visual scan after each click to ensure robust execution.
*   **🛡️ Anti-Ban Mechanics:**
    *   **Human-like Movements:** Mouse cursors move using natural, bezier-like acceleration curves instead of instant teleportation.
    *   **Randomization:** Every click includes a random spatial offset (+/- 3px) and randomized execution delays to mimic human behavior and evade detection.
*   **🧩 Modularity (Sub-Macros):** Create smaller, reusable macros and nest them inside larger ones.
*   **📱 Telegram Notifications:** Built-in support to alert you via Telegram if the bot encounters an error or is stopped.

---

## 🚀 Complete Setup Guide (From A to Z)

Follow these step-by-step instructions to get the bot running on your local machine.

### 1. Prerequisites
Ensure you have the following installed:
- [Python 3.10+](https://www.python.org/downloads/) (Make sure to check "Add Python to PATH" during installation).
- [Git](https://git-scm.com/downloads) (To clone the repository).

### 2. Installation
Open your terminal (Command Prompt or PowerShell) and run the following commands:

```bash
# Clone the repository
git clone https://github.com/marcelluxx/BOT-MACRO.git

# Navigate into the project directory
cd BOT-MACRO

# Create a virtual environment to keep dependencies isolated
python -m venv .venv

# Activate the virtual environment
# On Windows:
.venv\Scripts\activate
# (On Mac/Linux, use: source .venv/bin/activate)

# Install required Python packages
pip install -r requirements.txt
```

### 3. Setup Telegram Notifications (Optional but recommended)
If you want the bot to send you updates:
1. Talk to [BotFather](https://t.me/botfather) on Telegram to create a bot and get a **Token**.
2. Find your **Chat ID** (using a bot like @userinfobot).
3. Create a `.env` file in the root directory of the project.
4. Add the following lines to your `.env` file:
   ```env
   TELEGRAM_BOT_TOKEN=your_bot_token_here
   TELEGRAM_CHAT_ID=your_chat_id_here
   ```

### 4. Running the Bot
Launch the graphical interface (GUI) with:
```bash
python main.py
```

---

## 🎮 How to Use the Bot

### 1. Preparing Vision Assets
Place `.png` images of buttons or icons you want the bot to recognize into the `assets/` folder. The bot will automatically scan this folder during a "Vision Scan" action and click any matches it finds on screen.

### 2. Creating a Macro
You can build a macro in two ways:

*   **Manual Method:** Drag blocks from the left **Toolbox** into the center **Timeline**.
*   **Recording Method:**
    1.  Click **⏺ Record** (or press **F8**).
    2.  Perform your clicks inside the emulator/app.
    3.  **IMPORTANT:** If a popup appears, or you want the bot to verify the screen state, press **F7**. This inserts a "Vision Flag".
    4.  Press **F8** again to stop recording.

### 3. Editing your Macro
*   **Reorder:** Drag blocks up and down in the timeline.
*   **Edit:** Click any block to reveal its properties on the right panel (adjust coordinates, delays, or vision matching thresholds).
*   **Sub-Macros:** Drag a saved `.json` macro from the "Saved Actions" section into the timeline to nest it.

### 4. Playback
Press **▶ Play** (or **F9**). The bot will automatically bring the target window (default: "LDPlayer") to the front and begin looping the macro indefinitely.

---

## ⌨️ Global Hotkeys

These shortcuts work globally, even if the bot is running in the background:

| Key | Function |
| :--- | :--- |
| **F7** | **Insert Vision Flag** (Only during recording) |
| **F8** | **Toggle Record** |
| **F9** | **Toggle Playback (Loop)** |
| **ESC / F12** | **EMERGENCY STOP** (Instantly halts all operations) |

---

## ⚙️ Advanced Configuration

If your target emulator or application has a window title other than "LDPlayer":
1. Open `gui/main_window.py` (and `main.py` if using CLI).
2. Locate the constant `WINDOW_TITLE = "LDPlayer"`.
3. Change it to exactly match the title of your target window (e.g., "BlueStacks App Player").

---

## 🛠️ Troubleshooting

*   **The bot clicks the wrong spot:** Ensure your emulator window isn't strangely resized. The bot uses relative coordinates, meaning the internal resolution of the emulator must remain consistent between recording and playback.
*   **Vision Scan doesn't find the buttons:** Check that your `.png` files in `assets/` are cleanly cropped. You can also lower the "Threshold" in the block's properties panel (e.g., set it to `0.7` instead of `0.8`).
*   **Emergency Failsafe:** If the bot goes out of control, violently move your physical mouse to any of the **four corners of your screen**. This triggers the `PyAutoGUI` fail-safe and aborts the script.
