import unittest
from pipeline.reconcile import reconcile_exact

class ReconciliationTests(unittest.TestCase):
    def test_comparable_exact_control_and_full_coverage_are_required(self):
        rows=[{'partnerCode':'1220','value':'9007199254740993'},{'partnerCode':'2010','value':'2'}]
        self.assertEqual(reconcile_exact(rows,{'1220','2010'},'9007199254740995')['residual'],'0')
        with self.assertRaises(ValueError):reconcile_exact(rows,{'1220','2010'},'9007199254740994')
        with self.assertRaises(ValueError):reconcile_exact(rows[:1],{'1220','2010'},'9007199254740993')
        with self.assertRaises(ValueError):reconcile_exact(rows+rows[:1],{'1220','2010'},'18014398509481988')
        with self.assertRaises(ValueError):reconcile_exact(rows,{'1220'},'9007199254740995')
        with self.assertRaises(ValueError):reconcile_exact([{'partnerCode':'1220','value':None}],{'1220'},'0')

if __name__=='__main__':unittest.main()
