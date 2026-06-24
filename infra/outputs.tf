output "flow_arn" {
  value = awscc_mediaconnect_flow.srt_listener.flow_arn
}

output "flow_name" {
  value = awscc_mediaconnect_flow.srt_listener.name
}

output "source_ingest_ip" {
  value = awscc_mediaconnect_flow.srt_listener.source.ingest_ip
}

output "source_ingest_port" {
  value = awscc_mediaconnect_flow.srt_listener.source.ingest_port
}