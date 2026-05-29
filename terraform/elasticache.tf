# -----------------------------------------------------------------------------
# elasticache.tf — the Redis cache used by Django for session storage
#
# I use ElastiCache Serverless (not a traditional cluster) for two reasons:
#   1. No cluster sizing or node count to manage — capacity scales automatically.
#   2. It matches the existing production setup (humanlikebotcache-5rqgxm),
#      making migration straightforward.
#
# ElastiCache Serverless always enforces TLS. The connection string I inject
# into the application uses the rediss:// scheme (double-s = TLS).
#
# I place it in private subnets and restrict access via the cache security
# group so only the application instances can connect.
#
# Note: unlike a traditional ElastiCache cluster, Serverless does NOT use an
# aws_elasticache_subnet_group resource — subnet IDs are passed directly.
# -----------------------------------------------------------------------------

resource "aws_elasticache_serverless_cache" "redis" {
  engine = "redis"
  name   = "${local.name_prefix}-redis"

  # I set a reasonable upper bound on storage and compute units.
  # Serverless starts near zero and scales up automatically within these limits.
  # 10 GB and 5000 eCPU/s are generous for a research chat application —
  # adjust upward if you see throttling in CloudWatch.
  cache_usage_limits {
    data_storage {
      maximum = 10
      unit    = "GB"
    }
    ecpu_per_second {
      maximum = 5000
    }
  }

  # Private subnets — no internet route, only reachable from app instances
  subnet_ids         = aws_subnet.private[*].id
  security_group_ids = [aws_security_group.cache.id]

  tags = local.common_tags
}

# -----------------------------------------------------------------------------
# Build the Redis connection URL that Django receives as the REDIS_URL
# environment variable. The rediss:// prefix (double-s) signals TLS.
# I define this as a local so both elasticbeanstalk.tf and outputs.tf can
# reference it without duplicating the string interpolation.
# -----------------------------------------------------------------------------

locals {
  redis_url = "rediss://${aws_elasticache_serverless_cache.redis.endpoint[0].address}:${aws_elasticache_serverless_cache.redis.endpoint[0].port}"
}
