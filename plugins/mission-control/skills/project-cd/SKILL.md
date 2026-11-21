---
name: project-cd
description: Adds container and Kubernetes delivery to a repository: writes a Dockerfile and Helm chart, adds a v* tag workflow that builds and pushes the image and deploys with Helm, and validates the chart and workflow locally. Use when a project needs release, image publishing, a Helm chart, tag-driven deployment, or a deployment repair. Not for creating a repository or CI-only checks; use project-init and project-ci.
---

# Add delivery

Delivery is one repeatable release path: a tag builds an immutable image, Helm applies it, and the deployment is checked
or rolled back. This skill writes and validates that path; it does not deploy during validation and does not create the
git tag unless the person asks for a release.

## 1. Read the repository

Read `AGENTS.md`, the existing Dockerfile, charts and workflows before writing:

```bash
git status --short --branch
find deploy .github/workflows -maxdepth 4 -type f 2>/dev/null
find . -maxdepth 3 -iname 'Dockerfile*' -o -iname 'Chart.yaml' 2>/dev/null
helm version
docker version
kubectl config current-context
```

Report what exists. Never replace an existing Dockerfile, chart or release workflow without reading it and saying what
you are changing.

## 2. Ask for the delivery brief

Ask once, together:

- image repository and name (for example `ghcr.io/<owner>/<slug>`);
- chart name and release name;
- Kubernetes namespace and expected `kubectl` context;
- runner labels, including whether it already has cluster access;
- image pull secret already present in the namespace, if the package is private;
- smoke command or URL that proves the deployment works;
- tag pattern, default `v*`.

There are no deployment secrets in the repository. The image registry uses `GITHUB_TOKEN` in Actions; the cluster comes
from the chosen self-hosted runner. If the runner has no cluster access, stop and change the delivery brief rather than
inventing a kubeconfig secret.

## 3. Write the container image

If the repository has no Dockerfile, create a multi-stage, production-shaped one for its stack. Guidance and examples:
[references/delivery.md](references/delivery.md).

- Build dependencies in a builder stage; copy only runtime artifacts into the final image.
- Run as a non-root user when the runtime supports it.
- No secrets in build arguments or layers; no `.env`, local database or generated dependency directories.
- One `HEALTHCHECK`-equivalent application endpoint is better than a shell test that needs extra tools.
- `.dockerignore` includes `.git`, dependency caches, build output, local environments and test artifacts.
- The image listens on a configurable port; the chart wires it.

Verify locally when Docker is available:

```bash
docker build -t <image>:local .
```

An unavailable Docker daemon is reported as **image not built locally**, not as a pass.

## 4. Write the Helm chart

Create `deploy/helm/<name>` with a real chart, not an empty placeholder:

- `Chart.yaml` — name, description, type, version, appVersion.
- `values.yaml` — image repository/tag/pullPolicy, replicas, container port, service port/type, resources, probes, env,
  existing secret references and imagePullSecrets.
- `templates/deployment.yaml` — labels/selectors from the chart, rolling update, non-root security context, probes,
  resource requests/limits, env and envFrom.
- `templates/service.yaml` — only when the workload is reachable.
- `templates/ingress.yaml` — only when the brief names a host and ingress class; no invented domain.
- `templates/_helpers.tpl` — names, labels and image reference.
- `NOTES.txt` — how to reach the deployment.
- Optional migration Job, hook or initContainer only when the application actually has one.

Do not put registry or cluster credentials in `values.yaml`. A private registry uses an existing imagePullSecret name.
Do not add a `ServiceMonitor`, PVC or ingress the brief did not request.

Validate:

```bash
helm lint deploy/helm/<name>
helm template <release> deploy/helm/<name> --namespace <namespace> >/tmp/<name>-rendered.yaml
```

Inspect that the rendered image tag and pull policy are what the workflow will set.

## 5. Write the tag workflow

Create `.github/workflows/release.yml`; a single tag run builds the image, pushes it and deploys. Tag deployment is
automatic by the delivery brief; do not add an approval gate the person did not ask for.

Required properties:

```yaml
name: Release
on:
  push:
    tags: ["v*"]
permissions:
  contents: read
  packages: write
concurrency:
  group: release-${{ github.ref }}
  cancel-in-progress: false
```

The release job:

1. checks out the tag and verifies the version from `GITHUB_REF_NAME`;
2. logs in to GHCR with `GITHUB_TOKEN` and the actor;
3. builds and pushes `semver` and `sha-<short>` tags; never pushes `latest`;
4. verifies `kubectl config current-context` equals the expected context;
5. runs `helm upgrade --install <release> deploy/helm/<name> --namespace <namespace> --create-namespace --atomic --wait
   --timeout <duration> --set image.repository=<repo> --set image.tag=<version>`;
6. runs the smoke command and reports failure;
7. relies on `--atomic` to roll back a failed release.

Use the runner labels from the brief. Do not assume `ubuntu-latest` has cluster access. If the image build and the
deployment need different runners, use two jobs with `needs:`; keep the image tag passed as an output. The workflow must
not run on pull requests, branches or `workflow_dispatch` unless the person asks for a manual path.

## 6. Validate without deploying

```bash
docker build -t <image>:local .          # when Docker is available
helm lint deploy/helm/<name>
helm template <release> deploy/helm/<name> --namespace <namespace> >/tmp/rendered.yaml
actionlint .github/workflows/release.yml  # when actionlint is installed
git diff --check
```

Do not run `helm upgrade`, `kubectl apply` or a smoke check against a real cluster during validation. A local render is
not a deployment.

## 7. Finish

- Commit the Dockerfile, chart, workflow and the `AGENTS.md` delivery section.
- Push the commit when the repository has a remote and the person asked for CD.
- Do not create or push `v*` unless the person asked to release; the tag is the production action.
- Report the image repository, chart path, workflow trigger, runner, namespace/context, smoke command, validation result,
  and the exact release command the person should use.
