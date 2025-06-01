import re
import xml.etree.ElementTree as ET
tree = ET.parse('jbovlaste-en(1).xml')
root = tree.getroot()
dictionary = root[0]

type_count = {}
score_count = {}
score_words = {}
in_dict = set()
word_freq = {}
replace_list = {}
freq_total = 0

for line in open("exclude_replace.txt", "r", encoding="utf-8"):
    parts = line.split()
    exclude = parts[0]
    replace = None
    if len(parts) > 1:
        replace = parts[1]
    replace_list[exclude] = replace

for line in open("freq_lojbanio.txt", "r", encoding="utf-8"):
    word, freq = line.split()
    freq = int(freq)
    if word in replace_list:
        word = replace_list[word]
    if word is not None:
        word_freq[word] = word_freq.get(word, 0) + freq
        freq_total += freq

freq_to_rank = {0: "N/A"}

print(f"The corpus has {freq_total} valid words")
freq_cumulative = 0
dict_freq_cumulative = 0
thresholds = [0.8, 0.9, 0.95, 0.98, 0.99]
freq_miles = [(x * freq_total) for x in thresholds]
freq_check = [False for x in thresholds]
milestone_freq = []
words = list(word_freq)
words.sort(key = lambda x: word_freq[x], reverse=True)
dictionary_inclusions = set()
for i, w in enumerate(words):
    freq_cumulative += word_freq[w]
    for j, milestone in enumerate(freq_miles):
        if not freq_check[j] and freq_cumulative > milestone:
            print(f"--- threshold {thresholds[j]} passed at {i+1} words, freq = {word_freq[w]} ---")
            milestone_freq.append(word_freq[w])
            freq_check[j] = True
        if word_freq[w] not in freq_to_rank:
            freq_to_rank[word_freq[w]] = i+1

for w in words:
    if word_freq[w] >= milestone_freq[3]:
        dictionary_inclusions.add(w)

with open("input.txt", "w", encoding="utf-8") as f:
    for word in dictionary:
        word_type = word.attrib["type"]
        type_count[word.attrib["type"]] = type_count.get(word.attrib["type"], 0) + 1
        score = int(word.find("score").text)
        score_count[score] = score_count.get(score, 0) + 1
        if score not in score_words:
            score_words[score] = []
        score_words[score].append(word.attrib["word"])
        add_to_dictionary = word_freq.get(word.attrib["word"], 0) >= milestone_freq[3] or word_type == "cmavo" or word_type == "gismu" or ((word_type == "lujvo" or word_type == "fu'ivla" or word_type == "experimental gismu" or word_type == "experimental cmavo") and score >= 7 and len(word.attrib["word"]) <= 8)
        if add_to_dictionary:
            in_dict.add(word.attrib["word"])
            freq = word_freq.get(word.attrib["word"], 0)
            dict_freq_cumulative += freq
            tag = "favored"
            rafsi_ccv = ""
            rafsi_cvc = ""
            rafsi_cvv = ""
            if freq >= milestone_freq[0]:
                tag = "core-1"
            elif freq >= milestone_freq[1]:
                tag = "core-2"
            elif freq >= milestone_freq[2]:
                tag = "core-3"
            elif freq >= milestone_freq[3]:
                tag = "common"
            for rafsi in word.findall("rafsi"):
                r = rafsi.text
                if re.fullmatch(r"[^aeiou][^aeiou][aeiou]", r):
                    rafsi_ccv = r
                elif re.fullmatch(r"[^aeiou][aeiou][^aeiou]", r):
                    rafsi_cvc = r
                elif re.fullmatch(r"[^aeiou][aeiou]'?[aeiou]", r):
                    rafsi_cvv = r
            gloss_all = ""
            for gloss in word.findall("glossword"):
                if len(gloss_all) > 0:
                    gloss_all += ", "
                gloss_all += gloss.attrib["word"]
            print(f"-entry: ", file=f)
            print(f'    -word {word.attrib["word"]}', file=f)
            if word.find("glossword") is not None:
                print(f'    -gloss {gloss_all}', file=f)
            print(f'    -type {word.attrib["type"].split()[-1]}', file=f)
            print(f'    -freq {freq}', file=f)
            print(f'    -rank {freq_to_rank[freq]}', file=f)
            print(f'    -tag {tag}', file=f)
            print(f'    -rafsi-cvc {rafsi_cvc}', file=f)
            print(f'    -rafsi-ccv {rafsi_ccv}', file=f)
            print(f'    -rafsi-cvv {rafsi_cvv}', file=f)
            print(f'    -definition:', file=f)
            if word.attrib["type"].split()[-1] == "cmavo":
                print(f'        -selmaho {word.findtext("selmaho", "")}', file=f)
            print(f'        -meaning:', file=f)
            print(f'            -exp {word.findtext("definition")}', file=f)
    
    print(f"The following words are common but aren't in the dictionary:")
    print(dictionary_inclusions - in_dict)
    for word in dictionary_inclusions - in_dict:
        in_dict.add(word)
        freq = word_freq.get(word, 0)
        dict_freq_cumulative += freq
        tag = "favored"
        if freq >= milestone_freq[0]:
            tag = "core-1"
        elif freq >= milestone_freq[1]:
            tag = "core-2"
        elif freq >= milestone_freq[2]:
            tag = "core-3"
        elif freq >= milestone_freq[3]:
            tag = "common"
        print(f"-entry: ", file=f)
        print(f'    -word {word}', file=f)
        print(f'    -type ', file=f)
        print(f'    -freq {freq}', file=f)
        print(f'    -rank {freq_to_rank[freq]}', file=f)
        print(f'    -tag {tag}', file=f)
        print(f'    -rafsi', file=f)
        print(f'    -definition:', file=f)
        print(f'        -meaning:', file=f)
        print(f'            -exp <i>This word is not registered on jbovlaste.</i>', file=f)
   
print(f"The dictionary includes {len(in_dict)} words")
print(f"The dictionary has {dict_freq_cumulative} valid words in the corpus")
print(f"coverage: {dict_freq_cumulative / freq_total:.6f}")

print(type_count)
score_list = list(score_count)
score_list.sort()
for score in score_list:
    print(f"{score}\t{score_count[score]}")
    if score_count[score] < 50:
        print(score_words[score])

