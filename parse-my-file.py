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

speakers = set()

sources = {}
with open("sources.json", "r", encoding="utf-8") as file:
    sources = json.load(file)

quotes_total = 0
def process_quotes(entry):
    global quotes_total
    result = False
    for definition in entry["definition"]:
        for meaning in definition["meaning"]:
            if "example" in meaning and len(meaning["example"]) > 0:
                for quote in meaning["example"]:
                    if "source-id" in quote:
                        quotes_total += 1
                        index = quote["source-id"]
                        source = sources[index]
                        for attrib in source:
                            quote[attrib] = source[attrib]
                        source["instance"] = source.get("instance", 0) + 1
                        if "speaker" in quote:
                            for speaker in quote["speaker"].split(","):
                                speakers.add(speaker.strip())
                    else:
                        print(f"Warning: unsourced quote at {entry[word]}!")
                result = True
    return result

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
        if process_quotes(manual_entry):
            entry["good"] = True
            good_data.append(entry)

contributors = {}
for entry in good_data:
    if "contributor" in entry:
        c = entry["contributor"]
        if c not in contributors:
            contributors[c] = []
        contributors[c].append(entry["word"])

# Save to JSON
with open("output_all.json", "w", encoding="utf-8") as json_file:
    json.dump(automated_data, json_file, ensure_ascii=False, indent=4)
with open("output.json", "w", encoding="utf-8") as json_file:
    json.dump(good_data, json_file, ensure_ascii=False, indent=4)

print(f"{len(good_data)} words recorded")
print(f"{quotes_total} quotes recorded")
print("Conversion complete. Output saved to output.json.")

source_order = [x for x in sources if "instance" in sources[x] and sources[x]["instance"] > 0]
source_order.sort(key=lambda x: sources[x]["instance"], reverse=True)
for i in source_order:
    source = sources[i]
    if source.get("instance", 0) > 0:
        to_print = "- "
        if source["instance"] == 1:
            to_print += "(1 quote) "
        else:
            to_print += f'({source["instance"]} quotes) ' 
        if "link" in source:
            to_print += f'[{source["source"]}]({source["link"]})'
        else:
            to_print += f'{source["source"]}'
        if "author" in source:
            to_print += f' by {source["author"]}'
        if "translator" in source:
            to_print += f', translation by {source["translator"]}'
        if "originallink" in source:
            to_print += f' ([Original]({source["originallink"]}))'
        print(to_print)
print()
print("The quotes from roljbogu'e chatlog are from the following speakers: ")
print()
for s in speakers:
    print(s, end=", ")

print()
print()
print("Huge thanks to the following individuals who contributed to this project:")
print()
contributor_order = list(contributors)
contributor_order.sort(key=lambda x: len(contributors[x]), reverse=True)
for c in contributor_order:
    to_print = f"- {c} "
    if len(contributors[c]) == 1:
        to_print += "(1 word): "
    else:
        to_print += f"({len(contributor[c])} words): "
    for w in contributors[c]:
        to_print += f"**{w}**, "
    print(to_print[:-2] + ".")

print()
print(f"**NALVAI** is a Lojban dictionary that uses quotations from *real-world texts* as examples of usage. It currently contains **{len(good_data)} words** with [**{quotes_total} quotations** from **{len(source_order)} Lojban texts**](https://github.com/nalvai/nalvai.github.io#sources). Please provide quotations and definitions to help the dictionary grow!")

