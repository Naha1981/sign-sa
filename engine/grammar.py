import spacy

class SASLGrammarEngine:
    def __init__(self):
        try:
            self.nlp = spacy.load("en_core_web_sm")
        except OSError:
            print("Downloading spacy model...")
            from spacy.cli import download
            download("en_core_web_sm")
            self.nlp = spacy.load("en_core_web_sm")

    def to_gloss(self, sentence):
        """
        Converts English sentence to SASL Gloss (Time + Topic + Comment).
        
        Rules:
        1. Time words come first.
        2. WH-Questions: WH-word moves to the end.
        3. Remove noise words (is, am, the, a).
        4. Verbs are uninflected (GO not WENT).
        """
        doc = self.nlp(sentence)
        tokens = [token for token in doc]
        
        # 1. Identify and extract Time words
        time_words = []
        other_tokens = []
        for token in tokens:
            if token.ent_type_ == "DATE" or token.ent_type_ == "TIME":
                time_words.append(token.lemma_.upper())
            else:
                other_tokens.append(token)
        
        # 2. Check for WH-Question and move to end
        wh_words = ['who', 'what', 'where', 'when', 'why', 'how']
        wh_token = None
        current_tokens = []
        
        for token in other_tokens:
            if token.text.lower() in wh_words:
                wh_token = token
            else:
                current_tokens.append(token)
        
        # 3. Filter noise words and get lemmas
        # NOISE: is, am, are, was, were, the, a, an
        noise_words = ['be', 'the', 'a', 'an']
        meaningful_tokens = []
        for token in current_tokens:
            if token.lemma_.lower() not in noise_words and not token.is_punct:
                meaningful_tokens.append(token.lemma_.upper())
        
        # Construct Gloss
        gloss = time_words + meaningful_tokens
        
        # Append WH-word if it exists
        if wh_token:
            gloss.append(wh_token.lemma_.upper())
            facial_marker = "furrowed_brows"
        else:
            # Check if it's a yes/no question (starts with verb usually, but simplified here)
            if sentence.strip().endswith('?'):
                 facial_marker = "raised_brows"
            else:
                 facial_marker = "neutral"
            
        return {
            "gloss": gloss,
            "facial_marker": facial_marker
        }

if __name__ == "__main__":
    engine = SASLGrammarEngine()
    test_sentences = [
        "I am going to the shop tomorrow",
        "Where is the hospital?",
        "Call the police.",
        "I need a doctor."
    ]
    
    for s in test_sentences:
        result = engine.to_gloss(s)
        print(f"Input: {s}")
        print(f"Gloss: {result['gloss']}")
        print(f"Face:  {result['facial_marker']}")
        print("-" * 20)
