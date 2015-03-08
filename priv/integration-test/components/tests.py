#!/usr/bin/env python3

import json
import select
import sys
import unittest


# write integration tests from GUI perspective here
# use JSON to communicate with framework
# execute with "make integration-test" in project root

# test case ideas
  # worker generates some valid propositions
    # last gets counted, worker stays active
  # worker generates invalid proposition

def read_json():
    line = input()
#    print("input: " + line, file=sys.stderr)
    return json.loads(line)

def clear_mailbox(test_name):
    while select.select([sys.stdin], [], [], 0.01) == ([sys.stdin], [], []):
        line = input()
        print("input skipped in \"" + test_name + "\" test: " + line, file=sys.stderr)

class TestDiscoFramework(unittest.TestCase):

    def setUp(self):
        # executed before each test case
        self.some_attribute = "some value"

    # tests are sorted by name. This is important because these tests are order dependent.
    def test_1_all_data(self):
    # is all_data correctly received on startup?
        msg = read_json()
        self.assertEqual('all data',     msg['event'])
        self.assertEqual('[1]',          msg['state'])
        self.assertEqual(False,          msg['running'])
        self.assertEqual(0,              msg['round'])
        self.assertEqual(0,              msg['problem idx'])
        self.assertEqual(['[10]', '42'], msg['worker input'])
        self.assertEqual(['ten', '[10] 42', 1000, '[1]'],                                 msg['problems'][0])
        self.assertEqual([['pwb_00', 'test-worker', '', None, '', 0, 0, 0, 'no', False]], msg['workers'])

    def test_2_blocking(self):
        clear_mailbox("blocking")
        print(json.dumps({'action': 'block worker', 'worker id': 'pwb_00'}))
        update_msg = read_json()
        self.assertEqual('worker updated',                                 update_msg['event'])
        self.assertEqual(['pwb_00', None, '', 0, 0, 0, {'idx': 1}, False], update_msg['worker data'])

        print(json.dumps({'action': 'unblock worker', 'worker id': 'pwb_00'}))
        update_msg = read_json()
        self.assertEqual('worker updated',                           update_msg['event'])
        self.assertEqual(['pwb_00', None, '', 0, 0, 0, 'no', False], update_msg['worker data'])

    def test_3_start_round(self):
    # worker echoes input: test that the worker gets the right input
        clear_mailbox("start round")
        print(json.dumps({'action': 'start round'}))

        running_msg = read_json()
        self.assertEqual('worker updated',                          running_msg['event'])
        self.assertEqual(['pwb_00', None, '', 0, 0, 0, 'no', True], running_msg['worker data'])

        start_msg = read_json()
        self.assertEqual('round started', start_msg['event'])
        self.assertEqual(1,               start_msg['round number'])

        proposition_msg = read_json()
        self.assertEqual('worker updated', proposition_msg['event'])
        self.assertEqual(['pwb_00', '[(0,0,10)]', '[10] 42', 42, 0, 0, 'no', True], proposition_msg['worker data'])

        not_running_msg = read_json()
        self.assertEqual('worker updated', not_running_msg['event'])
        self.assertEqual(['pwb_00', '[(0,0,10)]', '[10] 42', 42, 0, 0, 'no', False], not_running_msg['worker data'])

        stop_msg = read_json()
        self.assertEqual('round ended', stop_msg['event'])
        self.assertEqual(1,             stop_msg['round number'])

        worker_update_msg = read_json() # "worker updated"
        self.assertEqual('worker updated', worker_update_msg['event'])
        # TODO find out why the normalized score (entry 4, after the number 42) is not set
        self.assertEqual(['pwb_00', '[(0,0,10)]', '[10] 42', 42, 0, 0, 'no', False], not_running_msg['worker data'])

    def test_4_choose_problem(self):
        clear_mailbox("choose problem")
        print(json.dumps({'action': 'choose problem', 'problem idx': 1}))
        update_msg = read_json()
        self.assertEqual('problem chosen', update_msg['event'])
        self.assertEqual(1,                update_msg['problem idx'])

        state_changed_msg = read_json() # "problem state changed"
        self.assertEqual('problem state changed', state_changed_msg['event'])
        self.assertEqual('[1]',                   state_changed_msg['problem state'])

        input_changed_msg = read_json() # "worker input changed"
        self.assertEqual('worker input changed', input_changed_msg['event'])
        self.assertEqual(['[20]', '42'],         input_changed_msg['worker input'])

    def test_5_save_apply_load(self):
        # TODO test saving and loading game state
        # as well as applying propositions (we need a state change to test
        # loading the savegame anyway)
        # Order: Save, Apply Proposition, Check, Load, Check
        clear_mailbox("apply load")
        filepath = '/tmp/disco-test-savegame.sav'
        print(json.dumps({'action': 'save game state', 'file path': filepath}))
        result_msg = read_json()
        self.assertEqual('save game state', result_msg['event'])
        self.assertEqual('ok',              result_msg['result'])

    def test_6_manually_end_round(self):
        # TODO start a very long round and test that the round can be ended manually
        clear_mailbox("manually end round")
        print("!! missing test for manually ending a round", file=sys.stderr)

    def test_7_add_scores(self):
        # TODO
        clear_mailbox("add scores")
        print("!! missing test for adding scores", file=sys.stderr)


if __name__ == '__main__':
    # execute tests
    unittest.main(exit=False, failfast=True)
    sys.stderr.flush()

    # shut down framework
    print(json.dumps({'action': 'quit program'}))
    sys.stdout.flush()

    # wait for framework to shut down before exiting test suite
    while True:
        sys.stdin.readline()
