from flask import Flask, request, jsonify
import easyocr
import cv2
import pandas as pd
from thefuzz import process, fuzz
import numpy as np
from PIL import Image
import io
import base64
import os

app = Flask(__name__)

# Initialize the EasyOCR reader and load data once at startup
reader = easyocr.Reader(['en', 'de', 'pt', 'it', 'fr'], gpu=False)
df = pd.read_parquet('cards_description.parquet')
known_codes = df['card_sets'].explode().tolist()

# Visual substitutions dictionary
numbers_to_letters = {
    '0': ['O'], '1': ['I', 'L'], '5': ['S'], '2': ['Z'], '8': ['B'], '3': ['E'], '6': ['G'], '7': ['T'], '9': ['P']
}

letters_to_numbers = {
    'O': ['0'], 'I': ['1'], 'L': ['1'], 'S': ['5'], 'Z': ['2'], 'B': ['8'], 'E': ['3'], 'G': ['6'], 'T': ['7'], 'P': ['9']
}

general_visual_substitutions = {
    '0': ['O'], '1': ['I', 'L'], '5': ['S'], '2': ['Z'], '8': ['B'], '3': ['E'], '6': ['G'], '7': ['T'], '9': ['P'],
    'O': ['0'], 'I': ['1', 'L'], 'S': ['5'], 'Z': ['2'], 'B': ['8'], 'E': ['3'], 'G': ['6'], 'T': ['7'], 'P': ['9'],
    'A': ['4'], 'L': ['1'], 'D': ['0'], 'M': ['N'], 'N': ['M'], 'C': ['G']
    # Add more if needed
}

# Constraint sets
allowed_letters = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ')
allowed_numbers = set('0123456789')
languages = ['EN', 'PT', 'FR', 'DE', 'IT']

def are_letters_capitalized(s):
    return all(c.isupper() for c in s if c.isalpha())

def generate_all_combinations(text):
    all_comb = []
    char_4 = '-'
    if len(text.split(char_4)[0]) == 4:
        if text[0] not in allowed_letters:
            char_0_comb = numbers_to_letters.get(text[0], [text[0]])
        else:
            char_0_comb = [text[0]]
        for char_0 in char_0_comb:
            if text[1] not in allowed_letters:
                char_1_comb = numbers_to_letters.get(text[1], [text[1]])
            else:
                char_1_comb = [text[1]]
            for char_1 in char_1_comb:
                char_2_comb = general_visual_substitutions.get(text[2], []) + [text[2]]
                for char_2 in char_2_comb:
                    char_3_comb = general_visual_substitutions.get(text[3], []) + [text[3]]
                    for char_3 in char_3_comb:
                        for char_5_6 in languages:
                            char_7_comb = general_visual_substitutions.get(text[7], []) + [text[7]]
                            for char_7 in char_7_comb:
                                if text[8] not in allowed_numbers:
                                    char_8_comb = letters_to_numbers.get(text[8], [text[8]])
                                else:
                                    char_8_comb = [text[8]]
                                for char_8 in char_8_comb:
                                    if text[9] not in allowed_numbers:
                                        char_9_comb = letters_to_numbers.get(text[9], [text[9]])
                                    else:
                                        char_9_comb = [text[9]]
                                    for char_9 in char_9_comb:
                                        all_comb.append(char_0+char_1+char_2+char_3+char_4+char_5_6+char_7+char_8+char_9)
    else:
        if text[0] not in allowed_letters:
            char_0_comb = numbers_to_letters.get(text[0], [text[0]])
        else:
            char_0_comb = [text[0]]
        for char_0 in char_0_comb:
            if text[1] not in allowed_letters:
                char_1_comb = numbers_to_letters.get(text[1], [text[1]])
            else:
                char_1_comb = [text[1]]
            for char_1 in char_1_comb:
                char_2_comb = general_visual_substitutions.get(text[2], []) + [text[2]]
                for char_2 in char_2_comb:
                    char_3_comb = general_visual_substitutions.get(text[3], []) + [text[3]]
                    for char_3 in char_3_comb:
                        for char_5_6 in languages:
                            char_7_comb = general_visual_substitutions.get(text[7], []) + [text[7]]
                            for char_7 in char_7_comb:
                                if text[8] not in allowed_numbers:
                                    char_8_comb = letters_to_numbers.get(text[8], [text[8]])
                                else:
                                    char_8_comb = [text[8]]
                                for char_8 in char_8_comb:
                                    all_comb.append(char_0+char_1+char_2+char_3+char_4+char_5_6+char_7+char_8)
    return all_comb

def find_best_match(combinations, known_codes):
    highest_score = 0
    best_match = None
    combination_match = None

    for combination in combinations:
        if combination in known_codes:
            return combination, 100, combination  # Exact match

        match, score = process.extractOne(combination, known_codes, scorer=fuzz.ratio)
        if score > highest_score:
            highest_score = score
            best_match = match
            combination_match = combination

    return best_match, highest_score, combination_match

def find_language(text):
    language_ocr = text[5:7]

    match, score = process.extractOne(language_ocr, languages, scorer=fuzz.ratio)

    return match, score, language_ocr

@app.route('/identify_card', methods=['POST'])
def identify_card():
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400

    image_file = request.files['image']
    if image_file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    # Read the image file
    file_bytes = np.frombuffer(image_file.read(), np.uint8)
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # Use EasyOCR to read text from the image
    results = reader.readtext(image)

    # Initialize variable to store the OCR text
    ocr_text = None

    # Search for the card code pattern
    for (bbox, text, prob) in results:
        if '-' in text and are_letters_capitalized(text):
            ocr_text = text
            break  # Stop after finding the first match

    if not ocr_text:
        return jsonify({'error': 'Card code not found in the image'}), 404

    # Generate all possible variations of the OCR text
    all_combinations = generate_all_combinations(ocr_text)

    # Find the best match in the known codes
    best_match, match_score, combination_match = find_best_match(all_combinations, known_codes)

    if not best_match:
        return jsonify({'error': 'No matching card found'}), 404

    # Optionally, find the language
    language_match, language_score, language_ocr = find_language(ocr_text)

    response = {
        'OCR_Text': ocr_text,
        'Match_Combination': combination_match,
        'Best_Match': best_match,
        'Match_Score': match_score,
        'Language_OCR': language_ocr,
        'Language_Match': language_match,
        'Language_Score': language_score
    }

    return jsonify(response), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=5000, debug=True)

