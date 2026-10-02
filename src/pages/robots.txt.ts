export function GET() {
  return new Response(
    'User-agent: *\nDisallow:\n# Development preview: HTML pages carry noindex. Do not block crawlers from reading it.\n',
  );
}
