#############################################
# Terraform Configuration
#############################################

terraform {
  required_version = ">= 1.5"

  required_providers {
    # AWSCC provider is used for MediaConnect Flow
    awscc = {
      source  = "hashicorp/awscc"
      version = "~> 1.0"
    }

    # AWS provider is used for IAM + MediaLive
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

#############################################
# Providers
#############################################

provider "awscc" {
  region = var.aws_region
}

provider "aws" {
  region = var.aws_region
}

#############################################
# Existing MediaLiveAccessRole
#
# This is the same IAM role that works when i manually create the MediaLive input
# from the AWS API Console.
#############################################

data "aws_iam_role" "medialive_access_role" {
  name = "MediaLiveAccessRole"
}

#############################################
# AWS MediaConnect Flow
#
# Architecture:
# OBS / FFmpeg SRT Caller
#     ↓
# MediaConnect SRT Listener Flow
#############################################

resource "awscc_mediaconnect_flow" "srt_listener" {
  name = var.flow_name

  source = {
    name           = "srt-listener-source"
    description    = "OBS SRT caller input into MediaConnect"
    protocol       = "srt-listener"
    ingest_port    = var.srt_port
    min_latency    = 2000
    whitelist_cidr = "0.0.0.0/0"
  }
}

#############################################
# AWS MediaLive Input
#
# Architecture:
# MediaConnect Flow
#     ↓
# MediaLive Input Type = MEDIACONNECT
#
# Important: use the existing MediaLiveAccessRole
# because manual AWS API Console creation works with this role.
#############################################

resource "aws_medialive_input" "mediaconnect_input" {
  name     = "obs-mediaconnect-input"
  type     = "MEDIACONNECT"
  role_arn = data.aws_iam_role.medialive_access_role.arn

  media_connect_flows {
    flow_arn = awscc_mediaconnect_flow.srt_listener.flow_arn
  }
}

#############################################
# MediaPackage V1 Channel
#############################################

resource "aws_media_package_channel" "mp_v1_channel" {
  channel_id  = "tf-lab-mp-v1-channel"
  description = "MediaPackage V1 channel for Terraform MediaLive HLS and DASH lab"
}

#############################################
# MediaLive Channel - ABR Ladder Output
#############################################

resource "aws_medialive_channel" "channel" {
  name          = "tf-lab-medialive-channel"
  channel_class = "SINGLE_PIPELINE"
  role_arn      = data.aws_iam_role.medialive_access_role.arn

  input_specification {
    codec            = "AVC"
    input_resolution = "HD"
    maximum_bitrate  = "MAX_20_MBPS"
  }

  input_attachments {
    input_attachment_name = "mediaconnect-input"
    input_id              = aws_medialive_input.mediaconnect_input.id
  }

  destinations {
    id = "mediapackage-destination"

    media_package_settings {
      channel_id = aws_media_package_channel.mp_v1_channel.id
    }
  }

  encoder_settings {
    timecode_config {
      source = "EMBEDDED"
    }

    audio_descriptions {
      name                = "audio_1"
      audio_selector_name = "default"

      codec_settings {
        aac_settings {
          bitrate           = 128000
          coding_mode       = "CODING_MODE_2_0"
          input_type        = "NORMAL"
          profile           = "LC"
          rate_control_mode = "CBR"
          raw_format        = "NONE"
          sample_rate       = 48000
          spec              = "MPEG4"
        }
      }
    }

    # 720p60 rendition
    video_descriptions {
      name   = "video_720p60"
      width  = 1920
      height = 1080

      codec_settings {
        h264_settings {
          bitrate               = 4500000
          framerate_control     = "SPECIFIED"
          framerate_numerator   = 60
          framerate_denominator = 1
          gop_size              = 2
          gop_size_units        = "SECONDS"
          profile               = "HIGH"
          rate_control_mode     = "CBR"
          scan_type             = "PROGRESSIVE"
          scene_change_detect   = "ENABLED"
          timecode_insertion    = "DISABLED"

          par_control     = "SPECIFIED"
          par_numerator   = 1
          par_denominator = 1
        }
      }
    }

    # 720p30 rendition
    video_descriptions {
      name   = "video_720p30"
      width  = 1280
      height = 720

      codec_settings {
        h264_settings {
          bitrate               = 3000000
          framerate_control     = "SPECIFIED"
          framerate_numerator   = 30
          framerate_denominator = 1
          gop_size              = 2
          gop_size_units        = "SECONDS"
          profile               = "MAIN"
          rate_control_mode     = "CBR"
          scan_type             = "PROGRESSIVE"
          scene_change_detect   = "ENABLED"
          timecode_insertion    = "DISABLED"

          par_control     = "SPECIFIED"
          par_numerator   = 1
          par_denominator = 1
        }
      }
    }

    # 480p rendition
    video_descriptions {
      name   = "video_480p30"
      width  = 854
      height = 480

      codec_settings {
        h264_settings {
          bitrate               = 1500000
          framerate_control     = "SPECIFIED"
          framerate_numerator   = 30
          framerate_denominator = 1
          gop_size              = 2
          gop_size_units        = "SECONDS"
          profile               = "MAIN"
          rate_control_mode     = "CBR"
          scan_type             = "PROGRESSIVE"
          scene_change_detect   = "ENABLED"
          timecode_insertion    = "DISABLED"

          par_control     = "SPECIFIED"
          par_numerator   = 1
          par_denominator = 1
        }
      }
    }

    # 360p rendition
    video_descriptions {
      name   = "video_360p30"
      width  = 640
      height = 360

      codec_settings {
        h264_settings {
          bitrate               = 700000
          framerate_control     = "SPECIFIED"
          framerate_numerator   = 30
          framerate_denominator = 1
          gop_size              = 2
          gop_size_units        = "SECONDS"
          profile               = "MAIN"
          rate_control_mode     = "CBR"
          scan_type             = "PROGRESSIVE"
          scene_change_detect   = "ENABLED"
          timecode_insertion    = "DISABLED"

          par_control     = "SPECIFIED"
          par_numerator   = 1
          par_denominator = 1
        }
      }
    }

    output_groups {
      name = "mediapackage-output-group"

      output_group_settings {
        media_package_group_settings {
          destination {
            destination_ref_id = "mediapackage-destination"
          }
        }
      }

      outputs {
        output_name             = "emp_720p60"
        video_description_name  = "video_720p60"
        audio_description_names = ["audio_1"]

        output_settings {
          media_package_output_settings {}
        }
      }

      outputs {
        output_name             = "emp_720p30"
        video_description_name  = "video_720p30"
        audio_description_names = ["audio_1"]

        output_settings {
          media_package_output_settings {}
        }
      }

      outputs {
        output_name             = "emp_480p30"
        video_description_name  = "video_480p30"
        audio_description_names = ["audio_1"]

        output_settings {
          media_package_output_settings {}
        }
      }

      outputs {
        output_name             = "emp_360p30"
        video_description_name  = "video_360p30"
        audio_description_names = ["audio_1"]

        output_settings {
          media_package_output_settings {}
        }
      }
    }
  }

  depends_on = [
    aws_medialive_input.mediaconnect_input,
    aws_media_package_channel.mp_v1_channel
  ]
}

#############################################
# MediaPackage v1 HLS Origin Endpoint
# through cloudformation as Terraform provider doesn't support AWS and AWSCC mediapackag v1 endpoint
#############################################
resource "aws_cloudformation_stack" "mp_v1_hls_endpoint" {
  name = "tf-lab-mp-v1-hls-endpoint"

  template_body = jsonencode({
    AWSTemplateFormatVersion = "2010-09-09"
    Resources = {
      HlsEndpoint = {
        Type = "AWS::MediaPackage::OriginEndpoint"
        Properties = {
          Id        = "hls"
          ChannelId = aws_media_package_channel.mp_v1_channel.id

          HlsPackage = {
            SegmentDurationSeconds = 6
            PlaylistWindowSeconds  = 60
            PlaylistType           = "EVENT"
          }
        }
      }
    }
  })
}

# -------------------------------------------------------------------
# MediaPackage V1 DASH Origin Endpoint
# -------------------------------------------------------------------
# Why CloudFormation instead of Terraform provider?

# We are using AWS Elemental MediaPackage V1. The Terraform AWS provider currently supports the MediaPackage V1
# channel resource, but the native Terraform origin endpoint resource was not available/supported in our provider setup.
#
# Earlier, Terraform returned: invalid resource type: aws_media_package_origin_endpoint
#
# So instead of manually creating the endpoint in AWS Console, we keep it automated as IaC by embedding an AWS CloudFormation stack inside Terraform.
#
# Terraform still manages the lifecycle of this endpoint through:
#   aws_cloudformation_stack.mp_v1_dash_endpoint
#
# -------------------------------------------------------------------

resource "aws_cloudformation_stack" "mp_v1_dash_endpoint" {
  name = "tf-mediapackage-v1-dash-endpoint"

  template_body = jsonencode({
    AWSTemplateFormatVersion = "2010-09-09"
    Description              = "MediaPackage V1 DASH origin endpoint created through CloudFormation because Terraform AWS provider does not support the V1 origin endpoint resource in this lab."

    Resources = {
      DashOriginEndpoint = {
        Type = "AWS::MediaPackage::OriginEndpoint"

        Properties = {
          Id        = "tf-v1-dash-endpoint"
          ChannelId = aws_media_package_channel.mp_v1_channel.id

          Description  = "DASH endpoint for Terraform MediaPackage V1 lab"
          ManifestName = "index"

          DashPackage = {
            SegmentDurationSeconds            = 2
            MinBufferTimeSeconds              = 30
            MinUpdatePeriodSeconds            = 15
            SuggestedPresentationDelaySeconds = 25
            Profile                           = "NONE"
          }
        }
      }
    }

    Outputs = {
      DashEndpointUrl = {
        Description = "MediaPackage V1 DASH endpoint URL"
        Value       = { "Fn::GetAtt" = ["DashOriginEndpoint", "Url"] }
      }
    }
  })
}