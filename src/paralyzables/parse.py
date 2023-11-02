import string
from unicodedata import normalize

from paralyzables.config import MAX_SIMILARITY_DEPTH


def _asciify(char: str) -> str:
    return normalize("NFD", char).encode("ascii", "ignore").decode("ascii")


def _get_accented_characters(char: str) -> list[str]:
    return [
        u for u in (chr(i) for i in range(137928)) if u != char and _asciify(u) == char
    ]


# TODO
def _get_paralyzables_chars(character, unicode_paralyzables_map, depth):
    mapped_chars = unicode_paralyzables_map[character]

    group = set([character])
    if depth <= MAX_SIMILARITY_DEPTH:
        for mapped_char in mapped_chars:
            group.update(
                _get_paralyzables_chars(
                    mapped_char, unicode_paralyzables_map, depth + 1
                )
            )
    return group


def parse_new_mapping_file(
    paralyzables_file, case_invariant=False
) -> dict[str, list[str]]:
    unicode_paralyzables_map = {}

    with open(paralyzables_file, "r") as unicode_mappings:
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

            if unicode_paralyzables_map.get(str1):
                unicode_paralyzables_map[str1].add(str2)
            else:
                unicode_paralyzables_map[str1] = set([str2])

            if unicode_paralyzables_map.get(str2):
                unicode_paralyzables_map[str2].add(str1)
            else:
                unicode_paralyzables_map[str2] = set([str1])

            if case_invariant is True:
                # NOTE: src upper or lower char
                if len(str1) == 1:
                    case_change = str1.lower() if str1.isupper() else str1.upper()
                    if case_change != str1:
                        unicode_paralyzables_map[str1].add(case_change)
                        if unicode_paralyzables_map.get(case_change) is not None:
                            unicode_paralyzables_map[case_change].add(str1)
                        else:
                            unicode_paralyzables_map[case_change] = set([str1])

                # NOTE: tgt upper or lower char
                if len(str2) == 1:
                    case_change = str2.lower() if str2.isupper() else str2.upper()
                    if case_change != str2:
                        unicode_paralyzables_map[str2].add(case_change)
                        if unicode_paralyzables_map.get(case_change) is not None:
                            unicode_paralyzables_map[case_change].add(str2)
                        else:
                            unicode_paralyzables_map[case_change] = set([str2])

    # NOTE: correspond accents
    for char in string.ascii_lowercase:
        accented = _get_accented_characters(char)
        unicode_paralyzables_map[char].update(accented)
        for accent in accented:
            if unicode_paralyzables_map.get(accent):
                unicode_paralyzables_map[accent].add(char)
            else:
                unicode_paralyzables_map[accent] = set([char])

    for char in string.ascii_uppercase:
        accented = _get_accented_characters(char)
        unicode_paralyzables_map[char].update(accented)
        for accent in accented:
            if unicode_paralyzables_map.get(accent):
                unicode_paralyzables_map[accent].add(char)
            else:
                unicode_paralyzables_map[accent] = set([char])

    paralyzables_map = dict()

    for character in list(unicode_paralyzables_map.keys()):
        char_group = _get_paralyzables_chars(character, unicode_paralyzables_map, 0)

        paralyzables_map[character] = list(char_group)

    return paralyzables_map
