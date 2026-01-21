from redis import Redis


def create_redis_client(host: str, port: int = 6390) -> Redis:
    return Redis(host=host, port=port, decode_responses=True)
