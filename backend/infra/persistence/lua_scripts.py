
class LuaScripts:
    # ATOMIC_FLAG: Increment flags.
    # KEYS[1] = intent key
    # ARGV[1] = flag_increment (usually 1)
    ATOMIC_FLAG = """
    if redis.call("EXISTS", KEYS[1]) == 1 then
        local current = redis.call("GET", KEYS[1])
        local intent = cjson.decode(current)
        intent['flags'] = intent['flags'] + tonumber(ARGV[1])
        local new_json = cjson.encode(intent)
        local ttl = redis.call("TTL", KEYS[1])
        if ttl > 0 then
            redis.call("SET", KEYS[1], new_json, "EX", ttl)
        else
            redis.call("SET", KEYS[1], new_json, "EX", 86400)
        end
        return intent['flags']
    else
        return 0
    end
    """

    # SAVE_JOIN: Add user to set if intent exists.
    # KEYS[1] = intent key
    # KEYS[2] = join key
    # ARGV[1] = user_id
    SAVE_JOIN = """
    if redis.call("EXISTS", KEYS[1]) == 1 then
        local added = redis.call("SADD", KEYS[2], ARGV[1])
        local ttl = redis.call("TTL", KEYS[1])
        if ttl > 0 then
            redis.call("EXPIRE", KEYS[2], ttl)
        end
        return added
    else
        return -1
    end
    """
