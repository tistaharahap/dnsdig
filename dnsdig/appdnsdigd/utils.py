import copy

import dns

# Taken from https://github.com/rthalley/dnspython/blob/master/examples/doh-json.py


def from_doh_simple(simple, add_qr=False):
    message = dns.message.QueryMessage()
    flags = 0
    for f in dns.flags.Flag:
        if simple.get(f.name, False):
            flags |= f
    if add_qr:  # QR is implied
        flags |= dns.flags.QR
    message.flags = flags
    message.set_rcode(simple.get("Status", 0))
    for i, sn in enumerate(dns.message.MessageSection):
        rr_list = simple.get(sn.name.title(), [])
        for rr in rr_list:
            rdtype = dns.rdatatype.RdataType(rr["type"])
            rrs = message.find_rrset(i, dns.name.from_text(rr["name"]), dns.rdataclass.IN, rdtype, create=True)
            if "data" in rr:
                rrs.add(dns.rdata.from_text(dns.rdataclass.IN, rdtype, rr["data"]), rr.get("TTL", 0))
    # we don't decode the ecs_client_subnet field
    return message


def make_rr(simple, rdata):
    csimple = copy.copy(simple)
    csimple["data"] = rdata.to_text()
    return csimple


def flatten_rrset(rrs):
    simple = {"name": str(rrs.name), "type": rrs.rdtype}
    if len(rrs) > 0:
        simple["TTL"] = rrs.ttl
        return [make_rr(simple, rdata) for rdata in rrs]
    else:
        return [simple]


def to_doh_simple(message: dns.message.Message):
    simple = {"Status": message.rcode()}
    for f in dns.flags.Flag:
        if f != dns.flags.Flag.AA and f != dns.flags.Flag.QR:
            # DoH JSON doesn't need AA and omits it.  DoH JSON is only
            # used in replies so the QR flag is implied.
            simple[f.name] = (message.flags & f) != 0
    for i, s in enumerate(message.sections):
        k = dns.message.MessageSection.to_text(i).title()
        simple[k] = []
        for rrs in s:
            simple[k].extend(flatten_rrset(rrs))
    # we don't encode the ecs_client_subnet field
    return simple
