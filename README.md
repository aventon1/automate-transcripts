Automate corrected transcripts

Author
Amina Venton, aventon@uw.edu
Repository at: https://github.com/aventon1/automate-transcripts

This program takes CLOx annotated erroneous transcriptions for the PNWE research study and generates the corrected transcriptions.


Getting Started

Requirements:
Python 3.8
A command-line interface
Workbook file saved as .XLSX

Arguments (example):
index_row = A
orig_text_transcript_col = B
onset_col = C
offset_col = D
correct_token_col = F

Run generate_corrected_transcripts.py with required arguments
This will create a .CSV file with the corrected transcript

This project is in the beta stage. It may contain a number of known or unknown bugs based on user data. Please submit all questions and issues in the official repository. 
