import cvzone
import cv2
from cvzone.HandTrackingModule import HandDetector
import numpy as np
import google.generativeai as genai
from PIL import Image
import streamlit as st

st.set_page_config(layout="wide")

col1, col2 = st.columns([3,2])
with col1:
    run = st.checkbox('Run', value=True)
    FRAME_WINDOW = st.image([])

with col2:
    st.title("Answer")
    subject_query = st.text_input("Enter your query (e.g., biology, chemistry, math, English, etc.):", "")
    output_text_area = st.subheader("")

genai.configure(api_key="AIzaSyCX19-eLmBw2xbwSWw6bCHjX-JViAUDP_U")
model = genai.GenerativeModel('gemini-1.5-flash')

# Initialize the webcam to capture video
cap = cv2.VideoCapture(0)
cap.set(3, 1280)
cap.set(4, 720)

# Initialize the HandDetector class with the given parameters
detector = HandDetector(staticMode=False, maxHands=1, modelComplexity=1, detectionCon=0.7, minTrackCon=0.5)

def getHandInfo(img):
    # Find hands in the current frame
    hands, img = detector.findHands(img, draw=False, flipType=True)
    if hands:
        hand = hands[0]  # Get the first hand detected
        lmList = hand["lmList"]  # List of 21 landmarks for the first hand
        fingers = detector.fingersUp(hand)  # Count the number of fingers up
        print(fingers)
        return fingers, lmList
    else:
        return None

def draw(info, prev_pos, canvas):
    fingers, lmList = info
    current_pos = None
    if fingers == [0, 1, 0, 0, 0]:  # Index finger up
        current_pos = lmList[8][0:2]  # Tip of index finger
        if prev_pos is None:
            prev_pos = current_pos
        cv2.line(canvas, current_pos, prev_pos, (255, 0, 255), 10)  # Draw line
    elif fingers == [1, 0, 0, 0, 0]:  # Thumb up
        canvas = np.zeros_like(img)  # Clear canvas when thumb is up
    return current_pos, canvas

def sendToAI(model, canvas, fingers, query):
    if fingers == [1, 1, 1, 1, 0]:  # 4 fingers up as trigger gesture
        if query:
            pil_image = Image.fromarray(canvas)
            response = model.generate_content([query, pil_image])  # Query for any subject
            return response.text
        else:
            return "Please enter a valid query."
    return None

prev_pos = None
canvas = None
image_combined = None
output_text = ""

while True:
    success, img = cap.read()
    img = cv2.flip(img, 1)

    if canvas is None:
        canvas = np.zeros_like(img)

    info = getHandInfo(img)
    if info:
        fingers, lmList = info
        prev_pos, canvas = draw(info, prev_pos, canvas)
        output_text = sendToAI(model, canvas, fingers, subject_query)

    image_combined = cv2.addWeighted(img, 0.7, canvas, 0.3, 0)
    FRAME_WINDOW.image(image_combined, channels="BGR")

    if output_text:
        output_text_area.text(output_text)

    cv2.waitKey(1)
