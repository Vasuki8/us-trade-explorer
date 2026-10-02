import { searchProducts, type ProductSearch } from '../lib/product-search';

const form = document.querySelector<HTMLFormElement>('#product-search')!;
const input = document.querySelector<HTMLInputElement>('#search')!;
const cards = [
  ...document.querySelectorAll<HTMLAnchorElement>('[data-product-code]'),
];
const chapters = cards.map((card) => ({
  code: card.dataset.productCode!,
  name: card.dataset.productName!,
}));
const summary = document.querySelector<HTMLElement>('#search-summary')!;
const guidance = document.querySelector<HTMLElement>('#empty-search')!;
const title = document.querySelector<HTMLElement>('#search-guidance-title')!;
const explanation = document.querySelector<HTMLElement>('#search-guidance')!;
const suggestion = document.querySelector<HTMLElement>('#parent-suggestion')!;
const parentLink =
  document.querySelector<HTMLAnchorElement>('#parent-chapter')!;
const limitedCoverage = `This preview covers only ${chapters.length} sample chapters. A missing result does not mean that trade is zero.`;

function render(result: ProductSearch) {
  input.value = result.term;
  cards.forEach((card) => {
    card.hidden = !result.matches.some(
      (p) => p.code === card.dataset.productCode,
    );
  });
  guidance.hidden = result.kind !== 'detail' && result.matches.length !== 0;
  suggestion.hidden = true;

  if (result.kind === 'detail') {
    title.textContent = 'Detailed product codes are not covered';
    const disclosure =
      'This preview contains HS2 chapter totals only. We cannot verify this detailed code or report its trade.';
    const coverage = result.parent
      ? `HS ${result.parent.code} is available as broader chapter coverage. Choose the chapter suggestion to explore its totals.`
      : `The parent chapter HS ${result.parentCode} is not included. ${limitedCoverage}`;
    summary.textContent = `${disclosure} ${coverage}`;
    explanation.textContent = `${disclosure} ${coverage}`;
    if (result.parent) {
      const parentCard = cards.find(
        (card) => card.dataset.productCode === result.parent!.code,
      )!;
      parentLink.href = parentCard.getAttribute('href')!;
      parentLink.textContent = `Explore broader HS ${result.parent.code} chapter: ${result.parent.name}`;
      suggestion.hidden = false;
    }
    return;
  }

  const count = result.matches.length;
  const matches = `${count} matching sample chapter${count === 1 ? '' : 's'}.`;
  if (count === 0) {
    title.textContent = 'No matching sample chapter';
    const recovery =
      result.kind === 'invalid'
        ? 'Use a two-digit HS chapter code, such as 09, or a product name. Unsupported or mixed codes cannot be searched in this preview.'
        : 'Try a broader word or a two-digit HS chapter code.';
    explanation.textContent = `${recovery} ${limitedCoverage}`;
    summary.textContent = `${matches} ${recovery} ${limitedCoverage}`;
  } else {
    const choice =
      result.kind === 'all'
        ? ' Showing all available sample chapters.'
        : count > 1
          ? ' Choose a description before exploring.'
          : '';
    summary.textContent = `${matches}${choice} HS2022 · 2-digit classification.`;
  }
}

function searchURL(term: string) {
  const url = new URL(location.href);
  url.search = '';
  if (term) url.searchParams.set('q', term);
  return url;
}

function restore() {
  const result = searchProducts(
    new URL(location.href).searchParams.get('q') ?? '',
    chapters,
  );
  const url = searchURL(result.term);
  if (url.href !== location.href) history.replaceState({}, '', url);
  render(result);
}

form.addEventListener('submit', (event) => {
  event.preventDefault();
  const result = searchProducts(input.value, chapters);
  const url = searchURL(result.term);
  if (url.href !== location.href) history.pushState({}, '', url);
  render(result);
});
document
  .querySelector<HTMLButtonElement>('#clear-search')!
  .addEventListener('click', () => {
    input.value = '';
    form.requestSubmit();
    input.focus();
  });
window.addEventListener('popstate', restore);
restore();
