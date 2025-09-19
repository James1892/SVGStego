from .utils import get_coordinates
from .leb128 import leb_encode

def estimate_capacity(file: str, binary_message: str | None = None, detailed: bool = False):
    try:
        coords = get_coordinates(file)
        numCoords = len(coords)

        if numCoords == 0:
            print("Warning: No valid coordinates found in the file.")
            return 0, False

        bitCapacity = numCoords
        if binary_message is not None:
            message_bits = len(binary_message) 
        else: message_bits = bitCapacity

        encoded_length = leb_encode(message_bits)
        leb_size = len(encoded_length)

        usable_bits = bitCapacity - leb_size
        charCapacity = usable_bits // 8
        max_full_chars = (bitCapacity - leb_size) // 8
        total_bits_used = max_full_chars * 8 + leb_size

        if binary_message is not None:
            total_bits_needed = leb_size + message_bits
            if total_bits_needed > bitCapacity:
                print("Error: Message exceeds embedding capacity.")
                return charCapacity, False

        if detailed:
            print("--- Capacity ---")
            print(f"Usable bit capacity before LEB128: {total_bits_used} bits")
            print(f"Estimated LEB128 size: {leb_size} bits")
            print(f"Final estimated capacity: {charCapacity} characters (approx. {charCapacity * 8} bits)")

        return charCapacity, True

    except Exception as error:
        print(f"Unexpected error while estimating capacity: {error}")
        return 0, False
