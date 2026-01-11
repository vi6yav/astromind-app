import cv2
import mediapipe as mp
import math
import time
import datetime
import winsound  # Windows Sound System
import numpy as np
import csv

# ==========================================
#        ASTROMIND: MISSION CONFIG
# ==========================================
# Thresholds (Tune these for sensitivity)
EAR_THRESHOLD = 0.20    # Eye Aspect Ratio < 0.20 = Sleeping
MAR_THRESHOLD = 0.40    # Mouth Aspect Ratio > 0.40 = Yawning
MICROSLEEP_LIMIT = 15   # Frames before alarm triggers (approx 0.5s)
EMERGENCY_LIMIT = 100   # Frames before Autopilot triggers (approx 3.5s)

# Colors (BGR Format)
CYAN = (255, 255, 0)
NEON_GREEN = (50, 255, 50)
RED = (0, 0, 255)
ORANGE = (0, 165, 255)
DARK_GREY = (50, 50, 50)

# ==========================================
#        SYSTEM INITIALIZATION
# ==========================================
print("[SYSTEM] INITIALIZING SENSORS...")
mp_face_mesh = mp.solutions.face_mesh
mp_drawing = mp.solutions.drawing_utils

# Initialize AI Model
face_mesh = mp_face_mesh.FaceMesh(
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Initialize Camera
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

# Mission Stats Variables
start_time = datetime.datetime.now()
drowsy_counter = 0
yawn_counter = 0
total_microsleeps = 0
total_yawns = 0
ear_history = []
mar_history = []
mission_grade = "A"

# CSV "Black Box" Logger
log_filename = f"mission_log_{start_time.strftime('%Y%m%d_%H%M%S')}.csv"
log_file = open(log_filename, mode='w', newline='')
log_writer = csv.writer(log_file)
log_writer.writerow(["Timestamp", "EAR", "MAR", "Status", "HeartRate_Sim"])

# Helper Math Function
def calculate_distance(p1, p2):
    return math.sqrt((p1.x - p2.x)**2 + (p1.y - p2.y)**2)

print("[SYSTEM] ASTROMIND ONLINE. PRESS 'Q' TO END MISSION.")

# ==========================================
#          MAIN MISSION LOOP
# ==========================================
while cap.isOpened():
    success, image = cap.read()
    if not success:
        continue

    # Flip image for "Mirror" view
    image = cv2.flip(image, 1)
    h, w, _ = image.shape
    overlay = image.copy() # For transparent HUD

    # Process AI Mesh
    image.flags.writeable = False
    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb_image)
    image.flags.writeable = True

    # Default Status
    status_text = "SYSTEM: ONLINE"
    status_color = CYAN
    ear = 0.0
    mar = 0.0

    if results.multi_face_landmarks:
        for face_landmarks in results.multi_face_landmarks:
            lm = face_landmarks.landmark

            # --- 1. BIOMETRIC CALCULATIONS ---
            # Eye Aspect Ratio (Left Eye)
            # Vertical points: 159-145, Horizontal: 33-133
            left_eye_v = calculate_distance(lm[159], lm[145])
            left_eye_h = calculate_distance(lm[33], lm[133])
            ear = left_eye_v / left_eye_h
            ear_history.append(ear)

            # Mouth Aspect Ratio (Yawning)
            # Vertical: 13-14, Horizontal: 78-308
            mouth_v = calculate_distance(lm[13], lm[14])
            mouth_h = calculate_distance(lm[78], lm[308])
            mar = mouth_v / mouth_h
            mar_history.append(mar)

            # --- 2. DRAW MESH (Tactical Wireframe) ---
            mp_drawing.draw_landmarks(
                image=image,
                landmark_list=face_landmarks,
                connections=mp_face_mesh.FACEMESH_TESSELATION,
                landmark_drawing_spec=None,
                connection_drawing_spec=mp_drawing.DrawingSpec(color=(0, 255, 255), thickness=1, circle_radius=0)
            )

            # --- 3. SAFETY LOGIC & ESCALATION ---
            
            # Check Eyes (Drowsiness)
            if ear < EAR_THRESHOLD:
                drowsy_counter += 1
            else:
                drowsy_counter = 0 # Reset if eyes open

            # Check Mouth (Yawning)
            if mar > MAR_THRESHOLD:
                yawn_counter += 1
            else:
                yawn_counter = 0
            
            # Count Events (Only once per trigger)
            if drowsy_counter == MICROSLEEP_LIMIT: total_microsleeps += 1
            if yawn_counter == 15: total_yawns += 1

            # --- ALARM STAGES ---
            # STAGE 0: Praise (Good Focus)
            if ear > 0.25 and mar < 0.2 and drowsy_counter == 0:
                 if int(time.time()) % 20 == 0: # Flash every 20s
                     status_text = "PILOT FOCUS: EXCELLENT"
                     status_color = NEON_GREEN

            # STAGE 1: Caution (Yellow)
            if drowsy_counter > 5 and drowsy_counter < MICROSLEEP_LIMIT:
                status_text = "CAUTION: EYES CLOSING"
                status_color = ORANGE

            # STAGE 2: Critical Alarm (Red)
            elif drowsy_counter >= MICROSLEEP_LIMIT and drowsy_counter < EMERGENCY_LIMIT:
                status_text = "CRITICAL: WAKE UP!"
                status_color = RED
                # Non-blocking beep trick (short duration)
                if drowsy_counter % 5 == 0: winsound.Beep(1000, 100)

            # STAGE 3: Emergency Autopilot (Dead Man's Switch)
            elif drowsy_counter >= EMERGENCY_LIMIT:
                status_text = "!!! AUTOPILOT ENGAGED !!!"
                status_color = NEON_GREEN
                # Simulation of taking control
                cv2.putText(image, "PILOT UNRESPONSIVE", (w//2 - 250, h//2), 
                            cv2.FONT_HERSHEY_SIMPLEX, 1.5, RED, 3)
                if drowsy_counter % 30 == 0: winsound.Beep(2000, 500)

            # Yawn Warning
            if yawn_counter > 10 and drowsy_counter < MICROSLEEP_LIMIT:
                status_text = "FATIGUE DETECTED (YAWN)"
                status_color = ORANGE

            # --- 4. DATA LOGGING (Black Box) ---
            # Save data every 10 frames
            bpm = 70 + (int(time.time() * 2) % 15) # Simulated Heart Rate
            if int(time.time() * 10) % 10 == 0:
                log_writer.writerow([datetime.datetime.now(), f"{ear:.3f}", f"{mar:.3f}", status_text, bpm])

    # ==========================================
    #            UI RENDER (THE HUD)
    # ==========================================
    # 1. Semi-Transparent Panels
    cv2.rectangle(overlay, (10, 10), (320, 160), DARK_GREY, -1)     # Top Left
    cv2.rectangle(overlay, (w-280, 10), (w-10, 200), DARK_GREY, -1) # Top Right
    cv2.rectangle(overlay, (0, h-40), (w, h), (0, 0, 0), -1)        # Bottom Bar
    
    # Apply Transparency
    cv2.addWeighted(overlay, 0.6, image, 0.4, 0, image)

    # 2. Left Panel (System Status)
    cv2.putText(image, status_text, (20, 50), cv2.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2)
    cv2.putText(image, f"FATIGUE EVENTS: {total_microsleeps}", (20, 90), cv2.FONT_HERSHEY_PLAIN, 1.2, (200,200,200), 1)
    cv2.putText(image, f"YAWN COUNT:     {total_yawns}", (20, 120), cv2.FONT_HERSHEY_PLAIN, 1.2, (200,200,200), 1)

    # 3. Right Panel (Biometrics)
    cv2.putText(image, "BIO-TELEMETRY", (w-260, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.5, CYAN, 1)
    cv2.putText(image, f"EYE OPEN: {ear:.2f}", (w-260, 80), cv2.FONT_HERSHEY_PLAIN, 1.5, NEON_GREEN if ear > EAR_THRESHOLD else RED, 1)
    cv2.putText(image, f"MOUTH:    {mar:.2f}", (w-260, 110), cv2.FONT_HERSHEY_PLAIN, 1.5, NEON_GREEN if mar < MAR_THRESHOLD else ORANGE, 1)
    cv2.putText(image, f"HR:       {bpm} BPM", (w-260, 150), cv2.FONT_HERSHEY_PLAIN, 1.5, RED, 1)

    # 4. Footer (Mission Time)
    duration = str(datetime.datetime.now() - start_time).split('.')[0]
    cv2.putText(image, f"MISSION TIME: {duration} | ASTROMIND SENSOR V2.0", (20, h-12), cv2.FONT_HERSHEY_PLAIN, 1, CYAN, 1)

    cv2.imshow('Astromind v2.0 - Biometric Sensor', image)

    # --- QUIT & GENERATE REPORT ---
    key = cv2.waitKey(5) & 0xFF
    if key == ord('q'):
        # Calculate Final Stats
        end_time = datetime.datetime.now()
        duration = end_time - start_time
        avg_ear = sum(ear_history) / len(ear_history) if ear_history else 0
        
        # Grading Logic
        if total_microsleeps == 0 and total_yawns < 2: mission_grade = "S (PERFECT)"
        elif total_microsleeps < 3: mission_grade = "A (SAFE)"
        elif total_microsleeps < 6: mission_grade = "C (CAUTION)"
        else: mission_grade = "F (DANGEROUS)"

        # Write Report
        report_name = f"Mission_Report_{end_time.strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_name, "w") as f:
            f.write("==================================================\n")
            f.write("      ASTROMIND: FLIGHT RECORDER LOG (SECURE)     \n")
            f.write("==================================================\n")
            f.write(f"DATE:         {end_time.strftime('%Y-%m-%d')}\n")
            f.write(f"DURATION:     {str(duration).split('.')[0]}\n")
            f.write(f"FINAL GRADE:  {mission_grade}\n")
            f.write("--------------------------------------------------\n")
            f.write(f"TOTAL MICROSLEEPS: {total_microsleeps}\n")
            f.write(f"TOTAL YAWNS:       {total_yawns}\n")
            f.write(f"AVG EYE OPENNESS:  {avg_ear:.3f}\n")
            f.write("==================================================\n")
        
        print(f"\n[MISSION COMPLETE] Log saved to {log_filename}")
        print(f"[MISSION COMPLETE] Report saved to {report_name}")
        break

# Cleanup
cap.release()
log_file.close()
cv2.destroyAllWindows()