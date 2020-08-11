class Sentence:
    def __init__(self, string, onset, offset, line_number, correct_token):
        self.string = string
        self.onset = onset
        self.offset = offset
        self.line_number = line_number
        self.correct_token = correct_token

    def get_list_of_tokens(self):
        string_before = self.get_substring_before_inc_tok()
        string_after = self.get_substring_after_inc_tok()

        tokens_before = self.get_toks_before_inc_tok(string_before)
        tokens_after = self.get_toks_after_inc_tok(string_after)

        in_tok_list = []
        in_tok_list.append(self.get_incorrect_token())

        split_tokens = tokens_before + in_tok_list + tokens_after

        token_objects_list = []

        for i in range(len(split_tokens)):
            token = split_tokens[i]
            token_objects_list.append(Token(token, i, self.correct_token))

        return token_objects_list

    def get_incorrect_token_index(self):
        token_objects_list = self.get_list_of_tokens()
        indices = [Token.string.find("<") for Token in token_objects_list]
        return indices.index(0)

    def get_incorrect_token(self):
        incorrect_token = self.string[self.string.find("<"): self.string.find(">") + 1]
        return incorrect_token

    def get_substring_before_inc_tok(self):
        return self.string[:self.string.index("<")]

    def get_substring_after_inc_tok(self):
        return self.string[self.string.index(">") + 1:]

    def get_toks_before_inc_tok(self, substring):
        return substring.split()

    def get_toks_after_inc_tok(self, substring):
        return substring.split()

class Token:
    def __init__(self, string, index, correct_token):
        self.string = string
        self.index = index
        self.correct_token = correct_token

    def is_incorrect(self):
        return self.string.find("<") != -1 and self.string.find(">") != -1

    def get_num_of_words(self):
        temp_string = self.string
        temp_string.replace("<", "").replace(">", "")
        return len(temp_string.split())