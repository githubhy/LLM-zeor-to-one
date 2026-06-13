(function(root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.ViewerSourceIndex = factory();
  }
})(typeof globalThis !== 'undefined' ? globalThis : this, function() {
  'use strict';

  function lineStartOffsets(source) {
    const starts = [0];
    for (let i = 0; i < source.length; i++) {
      if (source[i] === '\n') starts.push(i + 1);
    }
    return starts;
  }

  function lineStartOffset(source, lineNum) {
    const starts = lineStartOffsets(source);
    return starts[Math.max(0, Math.min(lineNum, starts.length - 1))] || 0;
  }

  function stripInlineMarkersWithMap(src) {
    const MARKERS = '*`~';
    const isWord = (c) => /[A-Za-z0-9]/.test(c);
    const isWS = (c) => c === ' ' || c === '\t' || c === '\n' || c === '\r';
    let stripped = '';
    const map = [];
    let prevWS = false;

    const emit = (k) => {
      const c = src[k];
      if (MARKERS.indexOf(c) !== -1) return;
      if (c === '=') {
        if (src[k + 1] === '=') return;
        if (src[k - 1] === '=') return;
      }
      if (c === ':') {
        const lookbehind = src.slice(Math.max(0, k - 16), k + 1);
        if (/==(?:yellow|green|red|blue|orange|purple|teal|pink):$/i.test(lookbehind)) return;
      }
      if (c === '_') {
        const prev = k > 0 ? src[k - 1] : '';
        const next = k + 1 < src.length ? src[k + 1] : '';
        if (isWord(prev) && isWord(next)) {
          stripped += c;
          map.push(k);
          prevWS = false;
        }
        return;
      }
      if (isWS(c)) {
        if (prevWS) return;
        stripped += ' ';
        map.push(k);
        prevWS = true;
        return;
      }
      stripped += c;
      map.push(k);
      prevWS = false;
    };

    let i = 0;
    while (i < src.length) {
      if (src[i] === '<' && src.startsWith('<!--', i)) {
        const end = src.indexOf('-->', i + 4);
        if (end !== -1) {
          i = end + 3;
          continue;
        }
      }

      if (src[i] === '[') {
        let j = i + 1;
        let depth = 1;
        while (j < src.length) {
          const c = src[j];
          if (c === '\n') break;
          if (c === '\\' && j + 1 < src.length) {
            j += 2;
            continue;
          }
          if (c === '[') depth++;
          else if (c === ']') {
            depth--;
            if (depth === 0) break;
          }
          j++;
        }
        if (depth === 0 && j < src.length && src[j] === ']') {
          const afterBracket = j + 1;
          if (src[afterBracket] === '(') {
            let k = afterBracket + 1;
            let urlDepth = 1;
            while (k < src.length) {
              const c = src[k];
              if (c === '\n') break;
              if (c === '\\' && k + 1 < src.length) {
                k += 2;
                continue;
              }
              if (c === '(') urlDepth++;
              else if (c === ')') {
                urlDepth--;
                if (urlDepth === 0) break;
              }
              k++;
            }
            if (urlDepth === 0 && k < src.length) {
              for (let m = i + 1; m < j; m++) emit(m);
              i = k + 1;
              continue;
            }
          }
          if (src[afterBracket] === '[') {
            let k = afterBracket + 1;
            while (k < src.length && src[k] !== ']' && src[k] !== '\n') k++;
            if (k < src.length && src[k] === ']') {
              for (let m = i + 1; m < j; m++) emit(m);
              i = k + 1;
              continue;
            }
          }
        }
      }

      emit(i);
      i++;
    }

    return { stripped, map };
  }

  function buildBlockSourceIndex(blockSource) {
    const visible = stripInlineMarkersWithMap(blockSource);
    return {
      blockSource,
      visibleText: visible.stripped,
      visibleToSource: visible.map,
    };
  }

  function sourceOffsetFromVisibleOffset(index, visibleOffset) {
    const map = index.visibleToSource;
    if (visibleOffset <= 0) return 0;
    if (visibleOffset >= map.length) return index.blockSource.length;
    return map[visibleOffset];
  }

  function findInlineMathRanges(blockSource) {
    const ranges = [];
    let i = 0;
    while (i < blockSource.length) {
      if (blockSource[i] !== '$' || blockSource[i - 1] === '\\') {
        i++;
        continue;
      }
      if (blockSource[i + 1] === '$') {
        i += 2;
        continue;
      }
      let j = i + 1;
      while (j < blockSource.length) {
        if (blockSource[j] === '\n') break;
        if (blockSource[j] === '$' && blockSource[j - 1] !== '\\') {
          ranges.push({
            sourceStart: i,
            sourceEnd: j + 1,
            text: blockSource.slice(i, j + 1),
          });
          i = j + 1;
          break;
        }
        j++;
      }
      if (j >= blockSource.length || blockSource[j] === '\n') i++;
    }
    return ranges;
  }

  return {
    lineStartOffsets,
    lineStartOffset,
    stripInlineMarkersWithMap,
    buildBlockSourceIndex,
    sourceOffsetFromVisibleOffset,
    findInlineMathRanges,
  };
});
