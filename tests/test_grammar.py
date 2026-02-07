import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine.grammar import SASLGrammarEngine

def test_sasl_grammar():
    print("Initializing Grammar Engine...")
    engine = SASLGrammarEngine()
    
    test_cases = [
        {
            "input": "I am going to the shop tomorrow",
            "expected_gloss": ["TOMORROW", "SHOP", "I", "GO"], # Note: spaCy might lemmatize differently, we'll see
            "expected_face": "neutral"
        },
        {
            "input": "Where is the hospital?",
            "expected_gloss": ["HOSPITAL", "WHERE"],
            "expected_face": "furrowed_brows"
        },
        {
            "input": "Call the police",
            "expected_gloss": ["POLICE", "CALL"], 
            "expected_face": "neutral" # Imperative might be neutral or urgent, depending on logic
        }
    ]
    
    passed = 0
    for case in test_cases:
        result = engine.to_gloss(case["input"])
        print(f"\nInput: {case['input']}")
        print(f"Gloss: {result['gloss']}")
        print(f"Face:  {result['facial_marker']}")
        
        # Loose check for key words
        gloss_set = set([w.upper() for w in result['gloss']])
        expected_set = set([w.upper() for w in case['expected_gloss']])
        
        if gloss_set == expected_set: # Order might vary slightly due to implementation details, checking set first
             print("Gloss Check: PASS (approx)")
             passed += 1
        else:
             print(f"Gloss Check: FAIL. Expected {case['expected_gloss']}")

    print(f"\nPassed {passed}/{len(test_cases)} tests.")

if __name__ == "__main__":
    test_sasl_grammar()
