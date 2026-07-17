# number_to_words.py - Utility to convert monetary amounts to Indian English words
from num2words import num2words

def convert_number_to_words(amount: int) -> str:
    """
    Converts an integer amount into Indian English currency word format.
    E.g., 48241 -> "Rupees Forty-Eight Thousand Two Hundred and Forty-One Only"
    """
    if amount == 0:
        return "Rupees Zero Only"
        
    try:
        # Convert using Indian English localization
        words = num2words(amount, lang='en_IN')
        
        # Capitalize each word for neat layout
        words_capitalized = words.title()
        
        # Format as standard Indian Rupees text
        return f"Rupees {words_capitalized} Only"
    except Exception:
        # Fallback if num2words fails
        return f"Rupees {amount} Only"
        
if __name__ == "__main__":
    print(convert_number_to_words(48241))
    print(convert_number_to_words(100000))
