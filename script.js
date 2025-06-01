let dictionary = [];
let fuse;

const input = document.getElementById('search');
const typeFilterEls = document.querySelectorAll('#typeFilter input');
const tagFilterEls = document.querySelectorAll('#tagFilter input');
const sortOrderEl = document.getElementById('sortOrder');
const resultsDiv = document.getElementById('results');

// from https://www.geeksforgeeks.org/edit-distance-dp-5/
function editDistance(s1, s2) {
    let m = s1.length;
    let n = s2.length;

    // Stores dp[i-1][j-1]
    let prev = 0;
    let curr = new Array(n + 1).fill(0);

    for (let j = 0; j <= n; j++) 
        curr[j] = j;

    for (let i = 1; i <= m; i++) {
        prev = curr[0];
        curr[0] = i;
        for (let j = 1; j <= n; j++) {
            let temp = curr[j];
            if (s1[i - 1] === s2[j - 1])
                curr[j] = prev;
            else
                curr[j] = 1 + Math.min(curr[j - 1], prev, curr[j]);
            prev = temp;
        }
    }

    return curr[n];
}

function longestCommonPrefix(a1, a2) {
  let result = 0;
  while(result < Math.min(a1.length, a2.length)){
    if (a1[result] !== a2[result]) return result;
    result += 1;
  }
  return result;
}

function getCheckedValues(elements) {
  return Array.from(elements)
    .filter(el => el.checked)
    .map(el => el.value);
}

function highlightMatch(text, matchInfo) {
  if (!matchInfo || !matchInfo.indices || matchInfo.indices.length === 0) return text;

  let result = '';
  let lastIndex = 0;

  matchInfo.indices.forEach(([start, end]) => {
    result += text.slice(lastIndex, start);
    result += '<mark>' + text.slice(start, end + 1) + '</mark>';
    lastIndex = end + 1;
  });

  result += text.slice(lastIndex);
  return result;
}

function generateQuoteElement(quote){
  const result = document.createElement('div');

  const quoteBody = document.createElement('blockquote');
  const quoteRaw = document.createElement('p');
  quoteRaw.innerHTML = "<b>" + quote.lojban.replaceAll("{{", "<u>").replaceAll("}}", "</u>") + "</b>";
  quoteBody.appendChild(quoteRaw);
  if (quote.english !== undefined) {
    const quoteTrans = document.createElement('p');
    quoteTrans.innerHTML = quote.english.replaceAll("{{", "<u>").replaceAll("}}", "</u>");
    quoteBody.appendChild(quoteTrans);
  }
  result.appendChild(quoteBody);

  const citation = document.createElement('p');
  citation.innerHTML = `—<cite>${quote.source}</cite>`;
  if (quote.author !== undefined) {
    citation.innerHTML += ` by ${quote.author}`;
  }
  if (quote.translator !== undefined) {
    citation.innerHTML += `, translated by ${quote.translator}`;
  }
  result.appendChild(citation);

  if (quote.note !== undefined) {
    const quoteNote = document.createElement('p');
    quoteNote.setAttribute("class", "note");
    quoteNote.innerHTML = quote.note.replaceAll("{{", "<b>").replaceAll("}}", "</b>");
    result.appendChild(quoteNote);
  }

  return result;
}

function convertMath(text){
  text = text.replaceAll(/\$?x_\{?([0-9])\}?\$?/g, "x<sub>$1</sub>");
  return text
}

function generateMeaningElement(meaning){
  const result = document.createElement('li');
  const explanation = document.createElement('p');
  if (meaning.variation !== undefined){
    explanation.innerHTML += `(<i>${meaning.variation}</i>) `;
  }
  if (meaning.context !== undefined){
    to_render = meaning.context.replaceAll("{{", "<b>").replaceAll("}}", "</b>");
    explanation.innerHTML += `(${to_render}) `;
  }
  explanation.innerHTML += convertMath(meaning.exp).replaceAll("{{", "<b>").replaceAll("}}", "</b>");
  result.appendChild(explanation);
  if (meaning.note !== undefined){
    const note = document.createElement('p');
    note.setAttribute("class", "note");
    to_render = meaning.note.replaceAll("{{", "<b>").replaceAll("}}", "</b>");
    note.innerHTML += `Note: ${to_render} `;
    result.appendChild(note);
  }
  if (meaning.example !== undefined){
    for (const quote of meaning.example){
      result.appendChild(generateQuoteElement(quote));
    }
  }
  return result
}

function generateDefinitionElement(definition){
  const result = document.createElement('div');
  if (definition.selmaho !== undefined){
    const selmaho = document.createElement('p');
    selmaho.innerHTML = `selma'o <b>${definition.selmaho}</b>:`;
    result.appendChild(selmaho);
  }
  const list = document.createElement('ul');
  for (meaning of definition.meaning){
    list.appendChild(generateMeaningElement(meaning));
  }
  result.appendChild(list);
  return result
}

function generateMetaElement(item) {
  const result = document.createElement('p');
  result.setAttribute("class", "note");
  const freqText = `Frequency: ${(Number(item.freq)/3139.9446).toFixed(2)} per 10000 `;
  const rankText = item.tag.startsWith("core") ? `(rank: ${item.rank}) ` : "";
  const rafsiText = "rafsi: " + `${item["rafsi-cvc"]} ${item["rafsi-ccv"]} ${item["rafsi-cvv"]}`.replaceAll("null", "").trim();
  result.innerHTML = `${freqText}${rankText}• ${rafsiText}`;
  return result;
}

function generateLabelElement(item, matches) {

  const header = document.createElement('summary');

  const statusHTML = (item.good) ? "✅" : "🕰️";

  const wordMatch = matches.find(m => m.key === 'word');
  const wordHTML = highlightMatch(item.word, wordMatch);
  
  const defMatch = matches.find(m => m.key === 'gloss');
  const defHTML = highlightMatch(item.gloss, defMatch);

  const tagsHTML = item.tags ? `Tags: ${item.tags.join(', ')}` : '';
  const style = item.type === "fu'ivla" ? "fuhivla" : item.type;
  const typeName = item.type === "fu'ivla" ? "zi'evla" : item.type;

  let tagText = "";
  switch (item.tag) {
  case "core-1":
    tagText = " ⁂";
    break;
  case "core-2":
    tagText = " ⁑";
    break;
  case "core-3":
    tagText = " ⁎";
    break;
  case "common":
    tagText = " •";
    break;
  }

  header.innerHTML = `${statusHTML} <strong>${wordHTML}</strong> • <span class="wtype ${style}">${typeName}${tagText}</span> • <em>${defHTML}</em>`;
  return header;
}

function displayResults(results) {
  resultsDiv.innerHTML = '';
  if (results.length === 0) {
    resultsDiv.innerHTML = '<em>No results found.</em>';
    return;
  }

  const found = document.createElement('em');
  found.innerHTML = `${results.length} words, ${results.filter(res => res.item.good).length} are good (reviewed and with quotes)`;
  resultsDiv.appendChild(found);

  results.forEach(res => {
    const item = res.item;
    const matches = res.matches || [];

    const entry = document.createElement('details');
    entry.className = 'entry';

    entry.appendChild(generateLabelElement(item, matches));
    entry.appendChild(generateMetaElement(item));
    for (const def of item.definition){
      entry.appendChild(generateDefinitionElement(def));
    }

    resultsDiv.appendChild(entry);

  });
}



function filterAndDisplay() {
  const query = input.value.trim();
  const selectedTypes = getCheckedValues(typeFilterEls);
  const selectedTags = getCheckedValues(tagFilterEls);
  const sortOrder = sortOrderEl.value;

  let results = [];

  if (sortOrder === 'best-def' && query) {
    results = fuse.search(query); // Contains .item and .matches
  } else if (sortOrder === 'best-word' && query) {
    results = dictionary.filter(item => (editDistance(item.word, query.toLowerCase()) < item.word.length / 2)).map(item => ({ item }));
  } else {
    results = dictionary.map(item => ({ item }));
  }

  // Type filtering
  if (selectedTypes.length > 0) {
    results = results.filter(entry => selectedTypes.includes(entry.item.type));
  }

  // Type filtering
  if (selectedTags.length > 0) {
    results = results.filter(entry => selectedTags.includes(entry.item.tag));
  }


/*
  // Tag filtering
  if (selectedTags.length > 0) {
    results = results.filter(entry =>
      entry.item.tags && selectedTags.every(tag => entry.item.tags.includes(tag))
    );
  }
*/

  // Sort results
  if (sortOrder === 'az') {
    results.sort((a, b) => a.item.word.localeCompare(b.item.word));
  } else if (sortOrder === 'za') {
    results.sort((a, b) => b.item.word.localeCompare(a.item.word));
  } else if (sortOrder === 'best-word' && query) {
    results.sort((a, b) => {
      const q = query.toLowerCase();
      const editScore = editDistance(a.item.word, q) - editDistance(b.item.word, q);
      if (editScore !== 0) return editScore;
      return longestCommonPrefix(b.item.word, q) - longestCommonPrefix(a.item.word, q);
    });
  } else if (sortOrder === 'best-def' && query) {
    results.sort((a, b) => {
      const scoreA = a.score ?? 1;
      const scoreB = b.score ?? 1;

      const key = sortOrder === 'best-word' ? 'word' : 'gloss';

      const aText = a.item[key]?.toLowerCase() ?? '';
      const bText = b.item[key]?.toLowerCase() ?? '';
      const q = query.toLowerCase();

      const aExact = aText === q;
      const bExact = bText === q;
      if (aExact && !bExact) return -1;
      if (bExact && !aExact) return 1;

      const aStarts = aText.startsWith(q);
      const bStarts = bText.startsWith(q);
      if (aStarts && !bStarts) return -1;
      if (bStarts && !aStarts) return 1;

      return scoreA - scoreB;
    });
  } else if (sortOrder === 'freq') {
    results.sort((a, b) => Number(b.item.freq) - Number(a.item.freq));
  } else { // The default is to sort them by A-Z
    results.sort((a, b) => a.item.word.localeCompare(b.item.word));
  }

  displayResults(results);
}

fetch('output.json')
  .then(res => res.json())
  .then(data => {
    dictionary = data;
    fuse = new Fuse(dictionary, {
      keys: ['gloss'],
      threshold: 0.4,
      includeMatches: true
    });
    filterAndDisplay(); // Initial load
  });

// Event listeners
input.addEventListener('input', filterAndDisplay);
typeFilterEls.forEach(el => el.addEventListener('change', filterAndDisplay));
tagFilterEls.forEach(el => el.addEventListener('change', filterAndDisplay));
sortOrderEl.addEventListener('change', filterAndDisplay);
