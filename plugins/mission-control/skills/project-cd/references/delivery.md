# Container and Helm delivery patterns

Use only the sections the repository needs. Replace every angle-bracket placeholder from the delivery brief.

## Contents

- Dockerfiles
- Chart values
- Deployment template
- Service template
- Release workflow
- Rollback and smoke

## Dockerfiles

### Go

```dockerfile
FROM golang:<version> AS build
WORKDIR /src
COPY go.mod go.sum ./
RUN go mod download
COPY . .
RUN CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/<binary> ./cmd/<binary>

FROM gcr.io/distroless/static:nonroot
COPY --from=build /out/<binary> /<binary>
USER nonroot:nonroot
EXPOSE <port>
ENTRYPOINT ["/<binary>"]
```

### Node

```dockerfile
FROM node:<version>-bookworm-slim AS build
WORKDIR /app
COPY package.json <lockfile> ./
RUN <pm> install --frozen-lockfile
COPY . .
RUN <pm> run build

FROM node:<version>-bookworm-slim
WORKDIR /app
ENV NODE_ENV=production
COPY --from=build /app/package.json <lockfile> ./
RUN <pm> install --prod --frozen-lockfile
COPY --from=build /app/dist ./dist
USER node
EXPOSE <port>
CMD ["node", "dist/index.js"]
```

Use the package manager and output directory the repository actually uses. Do not copy `node_modules` from the builder.

### Python

```dockerfile
FROM python:<version>-slim AS build
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN pip install uv && uv sync --frozen --no-dev

FROM python:<version>-slim
WORKDIR /app
COPY --from=build /app/.venv ./.venv
COPY src ./src
ENV PATH="/app/.venv/bin:$PATH"
USER <non-root-user>
EXPOSE <port>
CMD ["python", "-m", "<package>"]
```

Create the non-root user in the final image when the base image does not provide one. Never bake `.env` or credentials.

### Swift server

Use a Swift runtime image only when the project is a server executable:

```dockerfile
FROM swift:<version> AS build
WORKDIR /src
COPY Package.swift Package.resolved ./
RUN swift package resolve
COPY . .
RUN swift build -c release

FROM swift:<version>-slim
COPY --from=build /src/.build/release/<binary> /usr/local/bin/<binary>
USER <non-root-user>
ENTRYPOINT ["/usr/local/bin/<binary>"]
```

An iOS app has no container/chart delivery profile; stop and ask for the Apple distribution path instead.

## Chart values

```yaml
replicaCount: 1

image:
  repository: <image-repository>
  tag: ""
  pullPolicy: IfNotPresent

imagePullSecrets: []
nameOverride: ""
fullnameOverride: ""

serviceAccount:
  create: true
  name: ""

podAnnotations: {}
podSecurityContext:
  runAsNonRoot: true
  seccompProfile:
    type: RuntimeDefault

securityContext:
  allowPrivilegeEscalation: false
  readOnlyRootFilesystem: true
  capabilities:
    drop: ["ALL"]

service:
  type: ClusterIP
  port: <service-port>

containerPort: <container-port>

resources:
  requests:
    cpu: <request>
    memory: <request>
  limits:
    memory: <limit>

livenessProbe:
  httpGet:
    path: <health-path>
    port: http
  initialDelaySeconds: 10
  periodSeconds: 20

readinessProbe:
  httpGet:
    path: <ready-path>
    port: http
  initialDelaySeconds: 2
  periodSeconds: 5

env: []
envFrom: []

podDisruptionBudget:
  enabled: false
```

Add `ingress` only when a real host, class and TLS secret are supplied. Add persistence only when the application
actually owns durable local state; prefer an external service.

## Deployment template

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ include "<name>.fullname" . }}
  labels:
    {{- include "<name>.labels" . | nindent 4 }}
spec:
  replicas: {{ .Values.replicaCount }}
  selector:
    matchLabels:
      {{- include "<name>.selectorLabels" . | nindent 6 }}
  template:
    metadata:
      labels:
        {{- include "<name>.selectorLabels" . | nindent 8 }}
      {{- with .Values.podAnnotations }}
      annotations:
        {{- toYaml . | nindent 8 }}
      {{- end }}
    spec:
      {{- with .Values.imagePullSecrets }}
      imagePullSecrets:
        {{- toYaml . | nindent 8 }}
      {{- end }}
      securityContext:
        {{- toYaml .Values.podSecurityContext | nindent 8 }}
      containers:
        - name: {{ .Chart.Name }}
          image: "{{ .Values.image.repository }}:{{ required "image.tag is required" .Values.image.tag }}"
          imagePullPolicy: {{ .Values.image.pullPolicy }}
          securityContext:
            {{- toYaml .Values.securityContext | nindent 12 }}
          ports:
            - name: http
              containerPort: {{ .Values.containerPort }}
              protocol: TCP
          {{- with .Values.env }}
          env:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          {{- with .Values.envFrom }}
          envFrom:
            {{- toYaml . | nindent 12 }}
          {{- end }}
          livenessProbe:
            {{- toYaml .Values.livenessProbe | nindent 12 }}
          readinessProbe:
            {{- toYaml .Values.readinessProbe | nindent 12 }}
          resources:
            {{- toYaml .Values.resources | nindent 12 }}
```

The exact helper names come from the chart's `_helpers.tpl`. Do not paste this template without renaming them.

## Service template

```yaml
apiVersion: v1
kind: Service
metadata:
  name: {{ include "<name>.fullname" . }}
  labels:
    {{- include "<name>.labels" . | nindent 4 }}
spec:
  type: {{ .Values.service.type }}
  ports:
    - port: {{ .Values.service.port }}
      targetPort: http
      protocol: TCP
      name: http
  selector:
    {{- include "<name>.selectorLabels" . | nindent 4 }}
```

## Release workflow

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

jobs:
  release:
    runs-on: <runner-labels>
    env:
      IMAGE: <image-repository>
      RELEASE: <release-name>
      NAMESPACE: <namespace>
      EXPECTED_CONTEXT: <kubectl-context>
    steps:
      - uses: actions/checkout@v4

      - name: Resolve image tags
        id: tags
        run: |
          version="${GITHUB_REF_NAME#v}"
          sha="$(git rev-parse --short=7 HEAD)"
          echo "version=$version" >> "$GITHUB_OUTPUT"
          echo "sha=$sha" >> "$GITHUB_OUTPUT"

      - name: Log in to GHCR
        run: echo "${{ secrets.GITHUB_TOKEN }}" | docker login ghcr.io -u "${{ github.actor }}" --password-stdin

      - name: Build and push
        run: |
          docker build -t "$IMAGE:${{ steps.tags.outputs.version }}" .
          docker push "$IMAGE:${{ steps.tags.outputs.version }}"
          docker build -t "$IMAGE:sha-${{ steps.tags.outputs.sha }}" .
          docker push "$IMAGE:sha-${{ steps.tags.outputs.sha }}"

      - name: Check cluster context
        run: test "$(kubectl config current-context)" = "$EXPECTED_CONTEXT"

      - name: Deploy
        run: |
          helm upgrade --install "$RELEASE" deploy/helm/<name> \
            --namespace "$NAMESPACE" --create-namespace \
            --atomic --wait --timeout <duration> \
            --set image.repository="$IMAGE" \
            --set image.tag="${{ steps.tags.outputs.version }}"

      - name: Smoke
        run: <smoke-command>
```

- Use `GITHUB_TOKEN` only for GHCR. Cluster access comes from the self-hosted runner.
- `--atomic` rolls back a failed upgrade; `--wait` makes the job fail on an unhealthy rollout.
- The smoke command must be real and must fail non-zero. If there is no smoke endpoint, make one before adding CD.
- A multi-arch image requires a buildx step and a runner that can emulate or build both architectures; do not claim it
  without configuring it.
- This workflow deploys automatically on a tag, as requested. Do not add a production approval step unless the delivery
  brief changes.

## Rollback and smoke

- `--atomic` is the first rollback. Verify it is present in the workflow.
- A failed smoke check marks the workflow failed after the upgrade; roll back manually with
  `helm rollback <release> <previous-revision> -n <namespace>` if the release was allowed to complete.
- `kubectl rollout status deployment/<name> -n <namespace> --timeout=<duration>` is a useful extra guard when the chart's
  deployment name is known.
- Never run a rollback against production during skill validation.
