provider "aws" {
  region = "eu-west-3" 
}

# buckets S3 
resource "aws_s3_bucket" "kafka_buckets" {
  for_each = toset(["kafka-ing-logs", "kafka-ing-transactions", "kafka-ing-social", "kafka-ing-campaigns"])
  bucket   = each.value
}

resource "aws_s3_bucket_versioning" "versioning" {
  for_each = aws_s3_bucket.kafka_buckets
  bucket   = each.value.bucket

  versioning_configuration {
    status = "Enabled"
  }
}

# role IAM pour Glue Crawler
resource "aws_iam_role" "glue_crawler_role" {
  name = "GlueCrawlerRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "glue.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_policy" "glue_crawler_policy" {
  name        = "GlueCrawlerPolicy"
  description = "Policy for Glue Crawler to access S3 and Glue resources"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = ["s3:GetObject", "s3:PutObject", "s3:ListBucket"]
        Resource = [
          "arn:aws:s3:::kafka-ing-*",
          "arn:aws:s3:::kafka-ing-*/*"
        ]
      },
      {
        Effect = "Allow"
        Action = "glue:*"
        Resource = "*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "glue_crawler_attach" {
  role       = aws_iam_role.glue_crawler_role.name
  policy_arn = aws_iam_policy.glue_crawler_policy.arn
}

# Glue Crawlers
resource "aws_glue_crawler" "kafka_crawlers" {
  for_each      = toset(["logs", "transactions", "social_data", "ad_campaigns"])
  name          = "${each.key}_crawler"
  database_name = "kafka_database"
  role          = aws_iam_role.glue_crawler_role.arn

  s3_target {
    path = "s3://kafka-ing-${each.key}/"
  }

  depends_on = [aws_s3_bucket.kafka_buckets]
}

# Groupe de sécurité pour SSH
resource "aws_security_group" "allow_ssh" {
  name_prefix = "allow_ssh"

  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# Instance EC2
resource "aws_instance" "kafka_instance" {
  ami           = "ami-12345678" 
  instance_type = "t2.micro"
  key_name      = "my-key.pem"     
  security_groups = [aws_security_group.allow_ssh.name]

  tags = {
    Name = "KafkaInstance"
  }
}


resource "null_resource" "wait_for_instance" {
  depends_on = [aws_instance.kafka_instance]

  provisioner "local-exec" {
    command = "sleep 60"
  }
}

resource "null_resource" "create_kafka_topics" {
  depends_on = [null_resource.wait_for_instance]

  provisioner "remote-exec" {
    connection {
      type        = "ssh"
      user        = "ec2-user" # Ou "ubuntu", selon l'AMI
      private_key = file("~/.ssh/id_rsa") # clé privé
      host        = aws_instance.kafka_instance.public_ip
    }

    inline = [
      "echo 'Creating Kafka Topics...'",
     
    ]
  }
}
