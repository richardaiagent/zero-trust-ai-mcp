{{/*
infra/helm/mcp-platform/templates/_helpers.tpl
공통 헬퍼 템플릿
*/}}

{{- define "mcp.serviceTemplate" -}}
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {{ .name }}
  labels:
    app: {{ .name }}
    component: mcp-platform
spec:
  replicas: {{ .values.replicaCount }}
  selector:
    matchLabels:
      app: {{ .name }}
  template:
    metadata:
      labels:
        app: {{ .name }}
    spec:
      containers:
        - name: {{ .name }}
          image: "{{ .global.imageRegistry }}{{ .values.image.repository }}:{{ .values.image.tag }}"
          imagePullPolicy: {{ .global.imagePullPolicy }}
          ports:
            - containerPort: {{ .values.port }}
          envFrom:
            - secretRef:
                name: mcp-{{ .name }}-secret
          livenessProbe:
            httpGet:
              path: /health
              port: {{ .values.port }}
            initialDelaySeconds: 15
            periodSeconds: 20
          readinessProbe:
            httpGet:
              path: /health
              port: {{ .values.port }}
            initialDelaySeconds: 5
            periodSeconds: 10
          resources:
            {{- toYaml .values.resources | nindent 12 }}
---
apiVersion: v1
kind: Service
metadata:
  name: {{ .name }}
spec:
  selector:
    app: {{ .name }}
  ports:
    - port: {{ .values.port }}
      targetPort: {{ .values.port }}
{{- end }}
