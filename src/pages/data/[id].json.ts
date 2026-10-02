import { release } from '../../lib/data';
export function getStaticPaths() {
  return [{ params: { id: release.id } }];
}
export function GET() {
  return new Response(JSON.stringify(release), {
    headers: { 'Content-Type': 'application/json' },
  });
}
