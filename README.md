# ASTROMIND: Biometric Spacecraft Crew Monitor

**Astromind** is a mission-critical, offline AI sensor designed to prevent pilot incapacitation in isolated environments. 

Unlike standard drowsiness detectors, Astromind uses **Multimodal Bio-Fusion**—tracking both the physical symptoms of sleep (Eye Aspect Ratio) and the psychological precursors of fatigue (Yawning/Mouth Aspect Ratio) simultaneously.

## Key Features
* **Zero-Latency Alert System:** 3-Stage escalation from Warning -> Alarm -> Autopilot Trigger.
* **100% Offline Architecture:** Runs locally on Edge Hardware (Raspberry Pi / Jetson) with no internet dependency.
* **Black Box Forensics:** Automatically generates declassified mission reports with a Safety Grade (S, A, F) for post-flight analysis.
* **Privacy by Design:** No video feeds are stored; only mathematical vector data is logged.

## To add an .venv file
1. Open your project folder in VS Code.
2. Press Ctrl + Shift + P on your keyboard to open the Command Palette.
3. Type Python: Create Environment and click it.
4. Select Venv.
5. Select the Python interpreter (usually the one labeled "Recommended" or the highest version number like 3.12.x). [Crucial Step: You will see a list of files. Check the box next to requirements.txt.]
6. Click "OK" or "Create".

## How to Run

1.  **Clone the repository**
    ```bash
    git clone [https://github.com/vi6yav/astromind-app.git](https://github.com/vi6yav/astromind-app.git)
    cd astromind-app
    ```
2.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```
3.  **Initiate System**
    ```bash
    python app.py
    ```

## ⚠️ Disclaimer
This project is a prototype for aerospace applications. While designed for high-accuracy detection, it is currently a demonstration of vision-based biometrics.

