import json

def parse_lines(lines):
    def get_indent_level(line):
        return len(line) - len(line.lstrip(' '))

    def parse_block(index, current_indent):
        obj = {}
        list_tracker = {}

        while index < len(lines):
            line = lines[index]
            indent = get_indent_level(line)

            if indent < current_indent:
                break  # End of this block

            if not line.strip():  # Skip empty lines
                index += 1
                continue

            key_value = line.strip()[1:]  # Remove the leading "-"
            if ' ' in key_value:
                key, value = key_value.split(' ', 1)
            else:
                key, value = key_value, None

            index += 1

            # Peek next line to check if it’s a nested object
            if index < len(lines) and get_indent_level(lines[index]) > indent:
                nested_obj, index = parse_block(index, get_indent_level(lines[index]))
                value = nested_obj

            if value is None:
                value = None  # Explicit null

            is_list_key = key.endswith(":")

            if is_list_key:
                key = key.rstrip(":")  # Remove colon for JSON key
                if key not in obj:
                    obj[key] = []
                obj[key].append(value)
            else:
                if key in obj:
                    if key not in list_tracker:
                        obj[key] = [obj[key]]
                        list_tracker[key] = True
                    obj[key].append(value)
                else:
                    obj[key] = value

        return obj, index

    parsed_obj, _ = parse_block(0, 0)
    return parsed_obj

# Load and process file: automated data
with open("input.txt", "r", encoding="utf-8") as file:
    lines = file.readlines()

automated_data = parse_lines(lines)["entry"]

with open("my-file.txt", "r", encoding="utf-8") as file:
    lines = file.readlines()

manual_data = parse_lines(lines)["entry"]

def is_good(entry):
    for definition in entry["definition"]:
        for meaning in definition["meaning"]:
            if "example" in meaning and len(meaning["example"]) > 0:
                return True
    return False

def search_in_manual_data(target):
    for entry in manual_data:
        if entry["word"] == target:
            return entry
    return None

good_data = []

for entry in automated_data:
    manual_entry = search_in_manual_data(entry["word"])
    if manual_entry:
        for tag in manual_entry:
            entry[tag] = manual_entry[tag]
        if is_good(manual_entry):
            entry["good"] = True
            good_data.append(entry)


# Save to JSON
with open("output_all.json", "w", encoding="utf-8") as json_file:
    json.dump(automated_data, json_file, ensure_ascii=False, indent=4)
with open("output.json", "w", encoding="utf-8") as json_file:
    json.dump(good_data, json_file, ensure_ascii=False, indent=4)

print("Conversion complete. Output saved to output.json.")
