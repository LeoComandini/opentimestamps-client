# Copyright (C) 2018 The OpenTimestamps developers
#
# This file is part of the OpenTimestamps Client.
#
# It is subject to the license terms in the LICENSE file found in the top-level
# directory of this distribution.
#
# No part of the OpenTimestamps Client, including this file, may be copied,
# modified, propagated, or distributed except according to the terms contained
# in the LICENSE file.

import unittest
from opentimestamps.core.timestamp import Timestamp
from opentimestamps.core.op import OpAppend
from opentimestamps.core.notary import BitcoinBlockHeaderAttestation, LitecoinBlockHeaderAttestation, \
    PendingAttestation, UnknownAttestation
from otsclient.cmds import verify_all_attestations, discard_attestations, discard_suboptimal, prune_tree, \
    prune_timestamp


def compare_timestamps(t1, t2):
    """Return True iff the timestamps t1 and t2 are equal, checking also the attestations (unlike t1 == t2)"""
    # FIXME: instead of creating a new function, would it be better to use `t1.str_tree() == t2.str_tree()`?
    if t1.attestations == t2.attestations and t1.msg == t2.msg and t1.ops.keys() == t2.ops.keys():
        if all([compare_timestamps(stamp, t2.ops[op]) for op, stamp in t1.ops.items()]):
            return True
    return False


class TestPrune(unittest.TestCase):

    def test_verify_all_attestations(self):
        """Verifying all attestations"""

        # FIXME: some pb in catching errors, should it be done?
        # TODO: test with node verification

        t = Timestamp(b'')
        verify_all_attestations(t, [], None)
        self.assertTrue(True)

    def test_discard_attestations(self):
        """Discarding attestations"""
        t = Timestamp(b'')
        t1 = t.ops.add(OpAppend(b'\x01'))
        t2 = t.ops.add(OpAppend(b'\x02'))
        t.attestations.add(UnknownAttestation(b'unknown.', b''))
        t1.attestations.add(BitcoinBlockHeaderAttestation(1))
        t2.attestations.add(PendingAttestation("c2"))
        t2.attestations.add(PendingAttestation("c1"))

        discard_attestations(t, [UnknownAttestation, PendingAttestation("c1")])

        tn = Timestamp(b'')
        tn1 = tn.ops.add(OpAppend(b'\x01'))
        tn2 = tn.ops.add(OpAppend(b'\x02'))
        tn1.attestations.add(BitcoinBlockHeaderAttestation(1))
        tn2.attestations.add(PendingAttestation("c2"))

        self.assertTrue(compare_timestamps(t, tn))

    def test_discard_suboptimal(self):
        """Discarding suboptimal attestations"""
        t = Timestamp(b'')
        t1 = t.ops.add(OpAppend(b'\x01'))
        t2 = t.ops.add(OpAppend(b'\x02'))
        t3 = t.ops.add(OpAppend(b'\x03\03'))
        t4 = t.ops.add(OpAppend(b'\x04'))
        t1.attestations.add(BitcoinBlockHeaderAttestation(2))
        t2.attestations.add(BitcoinBlockHeaderAttestation(1))
        t3.attestations.add(LitecoinBlockHeaderAttestation(1))
        t4.attestations.add(LitecoinBlockHeaderAttestation(1))

        discard_suboptimal(t, BitcoinBlockHeaderAttestation)
        discard_suboptimal(t, LitecoinBlockHeaderAttestation)

        tn = Timestamp(b'')
        tn1 = tn.ops.add(OpAppend(b'\x01'))
        tn2 = tn.ops.add(OpAppend(b'\x02'))
        tn3 = tn.ops.add(OpAppend(b'\x03\03'))
        tn4 = tn.ops.add(OpAppend(b'\x04'))
        tn2.attestations.add(BitcoinBlockHeaderAttestation(1))
        tn4.attestations.add(LitecoinBlockHeaderAttestation(1))

        self.assertTrue(compare_timestamps(t, tn))

    def test_prune_tree(self):
        """Pruning tree"""
        t = Timestamp(b'')
        t1 = t.ops.add(OpAppend(b'\x01'))
        t2 = t.ops.add(OpAppend(b'\x02'))
        t1.attestations.add(PendingAttestation(""))

        prune_tree(t)

        tn = Timestamp(b'')
        tn1 = tn.ops.add(OpAppend(b'\x01'))
        tn1.attestations.add(PendingAttestation(""))

        self.assertTrue(t, tn)

    def test_pruning_timestamp(self):
        """Pruning timestamp"""
        t = Timestamp(b'')
        t1 = t.ops.add(OpAppend(b'\x01'))
        t2 = t.ops.add(OpAppend(b'\x02'))
        t3 = t.ops.add(OpAppend(b'\x03'))
        t21 = t2.ops.add(OpAppend(b'\x02'))
        t31 = t3.ops.add(OpAppend(b'\x03'))
        t1.attestations.add(PendingAttestation("c1"))
        t2.attestations.add(PendingAttestation("c2"))
        t3.attestations.add(PendingAttestation("c3"))
        t21.attestations.add(BitcoinBlockHeaderAttestation(2))
        t31.attestations.add(BitcoinBlockHeaderAttestation(1))

        prune_timestamp(t, [], [PendingAttestation], None)

        tn = Timestamp(b'')
        tn3 = tn.ops.add(OpAppend(b'\x03'))
        tn31 = tn3.ops.add(OpAppend(b'\x03'))
        tn31.attestations.add(BitcoinBlockHeaderAttestation(1))

        self.assertTrue(compare_timestamps(t, tn))
