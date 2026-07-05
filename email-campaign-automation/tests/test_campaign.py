import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from campaign import TemplateEngine, SubscriberList, EmailCampaignManager, EmailTemplate, Subscriber


def test_template_render():
    result = TemplateEngine.render("Hello {{name}}!", {"name": "Alice"})
    assert result == "Hello Alice!"


def test_template_render_multiple():
    result = TemplateEngine.render("{{greeting}} {{name}}, your code is {{code}}",
                                    {"greeting": "Hi", "name": "Bob", "code": "1234"})
    assert "Hi Bob" in result
    assert "1234" in result


def test_template_extract_variables():
    vars = TemplateEngine.extract_variables("Hello {{name}}, {{city}}!")
    assert "name" in vars
    assert "city" in vars


def test_subscriber_list_add():
    lst = SubscriberList()
    sub = lst.add("alice@example.com", "Alice", ["vip"])
    assert sub.email == "alice@example.com"
    assert "vip" in sub.tags
    assert lst.count() == 1


def test_subscriber_list_remove():
    lst = SubscriberList()
    lst.add("alice@example.com")
    lst.remove("alice@example.com")
    assert lst.count() == 0


def test_subscriber_list_by_tag():
    lst = SubscriberList()
    lst.add("a@example.com", tags=["vip"])
    lst.add("b@example.com", tags=["free"])
    vip = lst.get_by_tag("vip")
    assert len(vip) == 1
    assert vip[0].email == "a@example.com"


def test_campaign_create():
    mgr = EmailCampaignManager(from_email="noreply@test.com")
    mgr.add_template(EmailTemplate("welcome", "Welcome {{name}}", "<h1>Hi {{name}}</h1>"))
    lst = mgr.create_list("main")
    lst.add("user@test.com", "User")
    campaign = mgr.create_campaign("c1", "Welcome Campaign", "welcome", "main")
    assert len(campaign.recipients) == 1
    assert campaign.template_name == "welcome"


def test_campaign_send_no_smtp():
    mgr = EmailCampaignManager(from_email="noreply@test.com")
    mgr.add_template(EmailTemplate("welcome", "Welcome {{name}}", "<p>Hi {{name}}</p>"))
    lst = mgr.create_list("main")
    lst.add("user@test.com", "User")
    mgr.create_campaign("c1", "Welcome", "welcome", "main")
    sent, failed = mgr.send_campaign("c1", {"name": "User"})
    assert sent == 1
    assert failed == 0


def test_tracking_pixel():
    mgr = EmailCampaignManager(from_email="noreply@test.com")
    mgr.add_template(EmailTemplate("t", "Subject", "<p>Body</p>"))
    lst = mgr.create_list("main")
    lst.add("u@t.com")
    mgr.create_campaign("c1", "Test", "t", "main")
    mgr.send_campaign("c1")
    pixel_id = f"pixel_c1_u@t.com"
    mgr.track_open(pixel_id)
    assert mgr.campaigns["c1"].opened == 1


def test_stats():
    mgr = EmailCampaignManager()
    mgr.add_template(EmailTemplate("t", "S", "<p>B</p>"))
    mgr.create_list("main")
    mgr.lists["main"].add("a@b.com")
    stats = mgr.stats()
    assert stats["templates"] == 1
    assert stats["lists"] == 1
    assert stats["total_subscribers"] == 1


def test_auto_extract_variables():
    mgr = EmailCampaignManager()
    tpl = EmailTemplate("t", "Hello {{name}}", "<p>Hi {{name}} from {{city}}</p>")
    mgr.add_template(tpl)
    assert "name" in mgr.templates["t"].variables
    assert "city" in mgr.templates["t"].variables
