try:
    import mediapipe.python.solutions as solutions
    print("Explicit import successful")
    print(solutions.hands)
except ImportError as e:
    print(f"ImportError: {e}")
except AttributeError as e:
    print(f"AttributeError: {e}")

try:
    from mediapipe import solutions
    print("From import successful")
except ImportError as e:
    print(f"From ImportError: {e}")
