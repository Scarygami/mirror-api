
DEMOS = ["add_a_cat", "instaglass", "friend_finder", "check_in"]

demo_services = []
for demo in DEMOS:
    demo_services.append(__import__("demos." + demo, fromlist="*"))

DEMO_ROUTES = []
for demo_service in demo_services:
    if hasattr(demo_service, "ROUTES"):
        DEMO_ROUTES.extend(demo_service.ROUTES)
