# The result is sensitive by provider schema; never add a secret output.
resource "random_password" "turn" {
  length  = 64
  special = false
}

resource "aws_ssm_parameter" "turn_shared_secret" {
  name  = "/polyp/staging/turn/shared-secret"
  type  = "SecureString"
  tier  = "Standard"
  value = sensitive(random_password.turn.result)

  tags = merge(local.common_tags, {
    Purpose = "turn-shared-secret"
  })
}

data "aws_iam_policy_document" "turn_read" {
  statement {
    sid       = "ReadTurnSecret"
    effect    = "Allow"
    actions   = ["ssm:GetParameter"]
    resources = [aws_ssm_parameter.turn_shared_secret.arn]
  }
}

resource "aws_iam_role_policy" "turn_read" {
  for_each = {
    proxy   = aws_iam_role.proxy.id
    backend = aws_iam_role.backend.id
  }
  name   = "${local.name_prefix}-turn-read"
  role   = each.value
  policy = data.aws_iam_policy_document.turn_read.json
}

output "turn_parameter_name" {
  description = "Name of the TURN SecureString parameter; never its value."
  value       = aws_ssm_parameter.turn_shared_secret.name
}
