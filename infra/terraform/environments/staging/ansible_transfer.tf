locals {
  ansible_transfer_bucket_name = "${local.name_prefix}-ansible-transfer-${data.aws_caller_identity.current.account_id}-${var.region}"
}

resource "aws_s3_bucket" "ansible_transfer" {
  bucket = local.ansible_transfer_bucket_name

  tags = merge(local.common_tags, {
    Name    = local.ansible_transfer_bucket_name
    Purpose = "ansible-ssm-transfer"
  })
}

resource "aws_s3_bucket_public_access_block" "ansible_transfer" {
  bucket = aws_s3_bucket.ansible_transfer.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "ansible_transfer" {
  bucket = aws_s3_bucket.ansible_transfer.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_ownership_controls" "ansible_transfer" {
  bucket = aws_s3_bucket.ansible_transfer.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

# Avoid retaining sensitive temporary module payloads as object versions.
resource "aws_s3_bucket_versioning" "ansible_transfer" {
  bucket = aws_s3_bucket.ansible_transfer.id

  versioning_configuration {
    status = "Suspended"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "ansible_transfer" {
  bucket = aws_s3_bucket.ansible_transfer.id

  depends_on = [aws_s3_bucket_versioning.ansible_transfer]

  rule {
    id     = "expire-temporary-transfers"
    status = "Enabled"

    filter {}

    expiration {
      days = 1
    }
  }
}

resource "aws_s3_bucket_policy" "ansible_transfer" {
  bucket = aws_s3_bucket.ansible_transfer.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "DenyInsecureTransport"
      Effect    = "Deny"
      Principal = "*"
      Action    = "s3:*"
      Resource = [
        aws_s3_bucket.ansible_transfer.arn,
        "${aws_s3_bucket.ansible_transfer.arn}/*",
      ]
      Condition = {
        Bool = {
          "aws:SecureTransport" = "false"
        }
      }
    }]
  })
}

data "aws_iam_policy_document" "ansible_transfer" {
  statement {
    sid       = "ListAnsibleTransferBucket"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.ansible_transfer.arn]
  }

  statement {
    sid       = "ManageAnsibleTransferObjects"
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:PutObject", "s3:DeleteObject"]
    resources = ["${aws_s3_bucket.ansible_transfer.arn}/*"]
  }
}

resource "aws_iam_role_policy" "ansible_transfer" {
  for_each = {
    proxy    = aws_iam_role.proxy.id
    frontend = aws_iam_role.frontend.id
    backend  = aws_iam_role.backend.id
  }

  name   = "${local.name_prefix}-ansible-transfer"
  role   = each.value
  policy = data.aws_iam_policy_document.ansible_transfer.json
}
