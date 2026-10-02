export interface SearchChapter {
  code: string;
  name: string;
}

export interface ProductSearch {
  term: string;
  kind: 'all' | 'chapter' | 'name' | 'detail' | 'invalid';
  matches: SearchChapter[];
  parentCode?: string;
  parent?: SearchChapter;
}

export function searchProducts(
  raw: string,
  chapters: SearchChapter[],
): ProductSearch {
  const term = raw
    .replace(/[\r\n]/g, '')
    .trim()
    .slice(0, 120);
  if (!term) return { term, kind: 'all', matches: chapters };

  const code = /^(?:HS\s*)?(\d+)$/i.exec(term)?.[1];
  if (code) {
    if (code.length === 2) {
      return {
        term,
        kind: 'chapter',
        matches: chapters.filter((p) => p.code === code),
      };
    }
    if ([4, 6, 8, 10].includes(code.length)) {
      const parentCode = code.slice(0, 2);
      return {
        term,
        kind: 'detail',
        matches: [],
        parentCode,
        parent: chapters.find((p) => p.code === parentCode),
      };
    }
    return { term, kind: 'invalid', matches: [] };
  }

  // Code-shaped text must not fall through to substring matching.
  if (/\d/.test(term)) return { term, kind: 'invalid', matches: [] };
  return {
    term,
    kind: 'name',
    matches: chapters.filter((p) =>
      p.name.toLowerCase().includes(term.toLowerCase()),
    ),
  };
}
