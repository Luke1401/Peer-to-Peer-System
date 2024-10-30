from collections import Counter

def most_frequent_word(word_list):

    # Create a Counter object to count the frequency of each word
    word_counts = Counter(word_list)
    
    # Find the word with the highest frequency
    most_common_word, highest_count = word_counts.most_common(1)[0]
    
    return most_common_word

# Example usage
word_list = ["apple", "banana", "apple", "orange", "banana", "apple", "banana", "banana"]
result = most_frequent_word(word_list)
print(f"The most frequent word is: {result}")



a = int(-123 / 10)
print(a)
