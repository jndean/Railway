import unittest
import interpreting as I


class InterpreterObjects(unittest.TestCase):

    def test_Scope(self):
        s = I.Scope(parent=None, name='Test', locals={}, monos={}, globals={})
        # Assignment #
        two = I.Variable([I.Fraction(2)])
        three = I.Variable([I.Fraction(3)], ismono=True)
        s.assign('x2', two)
        s.assign('.x3', three)
        with self.assertRaises(I.RailwayVariableExists):
            s.assign('x2', two)
        with self.assertRaises(I.RailwayVariableExists):
            s.assign('.x3', three)

        # Lookup #
        self.assertEqual(two, s.lookup('x2'))
        self.assertEqual(three, s.lookup('.x3'))
        with self.assertRaises(I.RailwayUndefinedVariable):
            s.lookup('badvar')
        with self.assertRaises(I.RailwayUndefinedVariable):
            s.lookup('.badvar')
        with self.assertRaises(I.RailwayUndefinedVariable):
            s.lookup('.x2')
        with self.assertRaises(I.RailwayUndefinedVariable):
            s.lookup('x3')
        with self.assertRaises(I.RailwayUndefinedVariable):
            s.lookup('.x3', monos=False)


class ExpressionNodes(unittest.TestCase):

    def setUp(self):
        s = I.Scope(parent=None, name='Test', locals={}, monos={}, globals={})
        vals = {'x': I.Fraction(1, 2),
                'array': I.Fraction(9),
                'mono_x': I.Fraction(1, 20),
                'global_x': I.Fraction(7, 8)}
        s.assign('x', I.Variable(memory=[vals['x']]))
        s.assign('array', I.Variable(memory=[vals['array']]*10, isarray=True))
        s.assign('.x', I.Variable(memory=[vals['mono_x']], ismono=True))
        s.globals = {'global_x': I.Variable(memory=[vals['global_x']])}
        self.s = s
        self.vals = vals

    def test_Lookup(self):
        v = I.Lookup('x', index=tuple(), ismono=False)
        result = v.eval(scope=self.s)
        self.assertIsInstance(result, I.Fraction)
        self.assertEqual(result, self.vals['x'])

        v = I.Lookup('.x', index=tuple(), ismono=True)
        result = v.eval(scope=self.s)
        self.assertIsInstance(result, I.Fraction)
        self.assertEqual(result, self.vals['mono_x'])

        v = I.Lookup('global_x', index=tuple(), ismono=False)
        result = v.eval(scope=self.s)
        self.assertIsInstance(result, I.Fraction)
        self.assertEqual(result, self.vals['global_x'])

        v = I.Lookup('array', index=tuple(), ismono=False)
        result = v.eval(scope=self.s)
        self.assertIsInstance(result, list)
        self.assertEqual(result[0], self.vals['array'])

        v = I.Lookup('array', index=(I.Fraction(1),), ismono=False)
        result = v.eval(scope=self.s)
        self.assertIsInstance(result, I.Fraction)
        self.assertEqual(result, self.vals['array'])

        with self.assertRaises(I.RailwayUndefinedVariable):
            v = I.Lookup('notarray', index=(I.Fraction(1),), ismono=False)
            v.eval(scope=self.s)

        with self.assertRaises(I.RailwayIndexError):
            v = I.Lookup('array', index=(I.Fraction(100),), ismono=False)
            v.eval(scope=self.s)

        with self.assertRaises(I.RailwayIndexError):
            v = I.Lookup('array', index=(I.Fraction(-100),), ismono=False)
            v.eval(scope=self.s)

        with self.assertRaises(I.RailwayIndexError):
            v = I.Lookup('x', index=(I.Fraction(1),), ismono=False)
            v.eval(scope=self.s)

    def test_Binop(self):
        lhs = I.Lookup('x', index=tuple(), ismono=False)
        rhs = I.Lookup('array', index=(I.Fraction(0),), ismono=False)
        a, b = self.vals['x'], self.vals['array']
        ba, bb = bool(a), bool(b)
        cases = {'ADD': a+b, 'SUB': a-b, 'MUL': a*b, 'DIV': a/b, 'IDIV': a//b,
                 'POW': a**b, 'MOD': a % b, 'XOR': ba ^ bb, 'OR': ba | bb,
                 'AND': ba & bb, 'LESS': a < b, 'LEQ': a <= b, 'GREAT': a > b,
                 'GEQ': a >= b, 'EQ': a == b, 'NEQ': a != b}
        for name, groundtruth in cases.items():
            result = I.Binop(lhs, I.binops[name], rhs).eval(scope=self.s)
            self.assertEqual(result, I.Fraction(groundtruth))

        with self.assertRaises(I.RailwayTypeError):
            lhs = I.Lookup('x', index=tuple(), ismono=False)
            rhs = I.Lookup('array', index=tuple(), ismono=False)
            I.Binop(lhs, I.binops['ADD'], rhs).eval(scope=self.s)

    def test_Uniop(self):
        lhs = I.Lookup('x', index=tuple(), ismono=False)
        x = self.vals['x']
        cases = {'SUB': -x, 'NOT': I.Fraction(not bool(x))}
        for name, groundtruth in cases.items():
            result = I.Uniop(I.uniops[name], lhs).eval(scope=self.s)
            self.assertEqual(result, groundtruth)

        with self.assertRaises(I.RailwayTypeError):
            lhs = I.Lookup('array', index=tuple(), ismono=False)
            I.Uniop(I.uniops['SUB'], lhs).eval(scope=self.s)


class LetUnletNodes(unittest.TestCase):
    def setUp(self):
        s = I.Scope(parent=None, name='Test', locals={}, monos={}, globals={})
        vals = {'x': I.Fraction(1, 2),
                'array': I.Fraction(9),
                'mono_x': I.Fraction(1, 20),
                'global_x': I.Fraction(7, 8)}
        s.assign('x', I.Variable(memory=[vals['x']]))
        s.assign('array', I.Variable(memory=[vals['array']]*10, isarray=True))
        s.assign('.x', I.Variable(memory=[vals['mono_x']], ismono=True))
        s.globals = {'global_x': I.Variable(memory=[vals['global_x']])}
        self.s = s
        self.vals = vals

    def test_create_memory(self):
        x = I.Fraction(4, 5)
        length_list = [2, 3]
        result = I.create_memory(length_list, x)
        for l1 in range(length_list[0]):
            self.assertEqual(len(result[l1]), length_list[1])
            for l2 in range(length_list[1]):
                self.assertEqual(x, result[l1][l2])

        x = [I.Fraction(4, 5), I.Fraction(8, 9)]
        length_list = [2, 3]
        result = I.create_memory(length_list, x)
        for l1 in range(length_list[0]):
            self.assertEqual(len(result[l1]), length_list[1])
            for l2 in range(length_list[1]):
                self.assertEqual(x[l1], result[l1][l2])

        x = I.Fraction(0, 5)
        length_list = [11]
        result = I.create_memory(length_list, x)
        self.assertEqual(len(result), length_list[0])
        for l1 in range(length_list[0]):
            self.assertEqual(x, result[l1])

        x = [I.Fraction(-19, 5)]
        length_list = [1]
        result = I.create_memory(length_list, x)
        self.assertEqual(len(result), length_list[0])
        self.assertEqual(x[0], result[0])

        with self.assertRaises(IndexError):
            I.create_memory([10], [I.Fraction(-1)] * 9)

        with self.assertRaises(TypeError):
            I.create_memory([4], [[I.Fraction(2)]*4])

    def test_assert_memory(self):
        x, y = [I.Fraction(0)], [I.Fraction(0)]
        I.compare_memory(x, y)

        x, y = [], []
        I.compare_memory(x, y)

        x = [[I.Fraction(1), I.Fraction(2)],
             [I.Fraction(3), I.Fraction(4)]]
        y = [[I.Fraction(1), I.Fraction(2)],
             [I.Fraction(3), I.Fraction(4)]]
        I.compare_memory(x, y)

        y[0].append(I.Fraction(5))
        with self.assertRaises(IndexError):
            I.compare_memory(x, y)

        y[0].pop()
        y[0][-1] = [I.Fraction(-1)]
        with self.assertRaises(IndexError):
            I.compare_memory(x, y)

        y[0][-1] = I.Fraction(-1)
        with self.assertRaises(ValueError):
            I.compare_memory(x, y)

    def test_let(self):
        let = I.Let(lookup=I.Lookup(name='y', index=tuple(), ismono=False),
                    rhs=None)
        let.eval(scope=self.s, backwards=False)
        self.assertEqual(
            I.Lookup('y', index=tuple(), ismono=False).eval(self.s),
            I.Fraction(0))

        with self.assertRaises(I.RailwayVariableExists):
            let = I.Let(lookup=I.Lookup(name='y', index=tuple(), ismono=False),
                        rhs=None)
            let.eval(scope=self.s, backwards=False)

        with self.assertRaises(I.RailwayVariableExists):
            let = I.Let(lookup=I.Lookup(name='.x', index=tuple(), ismono=True),
                        rhs=None)
            let.eval(scope=self.s, backwards=False)

        let = I.Let(lookup=I.Lookup(name='y1', index=tuple(), ismono=False),
                    rhs=I.Lookup(name='x', index=tuple(), ismono=False))
        let.eval(scope=self.s, backwards=False)
        self.assertEqual(
            I.Lookup('y1', index=tuple(), ismono=False).eval(self.s),
            self.vals['x'])

        let = I.Let(lookup=I.Lookup(name='array2',
                                    index=(I.Fraction(2), I.Fraction(2)),
                                    ismono=False),
                    rhs=I.Lookup(name='x',
                                 index=tuple(),
                                 ismono=False))
        let.eval(scope=self.s, backwards=False)
        for row in self.s.lookup(name='array2').memory:
            for elt in row:
                self.assertEqual(elt, self.vals['x'])

        with self.assertRaises(I.RailwayIndexError):
            let = I.Let(lookup=I.Lookup(name='z',
                                        index=tuple(),
                                        ismono=False),
                        rhs=I.Lookup(name='array',
                                     index=tuple(),
                                     ismono=False))
            let.eval(scope=self.s, backwards=False)

        let = I.Let(lookup=I.Lookup(name='z',
                                    index=tuple(),
                                    ismono=False),
                    rhs=I.Lookup(name='array',
                                 index=(I.Fraction(3),),
                                 ismono=False))
        let.eval(scope=self.s, backwards=False)
        self.assertEqual(self.s.lookup('z').memory[0],
                         self.vals['array'])

    def test_unlet(self):
        unlet = I.Unlet(lookup=I.Lookup(
                            name='badvar',
                            index=tuple(),
                            ismono=False),
                        rhs=I.Fraction(19, 67))
        with self.assertRaises(I.RailwayUndefinedVariable):
            unlet.eval(scope=self.s, backwards=False)
        unlet.eval(scope=self.s, backwards=True)
        self.assertEqual(self.s.lookup('badvar').memory[0], unlet.rhs)
        unlet.eval(scope=self.s, backwards=False)
        with self.assertRaises(I.RailwayUndefinedVariable):
            unlet.eval(scope=self.s, backwards=False)

        unlet = I.Unlet(lookup=I.Lookup(
                            name='x',
                            index=tuple(),
                            ismono=False),
                        rhs=I.Lookup(
                            name='array',
                            index=tuple(),
                            ismono=False))
        with self.assertRaises(I.RailwayIndexError):
            unlet.eval(scope=self.s, backwards=False)


if __name__ == '__main__':
    unittest.main()
