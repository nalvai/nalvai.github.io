import re
import os
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

lines = []
for file in os.listdir("words"):
    with open(os.path.join("words", file), "r", encoding="utf-8") as file:
        lines.extend(file.readlines())

manual_data = parse_lines(lines)["entry"]

speakers = set()

sources = {}
with open("sources.json", "r", encoding="utf-8") as file:
    sources = json.load(file)

def get_clean_quote(quote):
    result = ""
    for c in quote:
        if c.isalnum() or c == " ":
            result += c
    return result

quotes = set()
def process_quotes(entry):
    global quotes
    result = False
    for definition in entry["definition"]:
        for meaning in definition["meaning"]:
            if "example" in meaning and len(meaning["example"]) > 0:
                for quote in meaning["example"]:
                    if "source-id" in quote:
                        index = quote["source-id"]
                        source = sources[index]
                        for attrib in source:
                            if attrib not in ["instance"]:
                                quote[attrib] = source[attrib]
                        if "speaker" in quote:
                            for speaker in quote["speaker"].split(","):
                                speakers.add(speaker.strip())
                        if get_clean_quote(quote["lojban"]) not in quotes:
                            quotes.add(get_clean_quote(quote["lojban"]))
                            source["instance"] = source.get("instance", 0) + 1
                    else:
                        print(f"Warning: unsourced quote at {entry['word']}!")
                result = True
    return result

def search_in_manual_data(target):
    for entry in manual_data:
        if entry["word"] == target:
            return entry
    return None

good_data = []
included_wordlist = set()
canon_count = 0
addon_count = 0

for entry in automated_data:
    manual_entry = search_in_manual_data(entry["word"])
    if manual_entry:
        for tag in manual_entry:
            entry[tag] = manual_entry[tag]
        if process_quotes(manual_entry):
            entry["good"] = True
            included_wordlist.add(entry["word"])
            good_data.append(entry)
            canon_count += 1

for entry in manual_data:
    if entry["word"] not in included_wordlist:
        if process_quotes(entry):
            entry["tag"] = "attested"
            entry["freq"] = 0
            entry["rafsi-ccv"] = entry.get("rafsi-ccv", None) 
            entry["rafsi-cvc"] = entry.get("rafsi-cvc", None) 
            entry["rafsi-cvv"] = entry.get("rafsi-cvv", None) 
            entry["good"] = True
            included_wordlist.add(entry["word"])
            good_data.append(entry)
            automated_data.append(entry)
            addon_count += 1

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

print(f"{len(good_data)} words recorded ({canon_count} canon + {addon_count} addon)")
print(f"{len(quotes)} quotes recorded")
print("Conversion complete. Output saved to output.json.")

### Generating the HTML files ###

### README.md ###
source_order = [x for x in sources if "instance" in sources[x] and sources[x]["instance"] > 0]
source_order.sort(key=lambda x: sources[x]["instance"], reverse=True)
replace_1 = f"**NALVAI** is a Lojban dictionary that uses quotations from *real-world texts* as examples of usage. It currently contains **{len(good_data)} words** with [**{len(quotes)} quotations** from **{len(source_order)} Lojban texts**](https://github.com/nalvai/nalvai.github.io#sources). Please provide quotations and definitions to help the dictionary grow!"

replace_2 = ""
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
        replace_2 += to_print + "\n"

replace_2 += "\n"
replace_2 += "The quotes from chatlogs are from the following speakers: (in no particular order)\n"
replace_2 += "\n"
for s in speakers:
    replace_2 += re.sub("_", "\\_", s) + ", "

replace_2 += "\n"
replace_2 += "\n"
replace_2 += "Huge thanks to the following individuals who contributed to this project:\n"
replace_2 += "\n"
contributor_order = list(contributors)
contributor_order.sort(key=lambda x: len(contributors[x]), reverse=True)
for c in contributor_order:
    to_print = f"- {c} "
    if len(contributors[c]) == 1:
        to_print += "(1 word): "
    else:
        to_print += f"({len(contributors[c])} words): "
    for w in contributors[c]:
        to_print += f"**{w}**, "
    replace_2 += to_print[:-2] + "."

readme = open("README-core.md", "r", encoding="utf-8").read()
readme = readme.replace("<REPLACE-1>", replace_1)
readme = readme.replace("<REPLACE-2>", replace_2)
with open("README.md", "w", encoding="utf-8") as f:
    print(readme, file=f)

### wordlist.html ###
def generate_html_wordlist(wordlist):
    result = '<table><tbody>'
    result += '<tr>'
    for idx, word in enumerate(wordlist):
        w = word["word"]
        wdone = "wlist" if word.get("good", False) else "wlist-wip"
        wtype = word["type"].replace("'", "h")
        result += f'<td><a class="link {wdone} {wtype}" href="https://jbovlaste.lojban.org/dict/{w}">{w}</a></td>'
        if idx % 10 == 9:
            result += '</tr><tr>'
    result += '<td></td>' * ((10 - (len(wordlist) % 10)) % 10)
    result += '</tr>'
    result += "</tbody></table>"
    return result

tags = {"core-1": [], "core-2": [], "core-3": [], "common": [], "favored": [], "attested": []}
tag_desc = {
"core-1": "These words make up <b>80%</b> of the corpus.", 
"core-2": "These words make up further <b>10%</b> of the corpus. Combined with above, they make up <b>90%</b> of the corpus.", 
"core-3": "These words make up further <b>5%</b> of the corpus. Combined with above, they make up <b>95%</b> of the corpus.", 
"common": "These words make up further <b>3%</b> of the corpus. Combined with above, they make up <b>98%</b> of the corpus.", 
"favored": "Other words of historical significance. These words are included because they are either defined in gimste/ma'orste, or have a high vote score (at least +7) on jbovlaste.",
"attested": 'Other words used by the community. Words in this category are subject to the inclusion criteria described <a href="https://github.com/nalvai/nalvai.github.io?tab=readme-ov-file#suggest-a-worddefinition">here</a>. These words, while being actively used by the community, did not show up much in the frequency list, probably because of how the list was constructed.'}

words = [x for x in automated_data]
words.sort(key = lambda x: x["word"])
for w in words:
    tags[w["tag"]].append(w)

with open("wordlist.html", "w", encoding="utf-8") as f:
    head = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
          <title>Nalvai's Assortment of Lojban Vocabulary Attestation Instances</title>
            <link rel="stylesheet" href="style.css" />
            </head>
            <body>
              <h1>NALVAI <span style="color: red;">(DEMO)</span></h1>
                <h2>Nalvai's Assortment of Lojban Vocabulary Attestation Instances</h2>
                <p>These are the words I intend to include in <a href="/">the NALVAI project</a>. This list is largely based on a frequency list, although any words used by the community is welcome. <a href="https://forms.gle/81B1rohqByyoEDpv8">Suggest a word to be included!</a></p>
                <p>Currently the words here links to their corresponding entries in jbovlaste. <a href="/">Visit the main page</a> to see their entry in NALVAI!</p>
                <p>In this word list, a word with a fully filled background means that it currently has an entry in NALVAI. A word with only a border means that it has not yet been included, although I intend to include it in the future.</p>
    '''
    print(head, file=f)
    for tag in ["core-1", "core-2", "core-3", "common", "favored", "attested"]:
        print("<h3>" + tag.replace("-", " ").title() + (f" ({len(tags[tag])} words)" if not tag[0] == "a" else "") +  "</h3>", file=f)
        print("<p>" + tag_desc[tag] + "</p>", file=f)
        content = generate_html_wordlist(tags[tag])
        print(content, file=f)
    foot = '''
    </body>
    </html>
    '''
    print(foot, file=f)



