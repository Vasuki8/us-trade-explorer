import { change } from '../../packages/contracts/trade.ts';

interface ChangeOptions {
  priorYearIncluded: boolean;
  scope: 'observation' | 'included-chapters';
}

// Presentation only: observations, public release data and CSV stay unchanged.
export function changeView(
  current: string | null,
  previous: string | null,
  options: ChangeOptions,
) {
  const result = change(current, previous);
  const coverage =
    options.scope === 'included-chapters'
      ? ' for one or more included chapters'
      : '';
  const reason =
    current === null
      ? `Current value unavailable${coverage}`
      : !options.priorYearIncluded
        ? 'Prior-year month is not included in this release'
        : previous === null
          ? `Prior-year value unavailable${coverage}`
          : result.percent === null
            ? 'Percentage undefined from zero baseline'
            : null;
  return { ...result, reason };
}
