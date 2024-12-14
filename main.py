import argparse
import json

result_data = []
log_file_data = []


def parse_args():
    parser = argparse.ArgumentParser(description="Assembler and Interpreter for UVM")
    parser.add_argument("mode", choices=["assemble", "interpret"], help="Operation mode: 'assemble' or 'interpret'")
    parser.add_argument("input_file", help="Input file")
    parser.add_argument("output_file", help="Output file")
    parser.add_argument("--log_file", help="Log file (JSON format)")
    parser.add_argument("--result_file", help="Result file for interpreter (JSON format)")
    parser.add_argument("--memory_range", help="Memory range for interpreter (start:end)", type=str)
    return parser.parse_args()


def read_input_file(input_file):
    try:
        with open(input_file, "r", encoding="utf-8") as file:
            return file.readlines()
    except FileNotFoundError:
        print(f"Error! File {input_file} not found")
        exit(1)


def parse_instruction(instruction):
    parts = instruction.split(',')
    values = {}
    for part in parts:
        key, value = part.split('=')
        values[key.strip()] = int(value.strip())
    return values


def assemble_instruction(value):
    global result_data, log_file_data
    A = value['A']
    B = value['B']
    C = value['C']
    D = value.get('D', 0)

    command = bytearray(11)
    command[0] = A & 0xF
    command[0] |= (B & 0xF) << 4
    command[1] = (B >> 4) & 0xFF
    command[2] = (B >> 12) & 0xFF
    command[3] = (B >> 20) & 0xFF
    command[4] = (C & 0xFF)
    command[5] = (C >> 8) & 0xFF
    command[6] = (C >> 16) & 0xFF
    command[7] = (C >> 24) & 0xFF
    command[8] = (D & 0xFF)
    command[9] = (D >> 8) & 0xFF
    command[10] = (D >> 16) & 0xFF

    result_data.extend(command)

    log_file_data.append({
        "A": A, "B": B, "C": C, "D": D,
        "result": list(command)
    })


def write_log_file(log_file):
    with open(log_file, "w", encoding="utf-8") as file:
        json.dump(log_file_data, file, indent=4)
    print(f"Log written to {log_file}")


def write_binary_file(output_file):
    with open(output_file, "wb") as file:
        file.write(bytearray(result_data))
    print(f"Binary written to {output_file}")


def read_binary_file(input_file):
    try:
        with open(input_file, "rb") as file:
            return file.read()
    except FileNotFoundError:
        print(f"Error! File {input_file} not found")
        exit(1)


def interpret_commands(binary_data, memory_range):
    memory = [0] * 1024
    for i in range(0, len(binary_data), 11):
        if i + 11 > len(binary_data):
            break
        command = binary_data[i:i + 11]

        A = command[0] & 0xF
        B = ((command[0] >> 4) & 0xF) | (command[1] << 4) | (command[2] << 12) | (command[3] << 20)
        C = command[4] | (command[5] << 8) | (command[6] << 16) | (command[7] << 24)
        D = command[8] | (command[9] << 8) | (command[10] << 16)

        if A == 5:
            memory[B] = C
        elif A == 7:
            memory[B] = memory[C]
        elif A == 3:
            memory[B + C] = memory[D]
        elif A == 9:
            memory[B] = memory[C] ^ memory[D]

    start, end = map(int, memory_range.split(":"))
    return memory[start:end]


def write_result_file(result_file, memory_slice):
    result_data = [{"address": i, "value": value} for i, value in enumerate(memory_slice)]
    with open(result_file, "w", encoding="utf-8") as file:
        json.dump(result_data, file, indent=4)
    print(f"Result written to {result_file}")


def main():
    args = parse_args()
    if args.mode == "assemble":
        instructions = read_input_file(args.input_file)
        for line in instructions:
            if not line.strip():
                continue
            values = parse_instruction(line.strip())
            assemble_instruction(values)
        write_binary_file(args.output_file)
        write_log_file(args.log_file)
    elif args.mode == "interpret":
        if not args.result_file or not args.memory_range:
            print("Error! Result file and memory range are required for interpretation.")
            exit(1)
        binary_data = read_binary_file(args.input_file)
        memory_slice = interpret_commands(binary_data, args.memory_range)
        write_result_file(args.result_file, memory_slice)


if __name__ == "__main__":
    main()