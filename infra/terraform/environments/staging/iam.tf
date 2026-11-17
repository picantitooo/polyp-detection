data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "proxy" {
  name               = "${local.name_prefix}-proxy"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-proxy"
    Role = "proxy"
  })
}

resource "aws_iam_role" "frontend" {
  name               = "${local.name_prefix}-frontend"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-frontend"
    Role = "frontend"
  })
}

resource "aws_iam_role" "backend" {
  name               = "${local.name_prefix}-backend"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-backend"
    Role = "backend"
  })
}

resource "aws_iam_instance_profile" "proxy" {
  name = "${local.name_prefix}-proxy"
  role = aws_iam_role.proxy.name
  tags = local.common_tags
}

resource "aws_iam_instance_profile" "frontend" {
  name = "${local.name_prefix}-frontend"
  role = aws_iam_role.frontend.name
  tags = local.common_tags
}

resource "aws_iam_instance_profile" "backend" {
  name = "${local.name_prefix}-backend"
  role = aws_iam_role.backend.name
  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ssm" {
  for_each = {
    proxy    = aws_iam_role.proxy.name
    frontend = aws_iam_role.frontend.name
    backend  = aws_iam_role.backend.name
  }

  role       = each.value
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy_attachment" "ecr_read_only" {
  for_each = {
    frontend = aws_iam_role.frontend.name
    backend  = aws_iam_role.backend.name
  }

  role       = each.value
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

data "aws_iam_policy_document" "backend_models" {
  statement {
    sid       = "ListModelBucket"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = [aws_s3_bucket.models.arn]
  }

  statement {
    sid       = "ReadModelObjects"
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.models.arn}/*"]
  }
}

resource "aws_iam_role_policy" "backend_models" {
  name   = "${local.name_prefix}-backend-models"
  role   = aws_iam_role.backend.id
  policy = data.aws_iam_policy_document.backend_models.json
}
