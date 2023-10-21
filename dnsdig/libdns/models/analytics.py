from datetime import datetime, timedelta
from enum import Enum
from typing import List

from dns.rdatatype import RdataType

from dnsdig.libshared.models import BaseMongoDocument, BaseRequestResponse


class StatsTimeframes(int, Enum):
    Minutes15 = 15
    Minutes30 = 30
    Minutes60 = 60
    Minutes90 = 90
    Hour6 = 6 * 60
    Hour12 = 12 * 60
    Day1 = 24 * 60
    Day3 = 3 * 24 * 60
    Week1 = 7 * 24 * 60
    Month1 = 30 * 24 * 60


class AnalyticsResults(BaseRequestResponse):
    average: float
    median: float
    minimum: float
    maximum: float
    percentiles: List[float]


class Analytics(BaseMongoDocument):
    name: str
    record_type: RdataType
    resolve_time: float
    ttl: int

    @classmethod
    async def statistics(cls, timeframe: StatsTimeframes) -> AnalyticsResults | None:
        upper_bound = datetime.utcnow()
        lower_bound = upper_bound - timedelta(minutes=timeframe.value)

        pipeline = [
            {"$match": {"created_at": {"$gte": lower_bound, "$lte": upper_bound}}},
            {
                "$group": {
                    "_id": None,
                    "average": {"$avg": "$resolve_time"},
                    "median": {"$median": {"input": "$resolve_time", "method": "approximate"}},
                    "minimum": {"$min": "$resolve_time"},
                    "maximum": {"$max": "$resolve_time"},
                    "percentiles": {
                        "$percentile": {"input": "$resolve_time", "p": [0.75, 0.99], "method": "approximate"}
                    },
                }
            },
            {"$project": {"_id": False}},
        ]
        result = await cls.aggregate(pipeline, projection_model=AnalyticsResults).to_list(1)
        if len(result) == 0:
            return None

        return result[0]

    class Settings:
        name: str = "analytics"
