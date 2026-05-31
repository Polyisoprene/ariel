from arielbot.domain.entities import SubTarget, SubChannel, BotStatus


class TestSubTarget:
    def test_create(self):
        t = SubTarget(uid="123", nickname="test", live_status=0)
        assert t.uid == "123"
        assert t.nickname == "test"
        assert t.live_status == 0

    def test_equality(self):
        a = SubTarget(uid="1", nickname="x", live_status=1)
        b = SubTarget(uid="1", nickname="x", live_status=1)
        assert a == b


class TestSubChannel:
    def test_create(self):
        c = SubChannel(uid="1", group_id=100, bot_id=200, live_active=True, dyn_active=False)
        assert c.uid == "1"
        assert c.group_id == 100
        assert c.bot_id == 200
        assert c.live_active is True
        assert c.dyn_active is False


class TestBotStatus:
    def test_create(self):
        b = BotStatus(bot_id=1, group_id=2, push_active=True, bot_active=True)
        assert b.push_active is True
