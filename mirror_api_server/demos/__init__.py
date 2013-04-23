
DEMOS = ["add_a_cat", "instaglass", "friend_finder"]

demo_services = []
for demo in DEMOS:
    demo_services.append(__import__("demos." + demo, fromlist="*"))
