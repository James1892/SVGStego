import re
import xml.etree.ElementTree as ET

from .leb128 import leb_encode
from .constants import EMBED_TAGS
from .capacity import estimate_capacity
from .utils import remove_namespace, copy_svg, process_attribute_values 


def convert_message_to_binary(message: str) -> str:
    try:
        bits = ""
        for ch in message:
            code_point = ord(ch)
            byte_str = format(code_point, "08b")
            bits = bits + byte_str
        return bits
    except Exception as error:
        print(f"Error: Failed to convert message to binary. {error}")
        return ""


def embed_message(file: str, message: str) -> str | None:
    try:
        binary_message = convert_message_to_binary(message)

        leb_bits = leb_encode(len(binary_message))
        full_binary = leb_bits + binary_message

        capacity_chars, fits = estimate_capacity(file, full_binary)
        if not fits:
            print("Error: Message exceeds embedding capacity.")
            return None

        output_file = copy_svg(file)
        if output_file is None:
            return None

        tree = ET.parse(output_file)

        for elem in tree.iter():
            tag_without_ns = remove_namespace(elem.tag)
            elem.tag = tag_without_ns

        root = tree.getroot()
        bit_index = 0

        for elem in root.iter():
            tag = elem.tag
            if tag in EMBED_TAGS:
                for attr in EMBED_TAGS[tag]:
                    if attr in elem.attrib:
                        original_attr = elem.attrib[attr]
                        new_attr, next_bit_index = process_attribute_values(
                            original_attr,
                            full_binary,
                            bit_index
                        )
                        elem.set(attr, new_attr)
                        bit_index = next_bit_index

                        if bit_index >= len(full_binary):
                            break

                if bit_index >= len(full_binary):
                    break

        original_svg_tag = None
        with open(file, "r", encoding="utf-8") as f:
            for line in f:
                if "<svg" in line:
                    original_svg_tag = line
                    break

        if original_svg_tag is None:
            print("Error: Could not find <svg> tag in original file.")
            return None

        modified_svg_str = ET.tostring(root, encoding="unicode", method="xml")

        modified_svg_str = re.sub(r"\s+/>", "/>", modified_svg_str)

        svg_start = modified_svg_str.find(">")
        if svg_start == -1:
            print("Error: Malformed SVG output.")
            return None

        modified_svg_body = modified_svg_str[svg_start + 1 :]

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(original_svg_tag.strip() + modified_svg_body)

        ET.ElementTree(root).write(
            output_file, encoding="unicode", xml_declaration=False, method="xml")

        return output_file

    except Exception as error:
        print(f"Error embedding message: {error}")
        return None
