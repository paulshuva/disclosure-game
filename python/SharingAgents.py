from RecognitionAgents import RecognitionResponder
from Model import BayesianSignaller

class SharingResponder(RecognitionResponder):
    """
    Class of responder which remembers the actions of opponents and then retrospectively
    updates beliefs based on that when true information is available.
    Makes the most recent referral available to be shared.
    """
    def __init__(self, player_type=1, signals=[0, 1, 2], responses=[0, 1],
        share_weight=0.):
        # Memory available for sharing
        self.shareable = None
        #Weight given to other's info
        self.share_weight = share_weight
        super(SharingResponder, self).__init__(player_type, signals, responses)

    def __str__(self):
        return "sharing_%s" % super(SharingResponder, self).__str__()

    def exogenous_update(self, payoff, signaller, signal, signaller_type=None):
        self.update_beliefs(payoff, signaller, signal, signaller_type, self.share_weight)

    def remember(self, signaller, signal, response):
        """
        Remember what was done in response to a signal.
        """
        super(SharingResponder, self).remember(signaller, signal, response)
        if response == 1:
            payoff_sum = sum(map(lambda x: self.payoffs[signaller.player_type][x[1]], self.signal_memory[hash(signaller)]))
            self.shareable = (payoff_sum, (hash(signaller), (signaller.player_type, list(self.signal_memory[hash(signaller)]))))


class SharingSignaller(BayesianSignaller):
    def __init__(self, player_type=1, signals=[0, 1, 2], responses=[0, 1],
        share_weight=0.):
        # Exogenous memories
        self.exogenous = []
        #Weight given to other's info
        self.share_weight = share_weight
        super(SharingSignaller, self).__init__(player_type, signals, responses)

    def __str__(self):
        return "sharing_%s" % super(SharingSignaller, self).__str__()

    def exogenous_update(self, signal, response, tmp_signaller, payoff, midwife_type=None):
        self.log_signal(signal, tmp_signaller, self.share_weight)
        self.exogenous.append((tmp_signaller.player_type, signal, response, payoff))
        self.update_beliefs(response, tmp_signaller, payoff, midwife_type, self.share_weight)

    def get_memory(self):
        memories = zip(self.type_log, self.signal_log, self.response_log, self.payoff_log)
        for memory in self.exogenous:
            memories.remove(memory)
        payoff_sum = sum(map(lambda x: x[3], memories))
        return (payoff_sum, memories)
