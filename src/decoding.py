import re
import xml.etree.ElementTree as ET

from .constants import EMBED_TAGS, COORDINATE_PATTERN
from .utils import remove_namespace
from .leb128 import leb_decode


def convert_binary_to_text(binary_message: str) -> str:
    try:
        if binary_message is None:
            return ""

        if len(binary_message) == 0:
            return ""

        # Truncate to a multiple of 8 bits
        full_bytes_length = (len(binary_message) // 8) * 8
        truncated_bits = ""
        current_index = 0
        while current_index < full_bytes_length:
            truncated_bits = truncated_bits + binary_message[current_index]
            current_index = current_index + 1

        # Convert bits into characters
        characters = []
        bit_index = 0
        while bit_index < len(truncated_bits):
            byte_bits = truncated_bits[bit_index:bit_index + 8]
            byte_value = int(byte_bits, 2)
            character = chr(byte_value)
            characters.append(character)
            bit_index = bit_index + 8

        # Reconstruct string
        result_text = ""
        char_index = 0
        while char_index < len(characters):
            result_text = result_text + characters[char_index]
            char_index = char_index + 1

        return result_text

    except Exception as error:
        print("Error converting binary to text: " + str(error))
        return ""


def decode_message(file: str) -> str | None:
    try:
        tree = ET.parse(file)
        root = tree.getroot()
        binary_data = ""

        for element in root.iter():
            local_tag = remove_namespace(element.tag)

            if local_tag in EMBED_TAGS:
                embed_attributes = EMBED_TAGS[local_tag]

                attribute_index = 0
                while attribute_index < len(embed_attributes):
                    attribute_name = embed_attributes[attribute_index]

                    if attribute_name in element.attrib:
                        attribute_values = element.attrib[attribute_name]
                        matches = re.findall(COORDINATE_PATTERN, attribute_values)

                        match_index = 0
                        while match_index < len(matches):
                            number_string = matches[match_index]

                            bit_value = "0"
                            if "." in number_string:
                                parts = number_string.split(".")
                                if len(parts) > 1:
                                    decimal_part = parts[-1]
                                else:
                                    decimal_part = ""

                                if len(decimal_part) > 0:
                                    last_digit = decimal_part[-1]
                                else:
                                    last_digit = "0"

                                # Odd/even check of last decimal digit
                                if int(last_digit) % 2 == 1:
                                    bit_value = "1"
                                else:
                                    bit_value = "0"
                            else:
                                bit_value = "0"

                            binary_data = binary_data + bit_value
                            match_index = match_index + 1

                    attribute_index = attribute_index + 1

        if len(binary_data) == 0:
            return None

        message_length, leb_end_position = leb_decode(binary_data)

        message_bits = ""
        current_position = leb_end_position
        message_end_position = leb_end_position + message_length
        while current_position < len(binary_data) and current_position < message_end_position:
            message_bits = message_bits + binary_data[current_position]
            current_position = current_position + 1

        if len(message_bits) == 0:
            return None

        decoded_message = convert_binary_to_text(message_bits)

        if decoded_message is not None and len(decoded_message) > 0:
            return decoded_message
        else:
            return None

    except Exception as error:
        print("Error decoding message: " + str(error))
        return None
