import argparse
from src.capacity import estimate_capacity
from src.decoding import decode_message
from src.embedding import embed_message
from src.utils import validate_svg

def create_parser():
    parser = argparse.ArgumentParser(
        prog="SVGStego",
        description="SVG steganography program for hiding messages in SVG files.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-e", "--embed", action="store_true", help="Embed a message into an SVG file.")
    group.add_argument("-d", "--decode", action="store_true", help="Decode a hidden message from an SVG file.")
    group.add_argument("-c", "--calculate", action="store_true", help="Calculate the maximum message capacity of an SVG file.")

    parser.add_argument("-f", "--file", required=True, dest="svgFile", help="Specify the SVG file to process.")
    parser.add_argument("-m", "--message", dest="message", help="Specify the message to embed. Required when using -e / --embed.")
    return parser

def main():
    parser = create_parser()
    args = parser.parse_args()

    if args.embed:
        if not args.message:
            print("Error: You must provide a message using -m / --message when embedding.")
            return
        if not validate_svg(args.svgFile):
            return
        modified_file = embed_message(args.svgFile, args.message)
        if modified_file:
            print(f"Message successfully embedded into {modified_file}.")

    elif args.decode:
        if not validate_svg(args.svgFile):
            print("Error: Invalid SVG file.")
            return
        decoded_message = decode_message(args.svgFile)
        if decoded_message:
            print(f"Decoded Message: \n{decoded_message}")
        else:
            print("No message found or decoding failed.")

    elif args.calculate:
        if not validate_svg(args.svgFile):
            print("Error: Invalid SVG file.")
            return
        estimate_capacity(args.svgFile, detailed=True)

if __name__ == "__main__":
    main()
