import { release } from '../../lib/data';
import { csv } from '../../../packages/contracts/trade';
export function getStaticPaths() {
  return [{ params: { id: release.id } }];
}
export function GET() {
  return new Response(csv(release, release.observations), {
    headers: { 'Content-Type': 'text/csv;charset=utf-8' },
  });
}
