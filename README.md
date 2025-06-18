# Design and Development of a Communications Protocol for Pehuensat III

Welcome to the repository for my thesis project: **Design and Development of a Communications Protocol for the Pehuensat III picosatellite**, which is part of the ongoing space program at the Universidad Nacional del Comahue in Neuquén, Argentina.

This thesis project is being conducted to fulfill the requirements for the Electronic Engineering degree at the Faculty of Engineering, Universidad Nacional del Comahue.

Here, I will be sharing the project's code, as well as the final thesis document once it's complete, to document both the process and the outcomes.

Stay tuned for updates!

## 🧪 Setup: Installing MicroPico (Pico-W-Go) for VS Code

This project uses the **MicroPico Visual Studio Code Extension** (aka Pico-W-Go) to write, upload, and run MicroPython code on a Raspberry Pi Pico or Pico W.

> ✅ This extension makes it easy to manage files, run code, and access the REPL directly from VS Code.

---

### 🛠️ Prerequisites

- [Visual Studio Code](https://code.visualstudio.com/)
- Python 3.x installed on your system
- Raspberry Pi Pico or Pico W with MicroPython firmware installed 

### 🔄 Flashing MicroPython Firmware (if needed)

If your Pico doesn’t have MicroPython installed:

1. Download the latest `.uf2` firmware from:  
   https://micropython.org/download/rp2-pico/

2. Hold down the **BOOTSEL** button on your Pico and plug it into your computer via USB.
3. A USB drive will appear. Drag and drop the `.uf2` file into it.
4. The Pico will reboot and be ready to use.

---

### 🔌 Installing the Extension

1. Open **Visual Studio Code**
2. Go to the **Extensions Panel** (or press `Ctrl+Shift+X`)
3. Search for:  
   **`MicroPico`**
4. Install the one titled:  
   **`MicroPico`**  
   Author: `paulober`


---

### ⚙️ Extension Configuration

Once installed, configure the extension by:

1. Clicking the gear icon ⚙️ → **Extension Settings** for MicroPico.
2. Set the **Device Path**:
   - Windows: `COM3`, `COM4`, etc.
   - macOS/Linux: `/dev/ttyACM0`, `/dev/ttyUSB0`, etc.
3. Set the **Main File** if needed (e.g., `main.py`)
4. Set folders to sync (optional).

---
### ⚙️ Initialize the Project

1. Open the folder where your MicroPython project is located.
2. Open the **Command Palette** (`Ctrl+Shift+P` or `Cmd+Shift+P` on macOS)
3. Run:  
   **`MicroPico: Initialize MicroPico Project`**

> This step imports stub files for autocompletion and sets up the project-specific settings in `.vscode/`.

4. Follow any prompts to install recommended extensions (for autocompletion to work properly).

---

### 💡 Test Your Pico with a Simple Program

Create a new Python file (e.g., `blink.py`) and paste this:

```python
from machine import Pin
from utime import sleep

pin = Pin("LED", Pin.OUT)

print("LED starts flashing...")
while True:
    try:
        pin.toggle()
        sleep(1)  # sleep 1 sec
    except KeyboardInterrupt:
        break

pin.off()
print("Finished.")
```

---
To run it:

- Click the ▶️ **Run** button in the VS Code status bar  
  **or**

- Open the Command Palette (`Ctrl+Shift+P`) and run:  **`MicroPico: Run current file on Pico`** or you can right-click on the file and search for the option


To stop execution:

- Click the 🟥 **Stop** button in the status bar  
**or**

- Open the **Command Palette** and run: **`MicroPico: Stop execution from the command palette`**


### 🧯 Troubleshooting

- ⚠️ Make sure you are using a **data-capable USB cable** (not just charging) ⚠️
- Use the command palette (`Ctrl+Shift+P`) and type `Pico` to access common commands.
- If the port isn't detected:
  - Try unplugging and reconnecting the board
  - On Windows, check the port in Device Manager

---

### 📁 Project Notes

Make sure your `main.py` and any modules (e.g., `sx1278.py`, `ax25.py`) are in the root folder so the extension can sync them properly.

---