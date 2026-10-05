import dataclasses

import pytest

from app.integrations.base import NormalizedContent, PlatformAdapter


def test_normalized_content_has_the_agreed_fields_and_is_immutable():
    c = NormalizedContent(source="telegram", content_type="text", text="hi", external_message_id="42")
    assert [f.name for f in dataclasses.fields(c)] == ["source", "content_type", "text", "media_url",
                                                         "external_message_id"]
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.text = "changed"


def test_an_adapter_must_implement_both_methods():
    class Incomplete(PlatformAdapter):
        source = "demo"

        def normalize(self, raw_update):
            return None

    with pytest.raises(TypeError):
        Incomplete()

    class Echo(PlatformAdapter):
        source = "demo"

        def normalize(self, raw_update):
            return NormalizedContent(source=self.source, content_type="text", text=raw_update["text"],
                                     external_message_id=str(raw_update["id"]))

        def send_reply(self, content, reply_text):
            self.sent = (content.external_message_id, reply_text)

    adapter = Echo()
    content = adapter.normalize({"id": 7, "text": "hello"})
    adapter.send_reply(content, "LOW")
    assert content.text == "hello" and adapter.sent == ("7", "LOW")
