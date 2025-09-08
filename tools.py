def calc_checksum(*fields):
    res = 0
    for item in fields:
        for i in item.encode("ascii"):
            res += int(i)
    return res
