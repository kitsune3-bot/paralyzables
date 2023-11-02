import string
from unicodedata import normalize

from paralyzables.config import MAX_SIMILARITY_DEPTH


def _asciify(char: str) -> str:
    return normalize("NFD", char).encode("ascii", "ignore").decode("ascii")


def _get_accented_characters(char: str) -> list[str]:
    return [
        u for u in (chr(i) for i in range(137928)) if u != char and _asciify(u) == char
    ]


def _get_paralyzables_chars(
    character: str, unicode_confusable_map: dict[str, list[str]], depth: int
) -> set[str]:
    mapped_chars = unicode_confusable_map[character]

    group = set([character])
    if depth <= MAX_SIMILARITY_DEPTH:
        for mapped_char in mapped_chars:
            group.update(
                _get_paralyzables_chars(mapped_char, unicode_confusable_map, depth + 1)
            )
    return group


def parse_new_mapping_file(
    confusables_file: str, case_invariant: bool = False
) -> dict[str, list[str]]:
    unicode_confusable_map = {}

    with open(confusables_file, "r") as unicode_mappings:
        mappings = unicode_mappings.readlines()

        for mapping_line in mappings:
            if (
                not mapping_line.strip()
                or mapping_line[0] == "#"
                or mapping_line[1] == "#"
            ):
                continue

            mapping = mapping_line.split(";")[:2]
            str1 = chr(int(mapping[0].strip(), 16))
            mapping[1] = mapping[1].strip().split(" ")
            mapping[1] = [chr(int(x, 16)) for x in mapping[1]]
            str2 = "".join(mapping[1])

            if unicode_confusable_map.get(str1):
                unicode_confusable_map[str1].add(str2)
            else:
                unicode_confusable_map[str1] = set([str2])

            if unicode_confusable_map.get(str2):
                unicode_confusable_map[str2].add(str1)
            else:
                unicode_confusable_map[str2] = set([str1])

            if case_invariant is True:
                # NOTE: src upper or lower char
                if len(str1) == 1:
                    case_change = str2.swapcase()
                    unicode_confusable_map[str2].add(case_change)
                    if unicode_confusable_map.get(case_change) is not None:
                        unicode_confusable_map[case_change].add(str2)
                    else:
                        unicode_confusable_map[case_change] = {str2}

                # NOTE: tgt upper or lower char
                if len(str2) == 1:
                    case_change = str2.swapcase()
                    unicode_confusable_map[str2].add(case_change)
                    if unicode_confusable_map.get(case_change) is not None:
                        unicode_confusable_map[case_change].add(str2)
                    else:
                        unicode_confusable_map[case_change] = {str2}

    # NOTE: correspond accents
    for char in string.ascii_lowercase:
        accented = _get_accented_characters(char)
        unicode_confusable_map[char].update(accented)
        for accent in accented:
            if unicode_confusable_map.get(accent):
                unicode_confusable_map[accent].add(char)
            else:
                unicode_confusable_map[accent] = set([char])

    for char in string.ascii_uppercase:
        accented = _get_accented_characters(char)
        unicode_confusable_map[char].update(accented)
        for accent in accented:
            if unicode_confusable_map.get(accent):
                unicode_confusable_map[accent].add(char)
            else:
                unicode_confusable_map[accent] = set([char])

    paralyzables_map = dict()

    for character in unicode_confusable_map.keys():
        char_group = _get_paralyzables_chars(character, unicode_confusable_map, 0)

        paralyzables_map[character] = list(char_group)

    return paralyzables_map
