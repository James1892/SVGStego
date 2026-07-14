import re

from .leb128 import leb_encode
from .constants import EMBED_TAGS
from .capacity import estimate_capacity
from .utils import copy_svg, process_attribute_values


TAG_NAMES_PATTERN = "|".join(
    re.escape(tag_name)
    for tag_name in EMBED_TAGS
)

SUPPORTED_TAG_PATTERN = re.compile(
    rf"<(?P<namespace>[A-Za-z_][\w.-]*:)?"
    rf"(?P<tag>{TAG_NAMES_PATTERN})\b"
    rf"(?P<attributes>(?:[^>\"']|\"[^\"]*\"|'[^']*')*)>",
    re.DOTALL,
)


def convert_message_to_binary(message: str) -> str:
    try:
        bits = ""
        for ch in message:
            bits += format(ord(ch), "08b")
        return bits
    except Exception as error:
        print(f"Error: Failed to convert message to binary. {error}")
        return ""


def _create_attribute_pattern(attribute_name: str) -> re.Pattern[str]:
    return re.compile(
        rf"(?P<before>(?<![\w:.-])"
        rf"{re.escape(attribute_name)}\s*=\s*)"
        rf"(?P<quote>[\"'])"
        rf"(?P<value>.*?)"
        rf"(?P=quote)",
        re.DOTALL,
    )


def embed_bits_in_tag(
    tag_text: str,
    tag_name: str,
    full_binary: str,
    bit_index: int,
) -> tuple[str, int]:
    # Embed bits into the supported attributes of one SVG opening tag.
    for attribute_name in EMBED_TAGS[tag_name]:
        if bit_index >= len(full_binary):
            break

        attribute_pattern = _create_attribute_pattern(attribute_name)
        attribute_match = attribute_pattern.search(tag_text)

        if attribute_match is None:
            continue

        new_value, bit_index = process_attribute_values(
            attribute_match.group("value"),
            full_binary,
            bit_index,
        )

        quote = attribute_match.group("quote")
        new_attribute = (
            attribute_match.group("before")
            + quote
            + new_value
            + quote
        )

        tag_text = (
            tag_text[:attribute_match.start()]
            + new_attribute
            + tag_text[attribute_match.end():]
        )

    return tag_text, bit_index


def embed_bits_in_svg_source(
    svg_source: str,
    full_binary: str,
) -> tuple[str, int]:
    # Embed bits while preserving the SVG's original text formatting.
    bit_index = 0
    output_parts: list[str] = []
    previous_end = 0

    for tag_match in SUPPORTED_TAG_PATTERN.finditer(svg_source):
        output_parts.append(
            svg_source[previous_end:tag_match.start()]
        )

        modified_tag, bit_index = embed_bits_in_tag(
            tag_match.group(0),
            tag_match.group("tag"),
            full_binary,
            bit_index,
        )

        output_parts.append(modified_tag)
        previous_end = tag_match.end()

        if bit_index >= len(full_binary):
            break

    output_parts.append(svg_source[previous_end:])

    return "".join(output_parts), bit_index


def embed_message(file: str, message: str) -> str | None:
    try:
        # Convert message to binary and add the LEB128 length prefix.
        binary_message = convert_message_to_binary(message)
        leb_bits = leb_encode(len(binary_message))
        full_binary = leb_bits + binary_message

        _, fits = estimate_capacity(file, full_binary)
        if not fits:
            print("Error: Message exceeds embedding capacity.")
            return None

        with open(file, "r", encoding="utf-8", newline="") as source_file:
            original_source = source_file.read()

        modified_source, embedded_bits = embed_bits_in_svg_source(
            original_source,
            full_binary,
        )

        if embedded_bits != len(full_binary):
            print(
                "Error: The SVG capacity check passed, but not all bits "
                "could be embedded."
            )
            return None

        output_file = copy_svg(file)
        if output_file is None:
            return None

        with open(output_file, "w", encoding="utf-8", newline="") as target_file:
            target_file.write(modified_source)

        return output_file

    except Exception as error:
        print(f"Error embedding message: {error}")
        return None
