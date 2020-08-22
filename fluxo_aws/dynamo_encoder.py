from decimal import Decimal


def dynamo_encoder(d):
    for k, v in d.items():
        if isinstance(v, dict):
            iterdict(v)
        else:
            if type(v) == float:
                v = Decimal(v)
            d.update({k: v})
    return d
