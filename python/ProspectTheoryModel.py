import Model
import math
import random

class ProspectTheorySignaller(Model.BayesianSignaller):
    """
    A responder which makes decision using cumulative prospect theory.
    """
    def __init__(self, player_type=1, signals=[0, 1, 2], responses=[0, 1], 
        alpha=.859, beta=.826, l=2.25, gamma=.618, delta=.592):
        self.alpha = alpha
        self.gamma = gamma
        self.l = l
        self.delta = delta
        self.beta = beta
        super(ProspectTheorySignaller, self).__init__(player_type, signals, responses)

    def weighting(self, probability, power):
        return pow(probability, power) / pow(pow(probability, power) + pow(1. - probability, power), 1. / power)


    def value(self, outcome):
        """
        Return the relative value of an outcome.
        """
        if outcome > 0:
            return self.gain_value(outcome)
        elif outcome < 0:
            return self.l * self.loss_value(outcome)
        return 0

    def gain_value(self, payoff):
        if self.alpha > 0:
            payoff = pow(payoff, self.alpha)
        elif self.alpha < 0:
            payoff = math.log(payoff)
        else:
            payoff = 1 - pow(1 + payoff, self.alpha)
        return payoff

    def loss_value(self, payoff):
        if self.beta > 0:
            payoff = -pow(-payoff, self.beta)
        elif self.beta < 0:
            payoff = pow(1 - payoff, self.beta) - 1
        else:
            payoff = -math.log(-payoff)
        return payoff

    def collect_prospects(self, signal, appointment):
        """
        Compute the cumulative prospect theory value of this signal
        based on the estimated probalities at this appointment.
        """
        prospects = []
        for player_type, log in self.type_distribution.items():
            type_belief = log[appointment]
            for response, belief in self.response_belief[signal].items():
                response_belief = belief[appointment]
                total_belief = response_belief*type_belief
                payoff = self.baby_payoffs[response] + self.social_payoffs[player_type][signal]
                prospects.append((payoff, total_belief))
        prospects.sort()
        prospects.reverse()
        return prospects

    def cpt_value(self, prospects):
        """
        Compute the cumulative prospect theory value of this set of
        prospects.
        """
        payoffs, probs = zip(*prospects)
        signal_risk = 0.
        for i in range(len(prospects)):
            type_belief = probs[i]
            payoff = payoffs[i]
            power = self.gamma
            if payoff < 0:
                power = self.delta
            if i == 0 and payoff < 0 or i == (len(prospects) - 1) and payoff >= 0:
                weight =  (1 - self.weighting(1 - type_belief, power))
                #print "1 - w(1 - ", type_belief,")"
            elif payoff < 0:
                #print "sum(",probs[i:],"-sum(",probs[i + 1:],")"
                weight = self.weighting(sum(probs[i:]), power) - self.weighting(sum(probs[i + 1:]), power)
            else:
                weight = self.weighting(sum(probs[:i + 1]), power) - self.weighting(sum(probs[:i]), power)
                #print "sum(",probs[:i+1],"-sum(",probs[:i],")"
            #print "Weighting for outcome %f: %f" % (payoff, weight)
            signal_risk += self.value(payoff) * weight
        return signal_risk

    def do_signal(self, own_type, rounds=None):
        """
        Make a judgement about somebody based on
        the signal they sent based on expe
        """
        best = (random.randint(0, 2), -9999999)
        if rounds is None:
            rounds = self.rounds
        for signal in Model.shuffled(self.signals):
            act_risk = self.cpt_value(self.collect_prospects(signal, rounds))
            if act_risk > best[1]:
                best = (signal, act_risk)
        self.rounds += 1
        self.log_signal(best[0])
        return best[0]

class ProspectTheoryResponder(Model.BayesianResponder):
    """
    A responder which makes decision using prospect theory.
    Reference may take value 0 (total losses so far), 1 (losses last round), or 3
    (worst case losses this round)
    Weighting is some function that takes the probability p and returns a weighted version of it.
    """
    def __init__(self, player_type=1, signals=[0, 1, 2], responses=[0, 1],
        alpha=.88, beta=.88, l=2.25, gamma=.61, delta=.69):
        self.alpha = alpha
        self.gamma = gamma
        self.l = l
        self.delta = delta
        self.beta = beta
        super(ProspectTheoryResponder, self).__init__(player_type, signals, responses)

    def weighting(self, probability, power):
        return pow(probability, power) / pow(pow(probability, power) + pow(1. - probability, power), 1. / power)


    def value(self, outcome):
        """
        Return the relative value of an outcome.
        """
        if outcome > 0:
            return self.gain_value(outcome)
        elif outcome < 0:
            return self.l * self.loss_value(outcome)
        return 0

    def gain_value(self, payoff):
        if self.alpha > 0:
            payoff = pow(payoff, self.alpha)
        elif self.alpha < 0:
            payoff = math.log(payoff)
        else:
            payoff = 1 - pow(1 + payoff, self.alpha)
        return payoff

    def loss_value(self, payoff):
        if self.beta > 0:
            payoff = -pow(-payoff, self.beta)
        elif self.beta < 0:
            payoff = pow(1 - payoff, self.beta) - 1
        else:
            payoff = -math.log(-payoff)
        return payoff

    def collect_prospects(self, response, signal, appointment):
        """
        Collate the prospects for this response given the signal,
        and sort them in descending order of payoff.
        """
        prospects = []
        for player_type, belief in self.signal_belief[signal].items():
            type_belief = belief[appointment]
            payoff = self.payoffs[player_type][response]
            prospects.append((payoff, type_belief))
        prospects.sort()
        prospects.reverse()
        return prospects

    def cpt_value(self, prospects):
        """
        Compute the cumulative prospect theory value of this set of
        prospects.
        """
        payoffs, probs = zip(*prospects)
        signal_risk = 0.
        for i in range(len(prospects)):
            type_belief = probs[i]
            payoff = payoffs[i]
            power = self.gamma
            if payoff < 0:
                power = self.delta
            if i == 0 and payoff < 0 or i == (len(prospects) - 1) and payoff >= 0:
                weight =  (1 - self.weighting(1 - type_belief, power))
            elif payoff < 0:
                weight = self.weighting(sum(probs[i:]), power) - self.weighting(sum(probs[i + 1:]), power)
            else:
                weight = self.weighting(sum(probs[:i + 1]), power) - self.weighting(sum(probs[:i]), power)
            #print "Weighting for outcome %f: %f" % (payoff, weight)
            signal_risk += self.value(payoff) * weight
       #print "U(%d|x)=%f" % (signal, signal_risk)
        return signal_risk

    def respond(self, signal, rounds=None):
        """
        Make a judgement about somebody based on
        the signal they sent based on expe
        """
        if rounds is None:
            self.signal_log.append(signal)
            self.signal_matches[signal] += 1.
            rounds = self.rounds

        best = (random.randint(0, 1), -9999999)
        for response in Model.shuffled(self.responses):
            act_risk = self.cpt_value(self.collect_prospects(response, signal, rounds))
            if act_risk > best[1]:
                best = (response, act_risk)
        self.response_log.append(best[0])
        self.rounds += 1
        return best[0]
