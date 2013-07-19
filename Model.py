import random
import math
#import pylab
import time

line_type = {}
line_type[0] = '+-'
line_type[1] = 'o-'
line_type[2] = '1-'
line_colour = {}
line_colour[0] = 'r'
line_colour[1] = 'b'
line_colour[2] = 'g'

def generate_players():
    """ Generate players for a game.
    """
    return (Agent(None), Agent(None))

def all_played(women, rounds=12):
    for woman in women:
        if(woman.rounds < rounds):
            return False
    return True

def weighted_choice(choices):
    """
    Return a weighted random choice amongst player types,
    given a list of tuples of form (type, weight)
    """
    total = sum(weight for player_type, weight in choices)
    r = random.uniform(0, total)
    upto = 0
    for player_type, weight in choices:
        if upto + weight > r:
            return player_type
        upto += weight
    


def make_random_patients(signaller, num=1000, weights=[1/3., 1/3., 1/3.]):
    women = []
    for i in range(num):
        women.append(signaller(player_type=weighted_choice(zip([0, 1, 2], weights))))
    return women

def make_random_midwives(responder, num=100, weights=[1/3., 1/3., 1/3.]):
    midwives = []
    for i in range(num):
        midwives.append(responder(player_type=weighted_choice(zip([0, 1, 2], weights))))
    return midwives

def signal_choice(women):
    """
    Return a dictionary of women type vs. average signal choice per
    round.
    """
    choices = {}
    for player_type in range(3):
        choices[player_type] = {}
        for signal in range(3):
            choices[player_type][signal] = [0 for x in range(women[0].rounds)]
    for player_type, players in by_type(women).items():
        for i in range(women[0].rounds):
            for player in players:
                choices[player_type][player.signal_log[i]][i] += 1
    counts = count(women)
    for player_type, signals in choices.items():
        for signal in signals:
            for i in range(women[0].rounds):
                choices[player_type][signal][i] /= float(counts[player_type])
    return choices


def dump_women(women, params,file_name, mode):
    header = "\n"
    try:
        with open(file_name): pass
    except IOError:
        mode = 'w'
    if mode == 'a':
        target = open(file_name, 'a')
        target.write(header)
        target.close()
        target = open("signals_"+file_name, 'a')
        target.write(header)
        target.close()

    elif mode == 'w':
        target = open(file_name, 'w')
        header = "id, appointment, type, signal, payoff, referred"
        for name, value in params.items():
            header += ",%s" % name
        header += "\n"
        target.write(header)
        target.close()

        target = open("signals_"+file_name, 'w')
        header = "id, appointment, type, signal_p, signal_payoff, confidence"
        for name, value in params.items():
            header += ",%s" % name
        header += "\n"
        target.write(header)
        target.close()
    param_vals = ""
    for name, value in params.items():
        param_vals += ",%s" % value
    lines = []
    sig_lines = []
    j = 0
    for woman in women:
        for i in range(woman.rounds):
            line = "%d, %d,%d,%d, %f, %s %s" % (j, i, woman.player_type, woman.signal_log[i], woman.payoff_log[i], woman.response_log[i] == 1, param_vals)
            lines.append(line)
            for signal, payoffs in woman.payoff_belief.items():
                for payoff, belief in payoffs.items():
                    line = "%d, %d,%d, %d, %d, %f %s" % (j, i, woman.player_type, signal, payoff, belief[i], param_vals)
                    sig_lines.append(line)
        j += 1
    target = open(file_name, 'a')
    target.write("\n".join(lines))
    target.close()
    target = open("signals_"+file_name, 'a')
    target.write("\n".join(sig_lines))
    target.close()

def dump_midwives(midwives, params,file_name, mode):
    header = "\n"
    try:
        with open(file_name): pass
    except IOError:
        mode = 'w'
    if mode == 'a':
        target = open(file_name, 'a')
        target.write(header)
        target.close()
        target = open("signals_"+file_name, 'a')
        target.write(header)
        target.close()

    elif mode == 'w':
        target = open(file_name, 'w')
        header = "id, appointment, type, signal, payoff, referred"
        for name, value in params.items():
            header += ",%s" % name
        header += "\n"
        target.write(header)
        target.close()

        target = open("signals_"+file_name, 'w')
        header = "id, appointment, type, belief, b_type, belief_level"
        for name, value in params.items():
            header += ",%s" % name
        header += "\n"
        target.write(header)
        target.close()
    param_vals = ""
    for name, value in params.items():
        param_vals += ",%s" % value
    lines = []
    sig_lines = []
    j = 0
    for woman in midwives:
        for i in range(woman.rounds):
            line = "%d, %d,%d,%d, %f, %s %s" % (j, i, woman.player_type, woman.signal_log[i], woman.payoff_log[i], woman.response_log[i] == 1, param_vals)
            lines.append(line)

            for signal, types in woman.signal_belief.items():
                for player_type, log in types.items():
                    line = "%d, %d,%d,%d, %d, %f %s" % (j, i, woman.player_type, signal, player_type, woman.signal_belief[signal][player_type][i], param_vals)
                    sig_lines.append(line)
        j += 1
    target = open(file_name, 'a')
    target.write("\n".join(lines))
    target.close()
    target = open("signals_"+file_name, 'a')
    target.write("\n".join(sig_lines))
    target.close()

def type_belief(midwives):
    """
    Return a dictionary of signals vs. average belief about what they mean
    per round.
    """
    beliefs = {}
    counts = rounds_count(midwives)
    max_rounds = max(counts.keys())
    for i in range(3):
        beliefs[i] = {}
        for j in range(3):
            beliefs[i][j] = [0 for x in range(max_rounds)]
    for midwife in midwives:
        for i in range(3):
            for j in range(3):
                for k in range(midwife.rounds - 1):
                    beliefs[i][j][k] += midwife.signal_belief[i][j][k]
    for i in range(3):
        for j in range(3):
            for k in range(max_rounds):
                beliefs[i][j][k] /= float(counts[k])
    return beliefs

def referral_choice(midwives):
    """
    Return the probability of referring over time.
    """
    counts = rounds_count(midwives)
    max_rounds = max(counts.keys())
    referral = {'all':[0 for x in range(max_rounds)]}
    for signal in range(3):
        referral[signal] = [[0, 0] for x in range(max_rounds)]

    for midwife in midwives:
        for i in range(midwife.rounds - 1):
            if midwife.response_log[i] == 1:
                referral['all'][i] += 1.
                referral[midwife.signal_log[i]][i][1] += 1.
            referral[midwife.signal_log[i]][i][0] += 1.
    for i in range(max_rounds):
        referral['all'][i] /= float(counts[i])
        for signal in range(3):
            if referral[signal][i][0] > 0:
                referral[signal][i] = referral[signal][i][1] / referral[signal][i][0]
            else:
                referral[signal][i] = 0.
    return referral

def plot_referral_choice(midwives):
    choices = referral_choice(midwives)
    for signal, log in choices.items():
        label = "Signal:", signal
        pylab.plot(range(len(log)), log, label=label)
    pylab.legend(loc='upper right')
    pylab.show()



def plot_signal_beliefs(midwives):
    beliefs = type_belief(midwives)
    for signal, types in beliefs.items():
        for player_type, log in types.items():
            label = "Signal: %d, type: %d" % (signal, player_type)
            line = "%s%s" % (line_colour[player_type], line_type[signal])
            pylab.plot(range(len(log)), log, line, label=label)
    pylab.legend(loc='upper right')
    pylab.show()




def rounds_count(players):
    """
    Return a dictionary mapping number of rounds played
    to the number of players who played at least that many.
    """
    counts = {}
    for player in players:
        for i in range(player.rounds):
            if i in counts:
                counts[i] += 1
            else:
                counts[i] = 1
    return counts


def plot_average_signal_choice(women):
    choices = signal_choice(women)

    for player_type, signals in choices.items():
        for signal, log in signals.items():
            label = "Type: %d, signal: %d" % (player_type, signal)
            line = "%s%s" % (line_colour[signal], line_type[player_type])
            pylab.plot(range(women[0].rounds), log, line, label=label)
    pylab.legend(loc='upper right')
    pylab.show()

def plot_signal_choice(women):
    for player_type, signals in choices.items():
        for signal, log in signals.items():
            label = "Type: %d, signal: %d" % (player_type, signal)
            line = "%s%s" % (line_colour[signal], line_type[player_type])
            pylab.scatter(range(12), log, line, label=label)
    pylab.legend(loc='upper right')
    pylab.show()




def frequency(players):
    """ Return the frequency of each player type.
    """


def count(players):
    """
    Return the number of each player type.
    """
    types = {}
    types[0] = 0
    types[1] = 0
    types[2] = 0
    for player in players:
        types[player.player_type] += 1
    return types

def by_type(players):
    """ Return a dictionary mapping player type
    to a list of players with it.
    """
    types = {}
    for player_type in range(3):
        types[player_type] = []
    for player in players:
        types[player.player_type].append(player)
    return types


def test(women, midwives, rounds=12):
    birthed = []
    game = Game()
    game.init_payoffs()
    while not all_played(women, rounds):
        woman = women.pop()
        game.play_game(woman, random.choice(midwives))
        if woman.rounds == rounds:
            birthed.append(woman)
        else:
            women.append(woman)
        random.shuffle(women)
    return birthed

def all_played_caseload(caseload, rounds=12):
    for midwife, cases in caseload.items():
        if not all_played(cases, rounds):
            return False
    return True

def caseload_test(women, midwives, rounds=12):
    birthed = []
    game = Game()
    game.init_payoffs()
    #Assign women to midwives
    caseloads = {}
    num_women = len(women)
    num_midwives = len(midwives)
    load = num_women / num_midwives

    for midwife in midwives:
        caseloads[midwife] = []
        for i in range(load):
            caseloads[midwife].append(women.pop())

    # Assign leftovers at random
    while len(women) > 0:
        caseloads[random.choice(midwives)].append(women.pop())

    while not all_played_caseload(caseloads, rounds):
        for midwife, cases in caseloads.items():
            if not all_played(cases, rounds):
                woman = cases.pop()
                game.play_game(woman, midwife)
                if woman.rounds == rounds:
                    birthed.append(woman)
                else:
                    cases.append(woman)
    return birthed

def equal_rounds(women, midwives, rounds=100):
    game = Game()
    game.init_payoffs()

    for i in range(rounds):
        random.shuffle(women)
        random.shuffle(midwives)

        for j in range(len(women)):
            game.play_game(women[j], midwives[j])
    return women

def decision_fn_compare(file_prefix="12_appt_",test_fn=test, num_midwives=100, num_women=1000, runs=100):
    prospect_women = []
    prospect_midwives = []
    bayes_women = []
    bayes_midwives = []
    for i in range(runs):
        print "Starting run %d/%d on %s" % (i + 1, runs, file_prefix)
        women = make_random_patients(ProspectTheorySignaller, num=num_women,weights=[7/10., 2/10., 1/10.])
        mw = make_random_midwives(ProspectTheoryResponder, num_midwives, [5/10., 4/10., 1/10.])
        print "Made PTs."

        women = test_fn(women, mw)
        print "Ran trial."
        dump_women(women, {'starting_beliefs':'random', 'decision_rule':'prospect', 'caseload':'FALSE'}, file_prefix+"women_prospect.csv", 'a')
        dump_midwives(mw, {'starting_beliefs':'random', 'decision_rule':'prospect', 'caseload':'FALSE'}, file_prefix+"mw_prospect.csv", 'a')
        print "Dumped results."

        women = women = make_random_patients(BayesianSignaller, num=num_women,weights=[7/10., 2/10., 1/10.])
        mw = make_random_midwives(BayesianResponder, num_midwives, [5/10., 4/10., 1/10.])
        print "Made bayesians."

        women = test_fn(women, mw)
        print "Ran trial."
        dump_women(women, {'starting_beliefs':'random', 'decision_rule':'bayes', 'caseload':'FALSE', 'run':i}, file_prefix+"women_bayes.csv", 'a')
        dump_midwives(mw, {'starting_beliefs':'random', 'decision_rule':'prospect', 'caseload':'FALSE','run':i}, file_prefix+"mw_bayes.csv", 'a')
        print "Dumped results."


def random_expectations():
    initial = [0.01, 1.01]
    for i in range(2):
        initial.append(random.random())
    initial.sort()
    results = []
    for i in range(3):
        results.append(initial[i + 1] - initial[i])
    return results

def prospect_weighting(gamma):
    """
    Return a weighted probability according to
    Tversky-Kahneman (1992).
    """        
    def f(p):
        weight = pow(p, gamma) / pow(pow(p, gamma) + pow(1. - p, gamma), 1. / gamma)
        return weight
    return f

def prelec_weighting(alpha, beta):
    """
    Return a weighting probability according to
    Prelec (1998)
    """
    def f(p):
        return math.exp(-beta * pow((- math.log(p)), alpha))
    return f



class Agent(object):
    """
    An agent who plays a game, according to their
    type, and some decision rule.
    Players are one of three types.
    0 = low
    1 = middle
    2 = high

    Players have two possible response moves.
    0 = do nothing
    1 = refer
    """
    def __init__(self, player_type=1, signals=[0, 1, 2], responses=[0, 1]):
        self.player_type = player_type
        self.signals = signals
        self.responses = responses
        self.payoff_log = []
        self.signal_log = []
        self.response_log = []
        self.type_log = []
        self.rounds = 0
        self.payoffs = None


    def respond(self, signal):
        """
        Make a judgement about somebody based on
        the signal they sent.
        """
        self.rounds += 1
        self.signal_log.append(signal)
        resp = random.choice(self.responses)
        self.response_log.append(resp)
        return resp

    def do_signal(self, opponent):
        """ Report own consumption based on
        decision function.
        """
        self.rounds += 1
        sig = random.choice(self.signals)
        self.signal_log.append(sig)
        return sig


    def update_beliefs(self, payoff, signaller_type):
        """ Update the agent's beliefs about
        the frequency of other types and so on.
        """
        self.payoff_log.append(payoff)

class Signaller(Agent):

    def __init__(self, player_type=1, signals=[0, 1, 2], responses=[0, 1]):
        # Given own type, there are always 6 possible payoffs for a given signal.
        # 2 for each of the three midwife types, per signal.
        self.payoff_belief = dict([(signal, {}) for signal in signals])
        super(Signaller, self).__init__(player_type, signals, responses)

    def init_payoffs(self, payoffs, type_weights=[1/3., 1/3., 1/3.]):
        # Don't set up twice.
        if self.payoffs is not None:
            return
        #Only interested in payoffs for own type
        self.payoffs = payoffs[self.player_type]
        #Interested in payoffs per signal
        for signal_i, payoff_set in self.payoff_belief.items():
            for midwife_type in range(3):
                for i in range(2):
                    #Payoff for this signal with this midwife type
                    payoff = self.payoffs[midwife_type][signal_i][i]
                    if payoff in payoff_set:
                        payoff_set[payoff][0] += type_weights[midwife_type] / 2.
                    else:
                        payoff_set[payoff] = [type_weights[midwife_type] / 2.]

    def update_beliefs(self, payoff, signaller_type):
        self.payoff_log.append(payoff)
        rounds = self.rounds

        for signal_i, payoffs in self.payoff_belief.items():
            signal_matches = [x == signal_i for x in self.signal_log]
            payoff_matches = {}
            for payoff, belief in payoffs.items():
                payoff_matches[payoff] = [x == payoff for x in self.payoff_log]

            for payoff, belief in payoffs.items():
                matched_pairs = zip(payoff_matches[payoff], signal_matches)

                # Rounds where we got this payoff having sent the signal count(Signal | Payoff)
                signal_payoff_matches = [a and b for a, b in matched_pairs]
                n_k = signal_payoff_matches.count(True)

                # Rounds where we sent this signal
                n = float(signal_matches.count(True))

                #print "Payoff-Signal matches", signal_payoff_matches

                #P(Payoff) in this state of the world
                alpha_k = self.payoff_belief[signal_i][payoff][0]
                alpha_dot = len(payoffs)
                prob = (alpha_k + n_k) / float(alpha_dot + n)
               #print "Probability = (%f + %d) / (%d + (%d - 1)) = %f" % (alpha_k, n_k, alpha_dot, n, prob)

                self.payoff_belief[signal_i][payoff].append(prob)

    def update_beliefs_old(self, payoff, signaller_type):
        """ Women have belief about the state of the world,
        and how likely refer or not actions are on the part
        of the responder, i.e. P(Payoff | Signal) = P(Signal | Payoff)P(Payoff) / P(Signal | Payoff)P(Payoff) + ..
        """
        self.payoff_log.append(payoff)
        rounds = self.rounds
        for signal_i, payoffs in self.payoff_belief.items():
            signal_matches = [x == signal_i for x in self.signal_log]
            payoff_matches = {}
            for payoff, belief in payoffs.items():
                payoff_matches[payoff] = [x == payoff for x in self.payoff_log]

            for payoff, belief in payoffs.items():
                #Othey payoffs
                other_payoffs = filter(lambda x: x != payoff, payoffs.keys())
                # Update given recent payoff using bayes rule
                #print "Payoff matches", payoff_matches
                
                #print "Signal matches", signal_matches

                matched_pairs = zip(payoff_matches[payoff], signal_matches)

                # Rounds where we got this payoff having sent the signal count(Signal | Payoff)
                signal_payoff_matches = [a and b for a, b in matched_pairs]
                # Other payoffs and this signal
                signal_payoff_others = {}
                for x in other_payoffs:
                    matched_pairs = zip(payoff_matches[x], signal_matches)
                    signal_payoff_others[x] = [a and b for a, b in matched_pairs]
                

                # Rounds where we sent this signal
                signal_matches_count = float(signal_matches.count(True))

                #print "Payoff-Signal matches", signal_payoff_matches

                #P(Payoff) in this state of the world
                p_payoff = self.payoff_belief[signal_i][payoff][0]
                p_signal_payoff = 0.
                p_signal_not_payoff = 0.
                p_payoff_signal = self.payoff_belief[signal_i][payoff][rounds - 1]
            
                if signal_matches_count > 0:
                   #print "Updating payoff belief for signal", signal_i, "payoff", payoff,". Signal happened",signal_matches_count," times"
                   #print "Got both",signal_payoff_matches.count(True),"times."
                    #P(Signal | Payoff)
                    p_signal_payoff = signal_payoff_matches.count(True) / signal_matches_count
                   #print "P(Signal|Payoff)=",p_signal_payoff
                    #P(Signal | -Payoff)
                    p_signal_not_payoff = 0.
                    for key, matches in signal_payoff_others.items():
                        p_signal_not_payoff += (matches.count(True) / signal_matches_count) * self.payoff_belief[signal_i][key][0]
                   #print "P(Signal|-Payoff)=",p_signal_not_payoff
                    # Probability that this signal actually leads to this payoff (P(Payoff | Signal))
                    p_payoff_signal = p_signal_payoff*p_payoff / (p_signal_payoff*p_payoff + p_signal_not_payoff)
                self.payoff_belief[signal_i][payoff].append(p_payoff_signal)

    def current_beliefs(self):
        """ Return the current beliefs about signals.
        """
        current = {}
        for signal, payoffs in self.payoff_belief.items():
            current[signal] = {}
            for payoff, log in payoffs.items():
                current[signal][payoff] = log[self.rounds]
        return current

    def get_belief(self, signal, payoff, appointment):
        if payoff in self.payoff_belief[signal]:
            return self.payoff_belief[signal][appointment]
        return 0

class LyingSignaller(Signaller):

    def do_signal(own_type):
        """ A decision function that always returns a
        type other than its own as a signal.
        """
        self.rounds += 1
        types = filter(lambda x: x != own_type, self.signals)
        return random.choice(types)

class BayesianSignaller(Signaller):
    def loss(self, payoff):
        """ Make a loss out of a payoff.
        """
        return -payoff

    def risk(self, signal, appointment):
        """
        Compute the bayes risk of sending this signal.
        """
        signal_risk = 0.

       #print "Assessing risk for signal",signal
        for payoff, belief in self.payoff_belief[signal].items():
            payoff_belief = belief[appointment]
            payoff = self.loss(payoff)
           #print "Believe payoff will be",payoff,"with confidence",payoff_belief
           #print "Risk is",payoff,"*",payoff_belief
            signal_risk += payoff * payoff_belief
       #print "R(%d|x)=%f" % (signal, signal_risk)
        return signal_risk


    def do_signal(self, own_type):
        best = (0, 9999999)
       #print "Type %d woman evaluating signals." % self.player_type
        for signal in self.signals:
            signal_risk = self.risk(signal, self.rounds)
           #print "Risk for signal %d is %f. Best so far is signal %d at %f." % (signal, signal_risk, best[0], best[1])
            if signal_risk < best[1]:
                best = (signal, signal_risk)
        self.signal_log.append(best[0])
        self.rounds += 1
        return best[0]


class ProspectTheorySignaller(BayesianSignaller):
    """
    A responder which makes decision using prospect theory.
    Reference may take value 0 (total losses so far), 1 (losses last round), or 3
    (worst case losses this round)
    """
    def __init__(self, weighting=prospect_weighting(0.5), reference=1,player_type=1, signals=[0, 1, 2], responses=[0, 1]):
        self.weighting = weighting
        self.reference = reference
        super(ProspectTheorySignaller, self).__init__(player_type, signals, responses)

    def value(self, reference, outcome):
        """
        Return the relative value of an outcome compared to
        the reference point. Outcome is assumed to be a cost
        here.
        """
        return (reference + outcome)

    def expected_utility(self, signal, appointment):
        """
        Compute the expected utility of this response at the
        given appointment.
        """

        signal_risk = 0.

       #print "Assessing risk for signal",signal
        for payoff, belief in self.payoff_belief[signal].items():
            payoff_belief = belief[appointment]
            
            reference_point = 0.  
           #print "appointment %d, using reference point %d" % (self.rounds, self.reference)
           #print "Payoffs", self.payoff_log 
            if self.rounds > 0:
                reference_point = self.payoff_log[self.rounds - 1]

            if self.reference == 0:
                reference_point = sum(self.payoff_log)
            elif self.reference == 2:
                reference_point = min(self.payoff_belief[signal].keys())

           #print "Believe payoff will be",payoff,"with confidence",payoff_belief
           #print "Utility is v(%f)*w(%f)" % (payoff,payoff_belief)
            signal_risk += self.value(reference_point, payoff) * self.weighting(payoff_belief)
       #print "U(%d|x)=%f" % (signal, signal_risk)
        return -signal_risk

    def do_signal(self, own_type):
        """
        Make a judgement about somebody based on
        the signal they sent based on expe
        """
        best = (0, 9999999)
        for signal in self.signals:
            act_risk = self.expected_utility(signal, self.rounds)
            if act_risk < best[1]:
                best = (signal, act_risk)
        self.signal_log.append(best[0])
        self.rounds += 1
        return best[0]

class MiniMaxSignaller(Signaller):
    """ A signaller which uses straight minimax, ignoring the
    risks.
    """

    def get_payoffs(self, signal):
        """
        Return a list of the possible payoffs for a signal.
        """
        payoffs = []
        for i in self.signals:
            for j in self.responses:
                payoffs.append(self.payoffs[i][signal][j])
        return payoffs

    def do_signal(self, signal):
        self.rounds += 1

        worst_case = {}
        for signal in self.signals:
            worst_case[signal] = min(self.get_payoffs(signal))
        
        best = (0, -99999)
        for signal in self.signals:
            if best[1] < worst_case[signal]:
                best = (signal, worst_case[signal])

        self.signal_log.append(best[0])
        return best[0]



class Responder(Agent):

    def __init__(self, player_type=1, signals=[0, 1, 2], responses=[0, 1]):
        # Belief that a particular signal means a state
        self.signal_belief = dict([(y, dict([(x, [1/3.]) for x in signals])) for y in signals])
        super(Responder, self).__init__(player_type, signals, responses)

    def init_payoffs(self, payoffs, type_weights=[1/3., 1/3., 1/3.]):
        self.type_weights = type_weights
        #Only interested in payoffs for own type
        self.payoffs = payoffs

    def update_beliefs(self, payoff, signaller_type):
        self.type_log.append(signaller_type)
        self.payoff_log.append(payoff)
        rounds = self.rounds

        type_matches = []
        for player_type in self.signals:
            type_matches.append([x == player_type for x in self.type_log])

        for signal_i, types in self.signal_belief.items():
            for player_type, belief in types.items():
                signal_matches = [x == signal_i for x in self.signal_log]
               #print "Updating P(%d|%d).." % (player_type, signal_i)
                alpha_k = self.type_weights[player_type]
               #print "alpha_k = %f" % alpha_k
                alpha_dot = len(self.signals)
               #print "Num alternatives = %d" % alpha_dot
                n = signal_matches.count(True)
               #print "n = %d" % n

                matched_pairs = zip(type_matches[player_type], signal_matches)
                signal_type_matches = [a and b for a, b in matched_pairs]
                n_k = signal_type_matches.count(True)
               #print "n_k = %d" % n_k
                prob = (alpha_k + n_k) / float(alpha_dot + n)
               #print "Probability = (%f + %d) / (%d + (%d - 1)) = %f" % (alpha_k, n_k, alpha_dot, n, prob)
                self.signal_belief[signal_i][player_type].append(prob)



    def update_beliefs_old(self, payoff, signaller_type):
        """ Update beliefs about the meaning of signals, essentially the
        belief that the State of the world is S based on s.
        i.e. P(Type | signal) = P(signal | Type)P(Type) / P(signal | Type)P(Type) + P(signal | -Type)P(-Type)
        """
        self.type_log.append(signaller_type)
        self.payoff_log.append(payoff)
        rounds = self.rounds

        type_matches = []
        for player_type in self.signals:
            type_matches.append([x == player_type for x in self.type_log])

        for signal_i, types in self.signal_belief.items():
            signal_matches = [x == signal_i for x in self.signal_log]
            for player_type, belief in types.items():
                other_types = filter(lambda x: x != player_type, self.signals)
                # Update given recent signal using bayes rule
                #Both together
                matched_pairs = zip(type_matches[player_type], signal_matches)
                signal_type_matches = [a and b for a, b in matched_pairs]
                signal_type_other_matches = {}
                #Other types and this signal
                for x in other_types:
                    matched_pairs = zip(type_matches[x], signal_matches)
                    signal_type_other_matches[x] = [a and b for a, b in matched_pairs]

                type_matches_count = float(type_matches[player_type].count(True))
                signal_matches_count = float(signal_matches.count(True))

                #P(Type) Might be wise to assume this is known
                p_type = self.type_weights[player_type]
                p_signal_type = 0.
                p_signal_not_type = 0.
                p_type_signal = self.signal_belief[signal_i][player_type][rounds - 1]
                #P(Signal | Type)
               #print "Seen this type", type_matches_count,"times."
               #print "Seen this signal", signal_matches_count,"times."
               #print "Saw this type and signal together", signal_type_matches.count(True), "times"
                if signal_matches_count > 0:
                    p_signal_type = signal_type_matches.count(True) / signal_matches_count
                #P(Signal | -Type)
                    p_signal_type_other = 0.
                    for key, matches in signal_type_other_matches.items():
                        p_signal_type_other += (matches.count(True) / signal_matches_count) * p_type
                # Probability that the signal actually meant this type (P(Type | Signal))
                   #print "Probability of signalling this type - ", p_signal_type
                   #print "Probability of signalling other type - ",p_signal_type_other
                    p_type_signal = p_signal_type*p_type / (p_signal_type*p_type + p_signal_type_other)
               #print "Updating signal ", signal_i, " type ", player_type
                self.signal_belief[signal_i][player_type].append(p_type_signal)

    def current_beliefs(self):
        """ Return the current beliefs about signals.
        """
        current = {}
        for signal, types in self.signal_belief.items():
            current[signal] = {}
            for player_type, log in types.items():
                current[signal][player_type] = log[self.rounds]
        return current

class BayesianResponder(Responder):
    """ Responds based on belief, and the bayes action rule.
    i.e. minimise the expected risk.
    """

    def loss(self, payoff):
        """ Transmute a payoff into a loss value.
        """
        return -payoff

    def risk(self, act, signal, appointment):
        """
        Return the expedted risk of this action given this signal
        was received.
        """
        act_risk = 0.

       #print "Assessing risk for action",act,"given signal",signal
        for player_type, belief in self.signal_belief[signal].items():
            type_belief = belief[appointment]
            payoff = self.loss(self.payoffs[player_type][act])
           #print "Believe true type is",player_type,"with confidence",type_belief
           #print "Risk is",payoff,"*",type_belief
            act_risk += payoff * type_belief
       #print "R(%d|%d)=%f" % (act, signal, act_risk)
        return act_risk

    def respond(self, signal):
        """
        Make a judgement about somebody based on
        the signal they sent by minimising bayesian risk.
        """
        self.signal_log.append(signal)
        best = (0, 9999999)
        for response in self.responses:
            act_risk = self.risk(response, signal, self.rounds)
            if act_risk < best[1]:
                best = (response, act_risk)
        self.response_log.append(best[0])
        self.rounds += 1
        return best[0]

class ProspectTheoryResponder(BayesianResponder):
    """
    A responder which makes decision using prospect theory.
    Reference may take value 0 (total losses so far), 1 (losses last round), or 3
    (worst case losses this round)
    Weighting is some function that takes the probability p and returns a weighted version of it.
    """
    def __init__(self, weighting=prospect_weighting(0.5), reference=0,player_type=1, signals=[0, 1, 2], responses=[0, 1]):
        self.weighting = weighting
        self.reference = reference
        super(ProspectTheoryResponder, self).__init__(player_type, signals, responses)

    def value(self, reference, outcome):
        """
        Return the relative value of an outcome compared to
        the reference point. Outcome is assumed to be a cost
        here.
        """
        return (reference + outcome)


    def expected_utility(self, act, signal, appointment):
        """
        Compute the expected utility of this response at the
        given appointment.
        """

        act_utility = 0.

       #print "Assessing utility for action",act,"given signal",signal
        for player_type, belief in self.signal_belief[signal].items():
            type_belief = belief[appointment]
            payoff = self.payoffs[player_type][act]


            reference_point = 0.

            if self.rounds > 0:
                reference_point = self.payoff_log[self.rounds - 1]

            if self.reference == 0:
                reference_point = sum(self.payoff_log)
            elif self.reference == 2:
                reference_point = min(self.payoffs[player_type].values())


           #print "Believe true type is",player_type,"with confidence",type_belief
           #print "Utility is v(%f)*w(%f)" % (payoff,type_belief)
            act_utility += self.value(reference_point, payoff) * self.weighting(type_belief)
       #print "U(%d|%d)=%f" % (act, signal, act_utility)
        return -act_utility

    def respond(self, signal):
        """
        Make a judgement about somebody based on
        the signal they sent based on expe
        """
        self.signal_log.append(signal)
        best = (0, 9999999)
        for response in self.responses:
            act_risk = self.expected_utility(response, signal, self.rounds)
            if act_risk < best[1]:
                best = (response, act_risk)
        self.response_log.append(best[0])
        self.rounds += 1
        return best[0]

class MiniMaxResponder(Responder):


    def get_payoffs(self, response):
        payoffs = []
        for player_type in self.signals:
            payoffs.append(self.payoffs[player_type][response])
        return payoffs

    """ A responder which uses straight minimax, ignoring the
    risks.
    """

    def respond(self, signal, opponent):
        self.rounds += 1
        self.signal_log.append(signal)

        worst_case = {}
        for response in self.responses:
            worst_case[response] = min(self.get_payoffs(response))
        best = (0, -99999)
        for response in self.responses:
            if best[1] < worst_case[response]:
                best = (response, worst_case[response])
        self.response_log.append(best[0])
        return best[0]


class Payoff(object):
    def __init__(self, name, value):
        self.name = name
        self.value = value

baby_payoff = Payoff("Healthy baby", 0)
no_baby_payoff = Payoff("Miscarriage", -100)
mid_baby_payoff = Payoff("Disabled baby", -50)
heavy_cost = Payoff("Social status cost of heavy drinking", -3)
moderate_cost = Payoff("Social status cost of moderate drinking", -2)
light_cost = Payoff("Social status cost of light drinking", -1)

heavy_cost_harsh = Payoff("Social status cost of heavy drinking (harsh midwife)", -6)
moderate_cost_harsh = Payoff("Social status cost of moderate drinking (harsh midwife)", -2)
light_cost_harsh = Payoff("Social status cost of light drinking (harsh midwife)", -1)

heavy_cost_moderate = Payoff("Social status cost of heavy drinking (medium midwife)", -5)
moderate_cost_moderate = Payoff("Social status cost of moderate drinking (medium midwife)", -4)
light_cost_moderate = Payoff("Social status cost of light drinking (medium midwife)", -3)


class Game(object):
    def __init__(self, num_rounds=1, baby_payoff=0, no_baby_payoff=100, mid_baby_payoff=50,referral_cost=50, heavy_cost=3,
     moderate_cost=2, light_cost=1, moderate_judge=2, harsh_judge=3):
        """ A multistage game played by two agents.
        """
        self.signal_log = []
        self.act_log = []
        self.disclosure_log = []
        self.payoff = [[[[0, 0] for y in range(3)] for z in range(3)] for i in range(3)]
        self.midwife_payoff = [[0, 0] for x in range(3)]
        self.num_rounds = num_rounds
        #Payoff for a baby
        self.baby_payoff = baby_payoff
        self.no_baby_payoff = -no_baby_payoff
        self.mid_baby_payoff = -mid_baby_payoff
        #Cost for referring
        self.referral_cost = referral_cost
        #Basic social cost of drinking types
        self.heavy_cost = heavy_cost
        self.moderate_cost = moderate_cost
        self.light_cost = light_cost
        #Type multipliers
        self.harsh_judge = harsh_judge
        self.moderate_judge = moderate_judge

    def init_payoffs(self):
        #Midwife payoffs
        #Light drinker
        self.midwife_payoff[0][0] = self.baby_payoff
        self.midwife_payoff[0][1] = self.baby_payoff - self.referral_cost

        #Moderate drinker
        self.midwife_payoff[1][0] = self.mid_baby_payoff
        self.midwife_payoff[1][1] = self.baby_payoff - self.referral_cost

        #Heavy drinker
        self.midwife_payoff[2][0] = self.no_baby_payoff
        self.midwife_payoff[2][1] = self.baby_payoff - self.referral_cost

        #Woman's payoff
        #[woman type][midwife type][signal][action]
        #Light drinkers
        #Non-judgemental midwife
        self.payoff[0][0][0][0] = self.baby_payoff - self.light_cost
        self.payoff[0][0][0][1] = self.baby_payoff - self.light_cost
        self.payoff[0][0][1][0] = self.baby_payoff - self.moderate_cost
        self.payoff[0][0][1][1] = self.baby_payoff - self.moderate_cost
        self.payoff[0][0][2][0] = self.baby_payoff - self.heavy_cost
        self.payoff[0][0][2][1] = self.baby_payoff - self.heavy_cost

        #Moderately judgemental midwife
        self.payoff[0][1][0][0] = self.baby_payoff - self.light_cost * self.moderate_judge
        self.payoff[0][1][0][1] = self.baby_payoff - self.light_cost * self.moderate_judge
        self.payoff[0][1][1][0] = self.baby_payoff - self.moderate_cost * self.moderate_judge
        self.payoff[0][1][1][1] = self.baby_payoff - self.moderate_cost * self.moderate_judge
        self.payoff[0][1][2][0] = self.baby_payoff - self.heavy_cost * self.moderate_judge
        self.payoff[0][1][2][1] = self.baby_payoff - self.heavy_cost * self.moderate_judge

        #Very judgemental midwife
        self.payoff[0][2][0][0] = self.baby_payoff - self.light_cost * self.harsh_judge
        self.payoff[0][2][0][1] = self.baby_payoff - self.light_cost * self.harsh_judge
        self.payoff[0][2][1][0] = self.baby_payoff - self.moderate_cost * self.harsh_judge
        self.payoff[0][2][1][1] = self.baby_payoff - self.moderate_cost * self.harsh_judge
        self.payoff[0][2][2][0] = self.baby_payoff - self.heavy_cost * self.harsh_judge
        self.payoff[0][2][2][1] = self.baby_payoff - self.heavy_cost * self.harsh_judge

        #Moderate drinkers
        #Non-judgemental midwife
        self.payoff[1][0][0][0] = self.mid_baby_payoff - self.light_cost
        self.payoff[1][0][0][1] = self.baby_payoff - self.light_cost
        self.payoff[1][0][1][0] = self.mid_baby_payoff - self.moderate_cost
        self.payoff[1][0][1][1] = self.baby_payoff - self.moderate_cost
        self.payoff[1][0][2][0] = self.mid_baby_payoff - self.heavy_cost
        self.payoff[1][0][2][1] = self.baby_payoff - self.heavy_cost

        #Moderately judgemental midwife
        self.payoff[1][1][0][0] = self.mid_baby_payoff - self.light_cost * self.moderate_judge
        self.payoff[1][1][0][1] = self.baby_payoff - self.light_cost * self.moderate_judge
        self.payoff[1][1][1][0] = self.mid_baby_payoff - self.moderate_cost * self.moderate_judge
        self.payoff[1][1][1][1] = self.baby_payoff - self.moderate_cost * self.moderate_judge
        self.payoff[1][1][2][0] = self.mid_baby_payoff - self.heavy_cost * self.moderate_judge
        self.payoff[1][1][2][1] = self.baby_payoff - self.heavy_cost * self.moderate_judge

        #Very judgemental midwife
        self.payoff[1][2][0][0] = self.mid_baby_payoff - self.light_cost * self.harsh_judge
        self.payoff[1][2][0][1] = self.baby_payoff - self.light_cost * self.harsh_judge
        self.payoff[1][2][1][0] = self.mid_baby_payoff - self.moderate_cost * self.harsh_judge
        self.payoff[1][2][1][1] = self.baby_payoff - self.moderate_cost * self.harsh_judge
        self.payoff[1][2][2][0] = self.mid_baby_payoff - self.heavy_cost * self.harsh_judge
        self.payoff[1][2][2][1] = self.baby_payoff - self.heavy_cost * self.harsh_judge

        #Heavy drinkers
        #Non-judgemental midwife
        self.payoff[2][0][0][0] = self.no_baby_payoff- self.light_cost
        self.payoff[2][0][0][1] = self.baby_payoff - self.light_cost
        self.payoff[2][0][1][0] = self.no_baby_payoff- self.moderate_cost
        self.payoff[2][0][1][1] = self.baby_payoff - self.moderate_cost
        self.payoff[2][0][2][0] =  self.no_baby_payoff - self.heavy_cost
        self.payoff[2][0][2][1] = self.baby_payoff - self.heavy_cost

        #Moderately judgemental midwife
        self.payoff[2][1][0][0] =  self.no_baby_payoff - self.light_cost * self.moderate_judge
        self.payoff[2][1][0][1] = self.baby_payoff - self.light_cost * self.moderate_judge
        self.payoff[2][1][1][0] = self.no_baby_payoff - self.moderate_cost * self.moderate_judge
        self.payoff[2][1][1][1] = self.baby_payoff - self.moderate_cost * self.moderate_judge
        self.payoff[2][1][2][0] = self.no_baby_payoff - self.heavy_cost * self.moderate_judge
        self.payoff[2][1][2][1] = self.baby_payoff - self.heavy_cost * self.moderate_judge

        #Very judgemental midwife
        self.payoff[2][2][0][0] = self.no_baby_payoff - self.light_cost * self.harsh_judge
        self.payoff[2][2][0][1] = self.baby_payoff - self.light_cost * self.harsh_judge
        self.payoff[2][2][1][0] = self.no_baby_payoff - self.moderate_cost * self.harsh_judge
        self.payoff[2][2][1][1] = self.baby_payoff - self.moderate_cost * self.harsh_judge
        self.payoff[2][2][2][0] = self.no_baby_payoff - self.heavy_cost * self.harsh_judge
        self.payoff[2][2][2][1] = self.baby_payoff - self.heavy_cost * self.harsh_judge


    def play_round(self, signaller, receiver):
        """ Play a round of this game between the
        two players.
        """
        signal = signaller.do_signal(receiver)
        act = receiver.respond(signal)
        signaller.response_log.append(act)
        signal_payoff = self.payoff[signaller.player_type][receiver.player_type][signal][act]
        receive_payoff = self.midwife_payoff[signaller.player_type][act]
        self.signal_log.append(signal)
        self.act_log.append(act)
        signaller.update_beliefs(signal_payoff, receiver.player_type)
        receiver.update_beliefs(receive_payoff, signaller.player_type)
        # Log honesty of signal
        self.disclosure_log.append(signal == signaller.player_type)

    def play_game(self, signaller, receiver):
        signaller.init_payoffs(self.payoff, random_expectations())
        receiver.init_payoffs(self.midwife_payoff)
        for r in range(self.num_rounds):
            self.play_round(signaller, receiver)


def main():
    print time.time()
    decision_fn_compare()
    decision_fn_compare("caseload_", caseload_test)
    decision_fn_compare("even_rounds_", equal_rounds, num_midwives=1000)
    print time.time()

if __name__ == "__main__":
    main()
