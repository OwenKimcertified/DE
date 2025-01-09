{{- define "my-airflow.name" -}}
{{- include "my-airflow.fullname" . | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "my-airflow.fullname" -}}
{{- if .Chart.Name }}
{{- .Chart.Name | replace " " "-" | lower -}}
{{- else -}}
my-airflow
{{- end -}}
{{- end -}}

{{- define "my-airflow.labels" -}}
app.kubernetes.io/name: {{ include "my-airflow.name" . }}
app.kubernetes.io/instance: {{ .Release.Name | quote }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}
