from collections import OrderedDict
import collections
from Results import *
import itertools

class Measures(object):
    def __init__(self, measures):
        self.measures = measures

    def keys(self):
        return self.measures.keys()

    def values(self):
        return self.measures.values()

    def dump(self, women, rounds, game, results=None):
        """
        A results dumper. Takes a tuple of a game and players, and two dictionaries.
        Measures should contain a mapping from a field name to method for getting a result
        given an appointment, set of players, and a game. Params should contain mappings
        from parameter names to values.
        Optionally takes an exist results object to add records to. This should have the same
        measures and params.
        Returns a results object for writing to csv.
        """
        if results is None:
            results = Result(self.measures.keys(), game.parameters, [])
        if women is None:
            return results
        line = map(lambda x: x.measure(rounds, women, game), self.measures.values())
        results.add_results(Result(self.measures.keys(), game.parameters, [line]))
        return results

# Measures

class Measure(object):
    def __init__(self, player_type=None, midwife_type=None, signal=None):
        self.player_type = player_type
        self.midwife_type = midwife_type
        self.signal = signal

    def filter_present(self, women, roundnum):
        """
        Filter out any women not present on this round.
        """
        women = filter(lambda x: x.started < roundnum, women)
        women = filter(lambda x: x.finished > roundnum, women)
        return women


class NumRounds(Measure):
    """
    Return the average number of rounds a player played before finishing.
    """
    def measure(self, roundnum, women, game):
        if self.player_type is not None:
            women = filter(lambda x: x.player_type == self.player_type, women)
        women = filter(lambda x: x.is_finished, women)
        if len(women) == 0:
            return 0.
        return sum(map(lambda woman: woman.finished - woman.started, women)) / float(len(women))

class Referred(Measure):
    """
    Return the fraction of players referred this round.
    """

    def measure(self, roundnum, women, game):
        return len(filter(lambda x: 1 in x.response_log, women)) / float(len(women))

class Appointment(Measure):
    def measure(self, roundnum, women, game):
        """
        Return the value passed as roundnum.
        """
        return roundnum

class TypeFinished(Measure):
    """
    Return the fraction of women of a particular type who finished this round.
    """
    def measure(self, roundnum, women, game):
        if self.player_type is not None:
            women = filter(lambda x: x.player_type == self.player_type, women)
        num_women = float(len(women))
        num_finished = len(filter(lambda x: x.is_finished, women))
        if num_women == 0:
            return 0.
        return num_finished / num_women


class TypeSignalBreakdown(Measure):
    """
    Return a function that yields the fraction of women of some type signalling
    a particular way who had a midwife of a particular type in the last round.
    """
    def measure(self, roundnum, women, game):
        if self.player_type is not None:
            women = filter(lambda x: x.player_type == self.player_type, women)
        if self.midwife_type is not None:
            women = filter(lambda x: x.type_log[len(x.type_log) - 1] == self.midwife_type, women)
        num_women = float(len(women))

        women = filter(lambda x: x.signal_log[len(x.signal_log) - 1] == self.signal, women)
        signalled = len(women)
        if num_women == 0:
            return 0.
        return signalled / num_women
    

class TypeReferralBreakdown(Measure):
    """
    Return a function that yields the fraction of women of some type signalling
    a particular way who had a midwife of a particular type and got referred.
    If signal is None, then this is for all signals.
    If midwife_type is None, then this is for all midwife types.
    """
    def measure(self, roundnum, women, game):
        women = filter(lambda x: 1 in x.response_log, women)
        if self.player_type is not None:
            women = filter(lambda x: x.player_type == self.player_type, women)
        if self.midwife_type is not None:
            women = filter(lambda x: x.type_log[len(x.type_log) - 1] == self.midwife_type, women)
        num_women = float(len(women))
        if self.signal is not None:
            women = filter(lambda x: x.signal_log[len(x.signal_log) - 1] == self.signal, women)
        signalled = len(women)
        if num_women == 0:
            return 0.
        return signalled / num_women

class PayoffType(Measure):
    """
    Return a function that gives the average payoff in the last
    round for a given type. If type is None, then the average
    for all types is returned.
    """
    def measure(self, roundnum, women, game):
        if self.player_type is not None:
            women = filter(lambda x: x.player_type == self.player_type, women)
        if len(women) == 0:
            return 0.
        return sum(map(lambda x: x.payoff_log[len(x.payoff_log)], women)) / float(len(women))
    

class SignalChange(Measure):
    """
    Return a function that yields average change in signal
    by women this round from last round.
    """
    def measure(self, roundnum, women, game):
        if roundnum == 0:
            return 0.
        women = filter(lambda x: x.player_type == self.player_type, women)
        num_women = len(women)
        if num_women == 0:
            return 0.
        change = map(lambda x: x.signal_log[roundnum - x.started] - x.signal_log[roundnum - 1 - x.started], women)
        return sum(change) / float(num_women)
    

class SignalRisk(Measure):
    """
    Return a function that gives the average risk associated
    with sending signal by players of this type who had that
    midwife type on their last round.
    """
    def measure(self, roundnum, women, game):
        #women = filter(lambda x: len(x.type_log) > roundnum, women)
        if self.player_type is not None:
            women = filter(lambda x: x.player_type == self.player_type, women)
        if self.midwife_type is not None:
            women = filter(lambda x: x.type_log[len(x.type_log) - 1] == self.midwife_type, women)
        total = sum(map(lambda x: x.round_signal_risk(roundnum)[self.signal], women))
        if len(women) == 0:
            return 0.
        return total / float(len(women))

class TypeFrequency(Measure):
    """
    Return the frequency of this type in the population at this round.
    """
    def measure(self, roundnum, women, game):
        women = self.filter_present(women, roundnum)
        types = map(lambda x: x.player_type, women)
        frequencies = collections.Counter(types)
        total = sum(frequencies.values())
        if total == 0:
            return 0.
        return frequencies[self.player_type] / float(total)

class SignalExperience(Measure):
    """
    A measure that gives the frequency of a signal experienced up
    to that round by some (or all) types of midwife.
    """
    def measure(self, roundnum, women, game):
        if self.midwife_type is not None:
            women = filter(lambda x: x.player_type == self.midwife_type, women)
        else:
            group_log = itertools.chain(*map(lambda x: x.signal_log, women))
        frequencies = collections.Counter(group_log)
        total_signals = sum(frequencies.values())
        if total_signals == 0:
            return 0.
        return frequencies[self.signal] / float(total_signals)

class TypeExperience(Measure):
    """
    A measure that gives the frequency of a type experienced up
    to that round by some (or all) types of midwife.
    """
    def measure(self, roundnum, women, game):
        if self.midwife_type is not None:
            women = filter(lambda x: x.player_type == self.midwife_type, women)
        else:
            group_log = itertools.chain(*map(lambda x: x.type_log, women))
        frequencies = collections.Counter(group_log)
        total_signals = sum(frequencies.values())
        if total_signals == 0:
            return 0.
        return frequencies[self.player_type] / float(total_signals)


class RightCallUpto(Measure):
    """
    Gives the frequency of right calls given by midwives of
    some (or any) type, up to now.
    """
    def measure(self, roundnum, women, game):
        if self.midwife_type is not None:
            women = filter(lambda x: x.player_type == self.midwife_type, women)
        total_calls = 0.
        total_right = 0.
        for midwife in women:
            r_log = midwife.response_log
            t_log = midwife.type_log
            total_calls += len(r_log)
            for i in range(len(r_log)):
                response = r_log[i]
                player = t_log[i]
                if response == 0:
                    if player == 0:
                        total_right += 1
                else:
                    if player != 0:
                        total_right += 1
        if total_calls == 0:
            return 0.
        return total_right / total_calls

class RightCall(Measure):
    """
    Gives the frequency of right calls given by midwives of
    some (or any) type, in this.
    """
    def measure(self, roundnum, women, game):
        if self.midwife_type is not None:
            women = filter(lambda x: x.player_type == self.midwife_type, women)
        total_calls = 0.
        total_right = 0.
        for midwife in women:
            try:
                response = midwife.response_log[len(midwife.response_log) - 1]
                player = midwife.type_log[len(midwife.response_log) - 1]
                total_calls += 1
                if response == 0:
                    if player == 0:
                        total_right += 1
                else:
                    if player != 0:
                        total_right += 1
            except IndexError:
                pass
        if total_calls == 0:
            return 0.
        return total_right / total_calls

class FalsePositive(Measure):
    def measure(self, roundnum, women, game):
        if self.midwife_type is not None:
            women = filter(lambda x: x.player_type == self.midwife_type, women)
        total_calls = 0.
        total_right = 0.
        for midwife in women:
            try:
                response = midwife.response_log[roundnum]
                player = midwife.type_log[roundnum]
                if response == 1:
                    if player == 0:
                        total_right += 1
                    total_calls += 1
            except IndexError:
                pass
        if total_calls == 0:
            return 0.
        return total_right / total_calls

class FalseNegative(Measure):
    def measure(self, roundnum, women, game):
        if self.midwife_type is not None:
            women = filter(lambda x: x.player_type == self.midwife_type, women)
        total_calls = 0.
        total_right = 0.
        for midwife in women:
            try:
                response = midwife.response_log[roundnum]
                player = midwife.type_log[roundnum]
                if response == 0:
                    if player != 0:
                        total_right += 1
                    total_calls += 1
            except IndexError:
                pass
        if total_calls == 0:
            return 0.
        return total_right / total_calls

class TypedFalseNegativeUpto(Measure):
    def measure(self, roundnum, women, game):
        if self.midwife_type is not None:
            women = filter(lambda x: x.player_type == self.midwife_type, women)
        total_calls = 0.
        total_right = 0.
        for midwife in women:
            r_log = midwife.response_log[:roundnum]
            t_log = midwife.type_log[:roundnum]
            for i in range(len(r_log)):
                response = r_log[i]
                player = t_log[i]
                if player == self.player_type:
                    total_calls += 1
                    if response == 0:
                        total_right += 1
        if total_calls == 0:
            return 0.
        return total_right / total_calls


class FalsePositiveUpto(Measure):
    def measure(self, roundnum, women, game):
        if self.midwife_type is not None:
            women = filter(lambda x: x.player_type == self.midwife_type, women)
        total_calls = 0.
        total_right = 0.
        for midwife in women:
            r_log = midwife.response_log[:roundnum]
            t_log = midwife.type_log[:roundnum]
            for i in range(len(r_log)):
                response = r_log[i]
                player = t_log[i]
                if response == 1:
                    if player == 0:
                        total_right += 1
                    total_calls += 1
        if total_calls == 0:
            return 0.
        return total_right / total_calls

class FalseNegativeUpto(Measure):
    def measure(self, roundnum, women, game):
        if self.midwife_type is not None:
            women = filter(lambda x: x.player_type == self.midwife_type, women)
        total_calls = 0.
        total_right = 0.
        for midwife in women:
            r_log = midwife.response_log[:roundnum]
            t_log = midwife.type_log[:roundnum]
            for i in range(len(r_log)):
                response = r_log[i]
                player = t_log[i]
                if response == 0:
                    if player != 0:
                        total_right += 1
                    total_calls += 1
        if total_calls == 0:
            return 0.
        return total_right / total_calls


class AccruedPayoffs(Measure):
    def measure(self, roundnum, women, game):
        if self.player_type is not None:
            women = filter(lambda x: x.player_type == self.player_type, women)
        total = sum(map(lambda x: x.accrued_payoffs, women))
        if len(women) == 0:
            return 0.
        return total / float(len(women))


def measures_women():
    measures = OrderedDict()
    measures['appointment'] = Appointment()
    measures['finished'] = TypeFinished()
    measures['accrued_payoffs'] = AccruedPayoffs()
    for i in range(3):
        measures["type_%d_ref" % i] = TypeReferralBreakdown(player_type=i)
        measures["type_%d_finished" % i] = TypeFinished(player_type=i)
        measures['accrued_payoffs_type_%d' % i] = AccruedPayoffs(player_type=i)
        measures['rounds_played_type_%d' % i] = NumRounds(player_type=i)
        for j in range(3):
            measures["type_%d_signal_%d" % (i, j)] = TypeSignalBreakdown(player_type=i, signal=j)
            measures["type_%d_mw_%d_ref" % (i, j)] = TypeReferralBreakdown(player_type=i, midwife_type=j)
            measures["type_%d_sig_%d_ref" % (i, j)] = TypeReferralBreakdown(player_type=i, signal=j)
            for k in range(3):
                measures["type_%d_mw_%d_sig_%d" % (i, j, k)] = TypeReferralBreakdown(player_type=i, midwife_type=j, signal=k)
    return Measures(measures)

def measures_midwives():
    measures = OrderedDict()
    measures['appointment'] = Appointment()
    measures['all_right_calls_upto'] = RightCallUpto()
    measures['all_right_calls'] = RightCall()
    measures['false_positives_upto'] = FalsePositiveUpto()
    measures['false_positives'] = FalsePositive()
    measures['false_negatives_upto'] = FalseNegativeUpto()
    measures['false_negatives'] = FalseNegative()
    measures['accrued_payoffs'] = AccruedPayoffs()
    for i in range(3):
        measures['signal_%d_frequency' % i] = SignalExperience(signal=i)
        measures['type_%d_frequency' % i] = TypeExperience(player_type=i)
        measures['type_%d_right_calls_upto' % i] = RightCallUpto(midwife_type=i)
        measures['type_%d_right_calls' % i] = RightCall(midwife_type=i)
        measures['type_%d_false_positives_upto' % i] = FalsePositiveUpto(midwife_type=i)
        measures['type_%d_false_positives' % i] = FalsePositive(midwife_type=i)
        measures['type_%d_false_negatives_upto' % i] = FalseNegativeUpto(midwife_type=i)
        measures['type_%d_false_negatives' % i] = FalseNegative(midwife_type=i)
        measures['type_%d_misses' % i] = TypedFalseNegativeUpto(player_type=i)
        measures['accrued_payoffs_type_%d' % i] = AccruedPayoffs(player_type=i)
    return Measures(measures)