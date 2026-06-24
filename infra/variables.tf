#############################################
# AWS Region
#############################################

variable "aws_region" {
  description = "AWS Region"
  type        = string
}

#############################################
# MediaConnect Flow Name
#############################################

variable "flow_name" {
  description = "MediaConnect Flow Name"
  type        = string
}

#############################################
# SRT Port
#############################################

variable "srt_port" {
  description = "Port OBS will connect to"
  type        = number
}

