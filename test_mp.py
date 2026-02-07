import mediapipe as mp
print(f"Mediapipe file: {mp.__file__}")
try:
    print(f"Solutions: {mp.solutions}")
    print("Import successful")
except AttributeError as e:
    print(f"Error: {e}")
    print(dir(mp))
