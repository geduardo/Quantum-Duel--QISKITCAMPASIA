import json
from collections import OrderedDict
import tornado.websocket

class DuelGroup:
    NUMBER_OF_MEMBERS = 3

    def __init__(self):
        self.members = []
        self.end = False

class MultiHandler(tornado.websocket.WebSocketHandler):
    duel_groups = OrderedDict()

    def open(self, *args, **kwargs):
        previous_last_duel_group_key = next(reversed(self.duel_groups), None)
        if previous_last_duel_group_key is None or self.duel_groups[previous_last_duel_group_key].end or len(self.duel_groups[previous_last_duel_group_key].members) >= DuelGroup.NUMBER_OF_MEMBERS:
            self.duel_groups[0 if previous_last_duel_group_key is None else previous_last_duel_group_key + 1] = DuelGroup()

        duel_group_key = next(reversed(self.duel_groups))
        duel_group = self.duel_groups[duel_group_key]
        duel_group.members.append(self)
        self.write_message({'duel_group': duel_group_key})

        if len(duel_group.members) >= DuelGroup.NUMBER_OF_MEMBERS:
            for member in duel_group.members:
                member.write_message({'message': 'ready'})

    def on_message(self, message):
        message = json.loads(message)
        duel_group = self.duel_groups[message['duel_group']]

        if duel_group.end:
            return

        duel_group.end = True
        for member in duel_group.members:
            member.write_message({'message': 'win' if member == self else 'lose'})

    def on_close(self):
        duel_group_key = next(filter(lambda x: self in self.duel_groups[x].members, self.duel_groups), None)
        if duel_group_key:
            self.duel_groups[duel_group_key].members.remove(self)
            if len(self.duel_groups[duel_group_key].members) == 0:
                del self.duel_groups[duel_group_key]