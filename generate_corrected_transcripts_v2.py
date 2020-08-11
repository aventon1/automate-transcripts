#!/usr/bin/python

"""Generates corrected ASR transcripts from reintegrating corrected tokens into original text"""

import sys
import re
import csv
import os
from itertools import zip_longest

from text import Sentence
import openpyxl


def get_sentence_objects(index_row, orig_text_transcript_col, correct_token_col, onset_col, offset_col):
    """
    Gets excel data and creates Sentence objects for each transcript

    Args:
        index_row (list): A list of indices per each line in the file
        orig_text_transcript_col (list): A list of the original text transcripts
        correct_token_col (list): A list correct tokens
        onset_col (list): A list of onset times for each text
        offset_col (list): A list of offset times for each text

    Returns:
        sentence_dict: A dictionary of index to Sentence objects mappings
    """
    #Dictionary for index=key value=list of Sentence objects at the index
    sentence_dict = {}

    # Iterate through each row of excel data
    for (index, text, onset, offset, correct_token) in zip_longest(index_row, orig_text_transcript_col,
                                                                   onset_col, offset_col, correct_token_col,
                                                                   fillvalue=-1):

        # Get cell values of Cell objects
        ind = index.value
        txt = (text.value)
        on = onset.value
        off = offset.value
        c_token = correct_token.value

        if ind in sentence_dict:
            sentence_dict[ind].append(Sentence(txt, on, off, ind, c_token))

        else:
            sentence_dict[ind] = [Sentence(txt, on, off, ind, c_token)]

    return sentence_dict


def clean_text(corrected_text):
    """
    Cleans the text by removing null characters and extra spaces

    Args:
        corrected_text (str): The corrected transcript ready for post-processing

    Returns:
        corrected_text: String of final corrected transcript
    """
    # Remove null characters
    corrected_text = corrected_text.replace("ø", "")

    # Remove extra spaces, tab, newline
    corrected_text = " ".join(corrected_text.split())

    return corrected_text


def get_corrected_sentences(sentence_objects_list):
    """
    Gets the original transcripts and replaces it with correct tokens

    Args:
        sentence_objects_list (list) : List of Sentence objects

    Returns:
        corrected_sentence: String of the corrected sentence with correct tokens

    """
    # Replace one-incorrect-token sentences with one line and return
    if len(sentence_objects_list) == 1:
        sentence = sentence_objects_list[0]
        corrected_sentence = re.sub(r"\<.*?\>", sentence.correct_token, sentence.string)
        return corrected_sentence

    # Stack to hold sentences as they are built
    new_sent_stack = []

    # Get each index for incorrect tokens in sentence
    incorrect_token_indices = [Sentence.get_incorrect_token_index() for Sentence in sentence_objects_list]

    # Iterate through sentence tokens, find correct tokens and replace
    for i in range(len(sentence_objects_list)):

        # Get Sentence object
        sentence_object = sentence_objects_list[i]

        # Get list of tokens in the sentence
        sentence_tok = sentence_object.get_list_of_tokens()

        # Get index of token to replace
        index = incorrect_token_indices[i]

        # Replace with correct token
        correct_tok = sentence_object.correct_token

        sentence_tok[index] = correct_tok

        # If first sentence, concatenate correct tokens and corrected token into string, add to stack
        if i == 0:
            new_sentence = sentence_object.get_substring_before_inc_tok() + correct_tok

            new_sent_stack.append(new_sentence)

        # If not the first sentence
        else:
            # Calculate if last incorrect token was more than one word
            last_index = incorrect_token_indices[i - 1]
            # Get previous incorrect sentence token
            prev_sent_tok = sentence_objects_list[i - 1].get_list_of_tokens()[last_index]
            # Get number of words in the incorrect token
            num_tokens = prev_sent_tok.get_num_of_words()

            words_to_add = 0
            multi_word_token = num_tokens > 1
            extra_words_in_token = 0

            # Calculate how many tokens to concatenate to sentence until the corrected token
            if multi_word_token:
                extra_words_in_token = num_tokens - 1
                words_to_add = index - last_index - extra_words_in_token - 1
            else:
                words_to_add = index - last_index - 1

            # Get tokens from the last corrected token
            for w in range(1, words_to_add + 1):

                if multi_word_token:
                    missing_token = sentence_tok[last_index + extra_words_in_token + w]
                else:
                    missing_token = sentence_tok[last_index + w]

                # Get sentence from stack
                old_sentence = new_sent_stack.pop()

                # Concatenate tokens
                new_sentence = old_sentence + " " + missing_token.string

                # Add back to stack
                new_sent_stack.append(new_sentence)

            # Add the corrected token to the end of sentence and add to stack
            old_sentence = new_sent_stack.pop()
            new_sentence = old_sentence + " " + sentence_object.correct_token
            new_sent_stack.append(new_sentence)

            # If at last incorrect token in sentence
            if i == len(sentence_objects_list) - 1:

                # If not last token in the sentence (end)
                if index != len(sentence_objects_list) - 1:
                    # Get remaining tokens
                    old_sentence = new_sent_stack.pop()
                    new_sentence = old_sentence + sentence_object.get_substring_after_inc_tok()
                    new_sent_stack.append(new_sentence)

    # Get the corrected sentence from only item in the stack
    corrected_sentence = new_sent_stack.pop()

    return corrected_sentence


def get_output(sent_dictionary):
    """
    Gets the index, corrected transcripts, offset, onset and puts in a list

    Args:
        sent_dictionary (dict): A mapping of sentence index to Sentence object

    Returns:
        output_rows: A nested list of the corrected transcripts
    """

    output_rows = []

    for key, value in sorted(sent_dictionary.items()):

        # Get list at sentence index
        sentence_list = value

        # Flag to check if the sentence needs to be corrected
        correct_sentence = False

        if len(sentence_list) == 1:
            corrected_token = sentence_list[0].correct_token
            if corrected_token is None:
                correct_sentence = True

        sentence = sentence_list[0]
        if correct_sentence:
            output_rows.append([sentence.line_number, sentence.string, sentence.onset, sentence.offset])
        else:
            corrected_sentence = get_corrected_sentences(sentence_list)
            output_rows.append([sentence.line_number, clean_text(corrected_sentence), sentence.onset, sentence.offset])

    return output_rows


if __name__ == "__main__":
    input_file = sys.argv[1]

    # Open existing workbook file
    excel_workbook = openpyxl.load_workbook(input_file)

    # Get the worksheet in the workbook
    sheet = excel_workbook.active

    # Get lists of column Cell objects for index, text, correct tokens, onset, and offset
    index_row = (list(sheet[sys.argv[2]]))
    orig_text_transcript_col = list(sheet[sys.argv[3]])
    onset_col = list(sheet[sys.argv[4]])
    offset_col = list(sheet[sys.argv[5]])
    correct_token_col = list(sheet[sys.argv[6]])

    # Remove headers of each column
    index_row.pop(0)
    orig_text_transcript_col.pop(0)
    correct_token_col.pop(0)
    onset_col.pop(0)
    offset_col.pop(0)

    # Get dictionary of index to Sentence objects
    sent_dictionary = get_sentence_objects(index_row, orig_text_transcript_col, correct_token_col, onset_col,
                                           offset_col)

    # Replace text with corrected tokens and get output
    output_rows = get_output(sent_dictionary)

    # Write output to csv file
    output_file = "{}-Corrected-Transcript-v2.csv".format(os.path.splitext(input_file)[0])
    with open(output_file, "w", newline="") as csvfile:
        # Create a csv writer object
        csvwriter = csv.writer(csvfile)

        # Write fields
        fields = ["Index", "Text", "Onset", "Offset"]
        csvwriter.writerow(fields)

        # Write data rows
        csvwriter.writerows(output_rows)