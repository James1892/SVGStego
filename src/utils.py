import re
import xml.etree.ElementTree as ET
from .constants import EMBED_TAGS, COORDINATE_PATTERN

NAMESPACE_DECLEL = re.compile(r'xmlns(?::(?P<prefix>[\w\.-]+))?="(?P<uri>[^"]+)"')


def remove_namespace(tag: str) -> str:
    if "}" in tag:
        parts = tag.split("}", 1)
        tag_without_ns = parts[-1]
        return tag_without_ns
    else:
        return tag


def validate_svg(file_name: str) -> bool:
    if not file_name.lower().endswith(".svg"):
        print("Invalid file extension.")
        return False

    try:
        tree = ET.parse(file_name)
        root = tree.getroot()

        tag_without_ns = root.tag.rsplit("}", 1)[-1]
        if tag_without_ns == "svg":
            return True
        else:
            return False

    except ET.ParseError:
        print("Error: File is not valid XML.")
        return False
    except Exception as error:
        print("Unexpected error: " + str(error))
        return False


def get_coordinates(file: str):
    try:
        coordinates = []
        tree = ET.parse(file)
        root = tree.getroot()

        for element in root.iter():
            local_tag = remove_namespace(element.tag)

            if local_tag in EMBED_TAGS:
                attribute_names = EMBED_TAGS[local_tag]

                attribute_index = 0
                while attribute_index < len(attribute_names):
                    attribute_name = attribute_names[attribute_index]

                    if attribute_name in element.attrib:
                        attribute_values = element.attrib[attribute_name]
                        matches = re.findall(COORDINATE_PATTERN, attribute_values)

                        match_index = 0
                        while match_index < len(matches):
                            number_string = matches[match_index]
                            float_value = float(number_string)
                            coordinates.append((local_tag, attribute_name, float_value))
                            match_index = match_index + 1

                    attribute_index = attribute_index + 1

        return coordinates

    except Exception as error:
        print("Error extracting coordinates: " + str(error))
        return []


def copy_svg(file: str, output_file: str | None = None) -> str | None:
    try:
        if output_file is None:
            output_file = file.replace(".", "-stego.", 1)

        with open(file, "r", encoding="utf-8") as original_file:
            file_data = original_file.read()

        with open(output_file, "w", encoding="utf-8") as copy_file:
            copy_file.write(file_data)

        return output_file

    except Exception as error:
        print("Error copying SVG file: " + str(error))
        return None


def embed_bit(value: str, bit: str) -> str:
    if "." not in value:
        if bit == "0":
            return value
        else:
            return value + ".1"

    integer_part, decimal_part = value.split(".", 1)

    if len(decimal_part) == 0:
        if bit == "0":
            return value
        else:
            return value + "1"

    decimal_digits = list(decimal_part)
    last_digit = decimal_digits[-1]

    if last_digit.isdigit():
        last_number = int(last_digit)
    else:
        last_number = 0

    want_odd = (bit == "1")
    is_odd = (last_number % 2 == 1)

    if want_odd != is_odd:
        if want_odd:
            if last_number < 9:
                decimal_digits[-1] = str(last_number + 1)
            else:
                decimal_digits[-1] = str(last_number - 1)
        else:
            if last_number > 0:
                decimal_digits[-1] = str(last_number - 1)
            else:
                decimal_digits[-1] = str(last_number + 1)

    new_decimal = ""
    digit_index = 0
    while digit_index < len(decimal_digits):
        new_decimal = new_decimal + decimal_digits[digit_index]
        digit_index = digit_index + 1

    return integer_part + "." + new_decimal


def process_attribute_values(attribute_string: str, full_binary: str, bit_index: int):
    result_string = attribute_string
    offset = 0

    for match in re.finditer(COORDINATE_PATTERN, attribute_string):
        matched_value = match.group()
        start_position, end_position = match.span()

        if bit_index >= len(full_binary):
            new_value = matched_value
        else:
            current_bit = full_binary[bit_index]
            bit_index = bit_index + 1
            new_value = embed_bit(matched_value, current_bit)

        adjusted_start = start_position + offset
        adjusted_end = end_position + offset

        result_string = result_string[:adjusted_start] + new_value + result_string[adjusted_end:]
        offset = offset + (len(new_value) - len(matched_value))

    return result_string, bit_index


def extract_namespaces(svg_path: str) -> dict[str, str]:
    try:
        with open(svg_path, "r", encoding="utf-8") as file_handle:
            head_content = file_handle.read(8192)

        namespace_map: dict[str, str] = {}

        for match in NAMESPACE_DECLEL.finditer(head_content):
            prefix_value = match.group("prefix")
            if prefix_value is None:
                prefix_value = ""

            uri_value = match.group("uri")
            namespace_map[prefix_value] = uri_value

        return namespace_map

    except Exception:
        return {}


def register_namespaces(namespace_map: dict[str, str]) -> None:
    for prefix, uri in namespace_map.items():
        ET.register_namespace(prefix, uri)
