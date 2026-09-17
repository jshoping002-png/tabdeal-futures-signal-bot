from datetime import datetime, timedelta, timezone
import json

import pytest

from tabdeal_signal.data_sources.contracts import DataQualityStatus
from tabdeal_signal.data_sources.public_sources import (
    BlsPublicApiDataSource,
    CftcPublicReportingDataSource,
    CoinMarketCapKeylessDataSource,
    EcbSdmxDataSource,
    PublicHttpResponse,
    SecEdgarDataSource,
    TreasuryDailyRatesDataSource,
    UrllibPublicHttpTransport,
)

UTC = timezone.utc


class FakeTransport:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.calls = []

    def request(self, method, url, *, query, body, content_type, timeout_seconds):
        self.calls.append((method, url, query, body, content_type, timeout_seconds))
        if self.error:
            raise self.error
        return self.response


def response(body, status=200, content_type="application/json", when=datetime(2026, 1, 1, tzinfo=UTC)):
    return PublicHttpResponse(status, when, body.encode(), content_type)


def test_bls_json_post_is_public_and_pit_safe():
    transport = FakeTransport(response(json.dumps({"Results": {}})))
    source = BlsPublicApiDataSource(
        endpoint="https://api.bls.gov/publicAPI/v1/timeseries/data/",
        topic="series-query",
        schema_version="verification-batch-001",
        body={"seriesid": ["X"]},
        transport=transport,
    )
    snapshot = source.fetch_snapshot(as_of=datetime(2026, 1, 1, 0, 0, 1, tzinfo=UTC))
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert transport.calls[0][0] == "POST"
    assert transport.calls[0][3] == b'{"seriesid":["X"]}'


def test_as_of_after_receive_is_unavailable():
    received = datetime(2026, 1, 1, 0, 0, 2, tzinfo=UTC)
    transport = FakeTransport(response("{}", when=received))
    source = SecEdgarDataSource(
        endpoint="https://data.sec.gov/test",
        topic="submissions",
        schema_version="verification-batch-002",
        transport=transport,
    )
    snapshot = source.fetch_snapshot(as_of=received - timedelta(seconds=1))
    assert snapshot.metadata.quality is DataQualityStatus.UNAVAILABLE
    assert snapshot.values["error_class"] == "pit_unavailable"


def test_http_429_is_rate_limited():
    transport = FakeTransport(response("{}", 429))
    source = CoinMarketCapKeylessDataSource(
        endpoint="https://pro-api.coinmarketcap.com/public-api/test",
        topic="market",
        schema_version="verification-batch-004",
        transport=transport,
    )
    snapshot = source.fetch_snapshot()
    assert snapshot.values["error_class"] == "rate_limited"


def test_invalid_json_is_invalid():
    transport = FakeTransport(response("not-json"))
    source = SecEdgarDataSource(
        endpoint="https://data.sec.gov/test",
        topic="submissions",
        schema_version="verification-batch-002",
        transport=transport,
    )
    snapshot = source.fetch_snapshot()
    assert snapshot.metadata.quality is DataQualityStatus.INVALID
    assert snapshot.values["error_class"] == "invalid_json"


def test_treasury_xml_is_parsed_without_domain_inference():
    transport = FakeTransport(response("<root><entry>1</entry></root>", content_type="application/xml"))
    source = TreasuryDailyRatesDataSource(
        endpoint="https://home.treasury.gov/test.xml",
        topic="daily-rates",
        schema_version="verification-batch-002",
        transport=transport,
    )
    snapshot = source.fetch_snapshot()
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert snapshot.values["root_tag"] == "root"
    assert "entry" in snapshot.values["xml_text"]


def test_text_source_preserves_cftc_format_without_inference():
    transport = FakeTransport(response("a,b\n1,2", content_type="text/csv"))
    source = CftcPublicReportingDataSource(
        endpoint="https://publicreporting.cftc.gov/resource/test.csv",
        topic="cot",
        schema_version="verification-batch-004",
        transport=transport,
    )
    snapshot = source.fetch_snapshot()
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert snapshot.values["text"] == "a,b\n1,2"


def test_hosts_are_strictly_scoped():
    with pytest.raises(ValueError):
        SecEdgarDataSource(
            endpoint="https://example.com/data",
            topic="submissions",
            schema_version="r",
        )


def test_transport_has_no_auth_surface_and_rejects_other_methods():
    transport = UrllibPublicHttpTransport()
    with pytest.raises(ValueError):
        transport.request(
            "DELETE",
            "https://data.sec.gov/test",
            query=None,
            body=None,
            content_type=None,
            timeout_seconds=1,
        )


def test_transport_rejects_url_userinfo():
    transport = UrllibPublicHttpTransport()
    with pytest.raises(ValueError):
        transport.request(
            "GET",
            "https://user:password@data.sec.gov/test",
            query=None,
            body=None,
            content_type=None,
            timeout_seconds=1,
        )


def test_configured_source_rejects_url_userinfo():
    with pytest.raises(ValueError):
        SecEdgarDataSource(
            endpoint="https://user:password@data.sec.gov/test",
            topic="submissions",
            schema_version="r",
        )


def test_response_rejects_naive_received_at():
    with pytest.raises(ValueError):
        PublicHttpResponse(200, datetime(2026, 1, 1), b"{}")


def test_auth_material_is_rejected_from_configured_sources():
    with pytest.raises(ValueError):
        SecEdgarDataSource(
            endpoint="https://data.sec.gov/test",
            topic="submissions",
            schema_version="r",
            query={"api_key": "secret"},
        )
    with pytest.raises(ValueError):
        BlsPublicApiDataSource(
            endpoint="https://api.bls.gov/publicAPI/v1/timeseries/data/",
            topic="series-query",
            schema_version="r",
            body={"authorization": "Bearer secret"},
        )


def test_ecb_text_envelope_preserves_source_payload():
    transport = FakeTransport(response('{"data":1}', content_type="application/json"))
    source = EcbSdmxDataSource(
        endpoint="https://data-api.ecb.europa.eu/service/test",
        topic="series",
        schema_version="verification-batch-005",
        transport=transport,
    )
    snapshot = source.fetch_snapshot()
    assert snapshot.metadata.quality is DataQualityStatus.VALID
    assert snapshot.values["text"] == '{"data":1}'
