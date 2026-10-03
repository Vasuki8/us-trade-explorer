import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync, readdirSync } from 'node:fs';
import { parseDocument } from 'yaml';

const directory = new URL('../.github/workflows/', import.meta.url);
const workflows = readdirSync(directory)
  .filter((name) => name.endsWith('.yml'))
  .map((name) => {
    const document = parseDocument(
      readFileSync(new URL(name, directory), 'utf8'),
    );
    assert.deepEqual(document.errors, [], `Invalid workflow YAML: ${name}`);
    return { name, workflow: document.toJS() };
  });
const evidenceWorkflows = workflows.filter(({ name }) =>
  name.startsWith('census-'),
);

// Only this reviewed expression subset is permitted for the private-job boundary.
// No eval, credential context or arbitrary workflow code runs in these tests.
function allows(
  condition: unknown,
  ref: string,
  event: string,
  repository: Record<string, unknown> = {},
) {
  assert.equal(
    typeof condition,
    'string',
    'Private job needs an explicit condition',
  );
  return (condition as string).split(/\s*&&\s*/).every((clause) => {
    if (clause === "github.ref == 'refs/heads/main'")
      return ref === 'refs/heads/main';
    if (clause === "github.event_name == 'workflow_dispatch'")
      return event === 'workflow_dispatch';
    if (clause === "toJSON(github.event.repository.private) == 'true'") {
      // GitHub represents missing property access as an empty string.
      return JSON.stringify(repository.private ?? '') === 'true';
    }
    assert.fail(`Unreviewed private-job expression: ${clause}`);
  });
}

for (const { name, workflow } of evidenceWorkflows) {
  test(`${name}: public or unknown repository cannot generate private evidence`, () => {
    for (const [jobName, job] of Object.entries<any>(workflow.jobs)) {
      for (const repository of [
        { private: false },
        {},
        { private: null },
        { private: 'true' },
        { private: 1 },
      ]) {
        assert.equal(
          allows(job.if, 'refs/heads/main', 'workflow_dispatch', repository),
          false,
          jobName,
        );
      }
    }
  });

  test(`${name}: private main manual route remains available; PRs and other branches do not`, () => {
    assert.deepEqual(Object.keys(workflow.on), ['workflow_dispatch']);
    assert.ok(Object.keys(workflow.jobs).length > 0);
    for (const [jobName, job] of Object.entries<any>(workflow.jobs)) {
      assert.equal(
        allows(job.if, 'refs/heads/main', 'workflow_dispatch', {
          private: true,
        }),
        true,
        jobName,
      );
      for (const event of [
        'pull_request',
        'pull_request_target',
        'workflow_run',
        'push',
        'schedule',
      ]) {
        assert.equal(
          allows(job.if, 'refs/heads/main', event, { private: true }),
          false,
          jobName,
        );
      }
      for (const ref of [
        'refs/heads/feature',
        'refs/pull/32/merge',
        'refs/tags/main',
        '',
      ]) {
        assert.equal(
          allows(job.if, ref, 'workflow_dispatch', { private: true }),
          false,
          jobName,
        );
      }
      assert.equal(job.environment, 'census-ingestion');
      assert.equal(job['timeout-minutes'], 20);
    }
  });
}

test('every secret-consuming job or Census evidence upload is behind the private boundary', () => {
  assert.equal(evidenceWorkflows.length, 5);
  let privateJobs = 0;
  for (const { name, workflow } of workflows) {
    for (const job of Object.values<any>(workflow.jobs)) {
      const content = JSON.stringify(job);
      if (
        !content.includes('secrets.CENSUS_API_KEY') &&
        !content.includes('pipeline/output/')
      )
        continue;
      privateJobs++;
      assert.ok(
        name.startsWith('census-'),
        `Private evidence appeared in ${name}`,
      );
      assert.equal(
        allows(job.if, 'refs/heads/main', 'workflow_dispatch', {
          private: false,
        }),
        false,
        name,
      );
      assert.equal(
        allows(job.if, 'refs/heads/main', 'pull_request_target', {
          private: true,
        }),
        false,
        name,
      );
      for (const step of job.steps) {
        if (step.uses)
          assert.match(
            step.uses,
            /@[a-f0-9]{40}$/,
            `${name}: Action must use full SHA`,
          );
        if (step.uses?.startsWith('actions/checkout@'))
          assert.equal(step.with['persist-credentials'], false);
      }
      const permissions = job.permissions ?? workflow.permissions;
      assert.ok(
        permissions &&
          Object.values(permissions).every(
            (permission) => permission === 'read',
          ),
      );
      assert.equal(workflow.env?.CENSUS_API_KEY, undefined);
    }
  }
  assert.equal(privateJobs, 5);
});

test('public verification and sample-preview jobs stay credential-free and available', () => {
  for (const name of ['checks.yml', 'github-preview.yml']) {
    const workflow = workflows.find((entry) => entry.name === name)!.workflow;
    assert.ok(!JSON.stringify(workflow).includes('secrets.CENSUS_API_KEY'));
    assert.ok(!JSON.stringify(workflow).includes('pipeline/output/'));
  }
  const preview = workflows.find(
    ({ name }) => name === 'github-preview.yml',
  )!.workflow;
  assert.equal(preview.jobs.build.if, "github.ref == 'refs/heads/main'");
  const upload = preview.jobs.build.steps.find((step: any) =>
    step.uses?.startsWith('actions/upload-artifact@'),
  );
  assert.equal(upload.with.path, 'dist/');
  assert.ok(
    !/private/i.test(upload.name),
    'Publicly readable sample artifact must not claim privacy',
  );
});
