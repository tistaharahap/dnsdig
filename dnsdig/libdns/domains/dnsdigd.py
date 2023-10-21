import copy
import time
from typing import Dict

import aiohttp
import asyncudp
import dns.message

from dnsdig.libshared.logging import logger


class DNSDigUDPServer:
    def __init__(self, host: str, port: int, socket: asyncudp.Socket | None = None):
        self.host = host
        self.port = port
        self.socket = socket

    # Taken from https://github.com/rthalley/dnspython/blob/master/examples/doh-json.py

    def make_rr(self, simple, rdata):
        csimple = copy.copy(simple)
        csimple["data"] = rdata.to_text()
        return csimple

    def flatten_rrset(self, rrs):
        simple = {"name": str(rrs.name), "type": rrs.rdtype}
        if len(rrs) > 0:
            simple["TTL"] = rrs.ttl
            return [self.make_rr(simple, rdata) for rdata in rrs]
        else:
            return [simple]

    def to_doh_simple(self, message: dns.message.Message):
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
                simple[k].extend(self.flatten_rrset(rrs))
        # we don't encode the ecs_client_subnet field
        return simple

    def from_doh_simple(self, simple, add_qr=False):
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

    @classmethod
    async def query_doh(cls, doh_question: Dict[str, str | int]):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dns.google/resolve", params=doh_question, allow_redirects=True) as resp:
                return await resp.json()

    async def start(self):
        if not self.socket:
            try:
                self.socket = await asyncudp.create_socket(local_addr=(self.host, self.port))
            except OSError:
                logger.error(f"Failed to bind to {self.host}:{self.port} - Address and port already in use")
                return

        while True:
            data, addr = await self.socket.recvfrom()

            start_time = time.time()

            data = dns.message.from_wire(data)

            response = self.to_doh_simple(message=data)
            questions = response.get("Question", [])
            if len(questions) == 0:
                continue
            question = questions[0]
            doh_question = {"name": question.get("name"), "type": question.get("type")}
            logger.info(f"[{data.id}] Received query from {addr} - {question.get('name')} {question.get('type')}")

            try:
                doh_response = await DNSDigUDPServer.query_doh(doh_question=doh_question)
            except Exception as exc:
                logger.error(f"[{data.id}] Failed to query DoH - {exc}")
                continue

            dns_response = self.from_doh_simple(simple=doh_response, add_qr=True)
            dns_response.id = data.id

            end_time = time.time()
            delta = (end_time - start_time) * 1000
            logger.info(f"[{data.id}] Query took {delta} ms")

            logger.info(f"[{data.id}] Sending response to {addr} - {question.get('name')} {question.get('type')}")
            self.socket.sendto(dns_response.to_wire(), addr)
