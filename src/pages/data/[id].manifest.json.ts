import { release, publicManifest } from '../../lib/data';
export function getStaticPaths() {
  return [{ params: { id: release.id } }];
}
export function GET() {
  return new Response(JSON.stringify(publicManifest), {
    headers: { 'Content-Type': 'application/json; charset=utf-8' },
  });
}
