def leb_encode(value: int) -> str:
    binary_str = ""
    while True:
        byte = value & 0x7F
        value >>= 7
        if value != 0:
            byte |= 0x80
        binary_str += f"{byte:08b}"
        if value == 0:
            break
    return binary_str


def leb_decode(bitstring: str) -> tuple[int, int]:
    value = 0
    shift = 0
    i = 0

    while i + 8 <= len(bitstring):
        byte_str = bitstring[i:i+8]
        byte = int(byte_str, 2)

        value |= (byte & 0x7F) << shift
        i += 8
        if (byte & 0x80) == 0:
            break
        shift += 7

    return value, i
