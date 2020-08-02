import sys
import re
import csv
from itertools import zip_longest
from collections import Counter

import openpyxl


def get_multi_ind(index_row):
    """
    Gets the indices of multiple lines of corrections

    Args:
        index_row (list): A list of indices per each line in the file

    Returns:
        multiple_text_indices: A list of indices that take up multiple lines
    """
    index_list = [index.value for index in index_row]

    # Count each index occurrence
    count = Counter(index_list)

    # Get and add indices with multiple lines of text to list
    multiple_text_indices = [i for i, j in count.items() if j > 1]

    return multiple_text_indices


def get_corr_tokens(index_row, correct_token_col):
    """
    Maps each index to correct tokens

    Args:
        index_row (list): A list of indices per each line in the file
        correct_token_col (list): A list correct tokens

    Returns:
        correct_tokens: A dictionary of index to correct tokens
    """
    # Dictionary of corrected tokens at index
    correct_tokens = {}

    # Iterate through correct token column and add indices and tokens to dictionary
    for (index, correct_token) in zip_longest(index_row, correct_token_col, fillvalue=-1):
        ind = index.value
        corr = correct_token.value

        if corr is not None:

            if ind not in correct_tokens:
                correct_tokens[ind] = []

            correct_tokens[ind].append(corr)

    return correct_tokens


def clean_text(corrected_text):
    """
    Cleans the text by removing null characters and extra spaces

    Args:
        corrected_text (str): The corrected text ready for post-processing

    Returns:
        corrected_text: String of final corrected text
    """
    # Remove null characters
    corrected_text = corrected_text.replace("ø", "")

    # Remove extra spaces, tab, newline
    corrected_text = " ".join(corrected_text.split())

    return corrected_text


def replace_text(index_row, orig_text_transcript_col, correct_token_col, onset_col, offset_col):
    """
    Gets original texts and replaces it with correct tokens

    Args:
        index_row (list): A list of indices per each line in the file
        orig_text_transcript_col (list): A list of the original text transcripts
        correct_token_col (list): A list correct tokens
        onset_col (list): A list of onset times for each text
        offset_col (list): A list of offset times for each text

    Returns:
        output_rows: A nested list of the corrected transcripts
    """
    # Get dictionary of corrected tokens at index
    correct_tokens = get_corr_tokens(index_row, correct_token_col)

    # Get the indices of multiple lines of corrections
    multiple_text_indices = get_multi_ind(index_row)

    # Set to keep track of processed multiple line indices
    multiple_text_indices_set = set()

    # List to add index of corrected text, onset, offset
    output_rows = []

    # Iterate through each row
    for (index, text, onset, offset) in zip_longest(index_row, orig_text_transcript_col,
                                                    onset_col, offset_col,
                                                    fillvalue=-1):
        # Get cell values of Cell objects
        ind = index.value
        txt = (text.value)
        on = onset.value
        off = offset.value

        # Transcript text is correct, add to list of output
        if ind not in correct_tokens.keys():
            output_rows.append([ind, txt, on, off])
            # print("{} {} {} {}".format(ind, txt, on, off))

        # Get corrected transcript text
        else:

            # Skip if indices with multiple lines already processed
            if ind in multiple_text_indices_set:
                continue

            # Process indices with single line
            elif ind not in multiple_text_indices:

                # Find and replace text with correct tokens
                corrected_text = re.sub(r"\<.*?\>", correct_tokens[ind][-1], txt)

                # Clean up the text
                corrected_text = clean_text(corrected_text)

                # Add to list of output
                output_rows.append([ind, corrected_text, on, off])
                # print("{} {} {} {}".format(ind, corrected_text, on, off))

            # Process indices with multiple lines
            else:

                # Find all erroneous tokens and replace text with correct tokens
                erroneous_tokens = re.findall("\<.*?\>", txt)

                corrected_text = txt
                for i, token in enumerate(correct_tokens[ind]):
                    err_tok = erroneous_tokens[i]
                    corrected_text = corrected_text.replace(err_tok, token)

                # Add processed index to set of processed indices for multiple text
                multiple_text_indices_set.add(ind)

                # Clean up the text
                corrected_text = clean_text(corrected_text)

                # Add to list of output
                output_rows.append([ind, corrected_text, on, off])
                # print("{} {} {} {}".format(ind, corrected_text, on, off))

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

    # Replace text with corrected tokens
    output_rows = replace_text(index_row, orig_text_transcript_col, correct_token_col, onset_col, offset_col)

    # Write output to csv file
    output_file = "{}-Corrected-Transcript.csv".format(input_file)
    with open(output_file, "w", newline="") as csvfile:
        # Create a csv writer object
        csvwriter = csv.writer(csvfile)

        # Write fields
        fields = ["Index", "Text", "Onset", "Offset"]
        csvwriter.writerow(fields)

        # Write data rows
        csvwriter.writerows(output_rows)