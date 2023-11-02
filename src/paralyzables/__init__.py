import re
from itertools import product

from paralyzables.config import NON_NORMAL_ASCII_CHARS
from paralyzables.parse import parse_new_mapping_file
from paralyzables.utils import is_ascii


class Paralyzables:
    def __init__(self, confusables_file: str, case_invariant: bool = False):
        self._confusables_map = parse_new_mapping_file(confusables_file, case_invariant)

    def is_confusables(self, str1: str, str2: str) -> bool:
        while str1 and str2:
            length1, length2 = 0, 0
            for index in range(len(str1), 0, -1):
                if str1[:index] in self.confusables_characters(str2[0]):
                    length1 = index
                    break
            for index in range(len(str2), 0, -1):
                if str2[:index] in self.confusables_characters(str1[0]):
                    length2 = index
                    break

            if not length1 and not length2:
                return False
            elif not length2 or length1 >= length2:
                str1 = str1[length1:]
                str2 = str2[1:]
            else:
                str1 = str1[1:]
                str2 = str2[length2:]
        return str1 == str2

    def confusables_characters(self, char: str) -> list[str]:
        mapped_chars = self._confusables_map.get(char)
        if mapped_chars:
            return mapped_chars
        if len(char) <= 1:
            return [char]
        return []

    def confusables_regex(
        self, string: str, include_character_padding: bool = False
    ) -> str:
        space_regex = "[\*_~|`\-\.]*" if include_character_padding else ""
        regex = space_regex
        for char in string:
            escaped_chars = [re.escape(c) for c in self.confusables_characters(char)]
            regex += "(?:" + "|".join(escaped_chars) + ")" + space_regex

        return regex

    def normalize(self, string: str, prioritize_alpha: bool = False) -> list[str]:
        normal_forms = set([""])
        for char in string:
            normalized_chars = []
            confusables_chars = self.confusables_characters(char)
            if not is_ascii(char) or not char.isalpha():
                for confusables in confusables_chars:
                    if prioritize_alpha:
                        if (
                            (
                                char.isalpha()
                                and confusables.isalpha()
                                and is_ascii(confusables)
                            )
                            or (not char.isalpha() and is_ascii(confusables))
                        ) and confusables not in NON_NORMAL_ASCII_CHARS:
                            normal = confusables
                            if len(confusables) > 1:
                                normal = self.normalize(confusables)[0]
                            normalized_chars.append(normal)
                    else:
                        if (
                            is_ascii(confusables)
                            and confusables not in NON_NORMAL_ASCII_CHARS
                        ):
                            normal = confusables
                            if len(confusables) > 1:
                                normal = self.normalize(confusables)[0]
                            normalized_chars.append(normal)
            else:
                normalized_chars = [char]

            if len(normalized_chars) == 0:
                normalized_chars = [char]
            normal_forms = set(
                [
                    x[0] + x[1].lower()
                    for x in list(product(normal_forms, normalized_chars))
                ]
            )
        return sorted(list(normal_forms))
